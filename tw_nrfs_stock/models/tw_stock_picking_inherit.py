# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockPickingNrfs(models.Model):
    _inherit = "stock.picking"
    
    # 7: defaults methods
    def _get_default_nrfs_location_id(self):
        domain = [
            ('type_id.value', '=', 'nrfs'),
            ('company_id', '=', self.env.company.id)
        ]
        if self.division:
            domain.append(('division', '=', self.division))
            
        location = self.env['stock.location'].search(domain, limit=1)
        return location.id if location else False

    # 8: fields
    has_nrfs = fields.Selection([
        ('have_nrfs', 'Have NRFS'),
        ('no_nrfs', 'No NRFS')
    ], string='Has QR Code', default='no_nrfs', compute='_compute_has_nrfs')

    # 9: relation fields
    nrfs_location_id = fields.Many2one('stock.location', string='NRFS Location', help='Location for NRFS', default=lambda self: self._get_default_nrfs_location_id())
    vehicle_id = fields.Many2one('tw.vehicle', string='Vehicle Number', help='Vehicle Number')
    driver_id = fields.Many2one('res.partner', string='Driver Expedisi', domain=[('category_id.name', '=', 'Driver')], help='Driver Expedisi')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('move_ids_without_package.move_line_ids', )
    def _compute_has_nrfs(self):
        for record in self:
            record.has_nrfs = 'no_nrfs'
            check_nrfs = record.move_ids_without_package.move_line_ids.filtered(lambda x: not x.is_rfs and x.picking_id.division == 'Unit' and x.picking_id.stock_inbound_id)
            if check_nrfs:
                record.has_nrfs = 'have_nrfs'

    @api.onchange('stock_inbound_id')
    def onchange_stock_inbound_id(self):
        self.vehicle_id = False
        self.driver_id = False
        if self.stock_inbound_id:
            self.vehicle_id = self.stock_inbound_id.vehicle_id.id
            self.driver_id = self.stock_inbound_id.driver_id.id

    # 12: override methods

    # 13: action methods
    def _prepare_update_lot(self, picking, move, move_line):
        res = super(InheritStockPickingNrfs, self)._prepare_update_lot(picking, move, move_line)
        location_id = self._get_destination_location(move_line)
        if move_line.lot_id.location_id.id != location_id:
            res.update({
                'location_id': location_id,
            })
        
        is_incoming_md = picking._is_incoming_md()
        if is_incoming_md and picking.division == 'Unit' and not move_line.is_rfs:
            self._create_nrfs(move, move_line.lot_id, 'LKUAT')
        
        return res
    
    def _process_validate_move_line(self, move, move_line):
        is_incoming_md = move_line.picking_id._is_incoming_md()
        company_warehouse = self.env['stock.warehouse']._get_company_warehouse(self.company_id)
        if not move_line.is_rfs and move_line.move_id.product_id.product_tmpl_id.tracking != 'serial' and is_incoming_md:
            self._check_nrfs_location()
            if move_line.location_dest_id.type_id.value not in ('nrfs', 'NRFS'):
                if company_warehouse.reception_steps in ['three_steps', 'two_steps'] and (move_line.location_id.id == company_warehouse.wh_qc_stock_loc_id.id or move_line.location_id.id == company_warehouse.wh_input_stock_loc_id.id):
                    move_line.suspend_security().write({
                        'location_qc_id': self.nrfs_location_id.id,
                    })
                else:
                    move_line.suspend_security().write({
                        'location_dest_id': self.nrfs_location_id.id,
                    })
            
        return super(InheritStockPickingNrfs, self)._process_validate_move_line(move, move_line)

    # 14: private methods
    def prepare_nrfs_vals(self, move_obj, lot_obj, nrfs_type, line_ids):
        vals = {
            'company_id': move_obj.picking_id.company_id.id,
            'origin': move_obj.picking_id.name,
            'nrfs_date': date.today(),
            'stock_inbound_id': move_obj.picking_id.stock_inbound_id.id,
            'vehicle_id': move_obj.picking_id.vehicle_id.id,
            'driver_id': move_obj.picking_id.driver_id.id,
            'division': move_obj.picking_id.division,
        }
        if lot_obj:
            vals.update({
                'lot_id': lot_obj.id,
                'product_id': lot_obj.product_id.id,
                'expedition_ship': lot_obj.expedition_ship,
                'chassis_number': lot_obj.chassis_number,
                'ship_list_number': lot_obj.ship_list_number,
                'unit_receipt_date': lot_obj.receive_date if lot_obj.receive_date else date.today(),
            })
        if nrfs_type:
            vals.update({
                'nrfs_type': nrfs_type,
            })
        if line_ids:
            vals.update({
                'line_ids': line_ids,
            })
            
        return vals

    def _create_nrfs(self, move_obj, lot_obj=False, nrfs_type=False, line_ids=False):
        vals = self.prepare_nrfs_vals(move_obj, lot_obj, nrfs_type, line_ids)
        self.env['tw.nrfs'].suspend_security().create(vals)
        
    def _get_destination_location(self, move_line):
        location_dest_id = move_line.location_dest_id.id
        is_incoming_md = move_line.picking_id._is_incoming_md()
        if move_line.move_id.product_id.product_tmpl_id.tracking == 'serial' and is_incoming_md:
            if not move_line.is_rfs:
                self._check_nrfs_location()
                location_dest_id = self.nrfs_location_id.id
        return location_dest_id

    def _check_nrfs_location(self):
        if not self.nrfs_location_id:
            raise Warning("Please fill in the NRFS Location first!")
    
    