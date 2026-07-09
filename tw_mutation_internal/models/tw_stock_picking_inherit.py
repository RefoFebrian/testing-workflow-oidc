# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 5: local imports

# 6: Import of unknown third party lib

class TWMutationInternal(models.Model):
    _inherit = "stock.picking"
    
    # 8: fields
    
    # 9: relation fields
    picking_line_ids = fields.One2many(comodel_name='tw.stock.picking.line', inverse_name="picking_id", string="Picking Line")
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('location_id','location_dest_id')
    def _onchange_location_internal(self):
        if self.location_id or self.location_dest_id:
            if self.location_id == self.location_dest_id:
                if self.picking_type_id.code != 'internal':
                    raise Warning(_("Source Location and Destination Location cannot be the same!"))
    
    @api.onchange('location_id')
    def _onchange_source_location_internal(self):
        if self.picking_type_id.code == 'internal':
            self.picking_line_ids = False

    @api.onchange('is_include_sublocations')
    def _onchange_is_include_sublocations(self):
        if self.picking_type_id.code == 'internal' and not self.is_include_sublocations:
            self.picking_line_ids = False

    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            if self.picking_type_id.company_id.id != self.company_id.id:
                self.picking_line_ids = False
                if self.type == 'internal':
                    self.picking_type_id = self.picking_type_id.get_picking_type('internal',self.company_id.id, self.division, additional_domain=[('sequence_code', '=', 'INT')])
            
    # 12: override methods
    def copy_data(self, default=None):
        if default is None:
            default = {}
        default['move_ids'] = False
        return super().copy_data(default)

    # 13: action methods
    def action_confirm_internal_transfer(self):
        self.ensure_one()
        self._validate_internal_transfer()
        move_dict = {}
        lot_ids = []
        for picking_line in self.picking_line_ids:
            lot_ids.append(picking_line.lot_id.id)
            product_id = picking_line.product_id.id
            location_id = picking_line.location_id.id
            key = (product_id, location_id)
            if key not in move_dict:
                move_dict[key] = {
                    'product_id': picking_line.product_id.id,
                    'product_uom': picking_line.product_id.uom_id.id,
                    'qty': picking_line.quantity,
                    'location_id': location_id,
                    'location_dest_id': picking_line.location_dest_id.id,
                }
                if picking_line.lot_id:
                    move_dict[key]['lot_ids'] = [picking_line.lot_id.id]
            else:
                move_dict[key]['qty'] += picking_line.quantity
                if picking_line.lot_id:
                    move_dict[key]['lot_ids'].extend([picking_line.lot_id.id])

        for move in move_dict.values():
            move_obj = self.env['stock.move'].suspend_security().with_context(default_company_id=self.company_id.id).create({
                'picking_id': self.id,
                'name': self.name,
                'product_id': move.get('product_id'),
                'product_uom_qty': move.get('qty'),
                'product_uom': move.get('product_uom'),
                'location_id': move.get('location_id'),
                'location_dest_id': move.get('location_dest_id'),
            })

            move_line_vals = {
                'picking_id': self.id,
                'move_id': move_obj.id,
                'product_id': move_obj.product_id.id,
                'state': 'assigned',
                'company_id': self.company_id.id,
                'location_id': move.get('location_id') or self.location_id.id,
                'location_dest_id': move.get('location_dest_id') or self.location_dest_id.id,
            }
            
            if move.get('lot_ids'):
                for lot_id in move.get('lot_ids'):
                    move_line_obj = self.env['stock.move.line'].suspend_security().search([
                        ('move_id', '=', move_obj.id),
                        ('product_id', '=', move_obj.product_id.id),
                        ('lot_id', '=', lot_id)
                    ], limit=1)
                    if not move_line_obj:
                        move_line_vals.update({
                            'lot_id': lot_id,
                            'quantity': 1,
                            'quantity_product_uom': 1
                        })
                        self.env['stock.move.line'].suspend_security().create(move_line_vals)
            else:
                move_line_obj = self.env['stock.move.line'].suspend_security().search([
                    ('move_id', '=', move_obj.id),
                    ('product_id', '=', move_obj.product_id.id)
                ], limit=1)
                if not move_line_obj:
                    move_line_vals.update({
                        'quantity': move_obj.product_uom_qty,
                        'quantity_product_uom': move_obj.product_uom_qty
                    })
                    self.env['stock.move.line'].suspend_security().create(move_line_vals)
        self.action_confirm()
        self.button_validate()
        
    def action_validate_internal_transfer(self):
        self._validate_internal_transfer()
        self.button_validate()

    def action_print_document(self):
        self.ensure_one()
        return self.env.ref('tw_mutation_internal.action_report_mutation_internal').report_action(self.id)

    def action_renew_available(self):
        res = super(TWMutationInternal, self).action_renew_available()
        if self.picking_line_ids:
            for picking_line in self.picking_line_ids:
                picking_line._renew_availability()
        return res
    
    # 14: private methods 
    def _check_qty_available(self):
        for move in self.move_ids_without_package:
            self.action_renew_available()
            if move.product_uom_qty > move.qty_available:
                raise Warning("Perhatian!\nQty %s yang dimasukkan (%s) tidak boleh lebih besar dari Qty Available (%s)!"% (move.product_id.name, int(move.product_uom_qty), int(move.qty_available))) 
    
    def _validate_internal_transfer(self):
        lot_names = [line.lot_id.name for line in self.picking_line_ids if line.lot_id]
        duplicates = {name for name in lot_names if lot_names.count(name) > 1}
        if duplicates:
            raise Warning(_("Perhatian! Nomor Serial Number yang di input duplikat!\n%s") % ", ".join(duplicates))
        
        if self.location_id == self.location_dest_id and not self.is_include_sublocations:
            raise Warning("Perhatian! Lokasi Asal dan Lokasi Tujuan tidak boleh sama!")

        if not self.picking_line_ids:
            raise Warning("Perhatian!\nTab Line tidak boleh kosong!")
        
        duplicate_check = {}
        for picking_line in self.picking_line_ids:
            if picking_line.tracking == 'serial' and not picking_line.lot_id:
                raise Warning("Perhatian!\nNomor Serial Number tidak boleh kosong!")
            if picking_line.quantity <= 0:
                raise Warning("Perhatian!\nQty %s yang dimasukkan (%s) tidak boleh kurang dari 0!" % (picking_line.product_id.name, int(picking_line.quantity)))
            if picking_line.quantity > picking_line.qty_available:
                raise Warning("Perhatian!\nQty %s yang dimasukkan (%s) tidak boleh lebih besar dari Qty Available (%s)!" % (picking_line.product_id.name, int(picking_line.quantity), int(picking_line.qty_available)))

            if picking_line.lot_id and picking_line.location_id != self.location_id:
                raise Warning("Perhatian!\nNomor Serial Number %s sudah tidak ada di lokasi %s!" % (picking_line.lot_id.name, picking_line.location_id.complete_name))
            
            picking_line._renew_availability()
            if picking_line.qty_available < picking_line.quantity:
                raise Warning("Perhatian!\nQty %s yang dimasukkan (%s) tidak boleh lebih besar dari Qty Available (%s)!" % (picking_line.product_id.name, int(picking_line.quantity), int(picking_line.qty_available)))

            if (picking_line.product_id, picking_line.location_id, picking_line.lot_id) in duplicate_check:
                raise Warning("Perhatian!\nTerdapat duplikasi Produk %s dan Lokasi %s %s!" % (picking_line.product_id.name, picking_line.location_id.complete_name, "dan Serial Number %s" % picking_line.lot_id.name if picking_line.lot_id else ""))
            else:
                duplicate_check[(picking_line.product_id, picking_line.location_id, picking_line.lot_id)] = True

        self._check_qty_available()