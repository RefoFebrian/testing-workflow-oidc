# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwAssetDistribution(models.Model):
    _name = "tw.asset.distribution"
    _description = "Asset Distribution"
    _order = "id desc"

    # 7: defaults methods
    def _get_default_date(self):
        return date.today()

    # 8: fields
    name = fields.Char(string="Name", readonly=True, default='New', copy=False, index=True, compute='_compute_name', store=True)
    date = fields.Date('Date',default=_get_default_date)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options('Umum'), default='Umum', readonly=True)
    state = fields.Selection([
        ('requested','Requested'),
        ('done','Done')],default='requested')
    type = fields.Selection([
        ('regular','Regular'),
        ('internal','Internal')],default='regular', string='Type')
    

    # Audit Trail
    confirm_date = fields.Datetime('Confirmed on')
    confirm_uid = fields.Many2one('res.users',string="Confirmed by")

    # 9: relation fields
    mutation_request_id = fields.Many2one('tw.asset.mutation','Mutation Request')
    company_id = fields.Many2one('res.company','Branch Request')
    company_sender_id = fields.Many2one('res.company', string='Branch Sender')
    pic_asset_id = fields.Many2one('hr.employee','PIC Asset',domain="[('company_id','=',company_id),('job_id.name','!=','SALESMAN PARTNER')]")
    detail_ids = fields.One2many('tw.asset.distribution.line','mutation_id')
    picking_count = fields.Integer(string='Picking Count', compute='_compute_picking_count')
    picking_id = fields.Many2one('stock.picking', string='Stock Picking', readonly=True, copy=False)

    # 10: constraints & sql constraints
    @api.constrains('detail_ids')
    def _check_detail_ids(self):
        if len(self.detail_ids) <= 0:
            raise Warning("Detail Asset tidak boleh kosong!")
        err_msg = ""
        if err_msg:
            raise Warning(err_msg)

    # 11: compute/depends & on change methods
    def _compute_picking_count(self):
        for rec in self:
            rec.picking_count = self.env['stock.picking'].search_count([('origin', '=', rec.name)])

    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            if not rec.name or rec.name == 'New':
                if rec.company_id:
                    code = 'MIA' if rec.type == 'internal' else 'SDA'
                    rec.name = self.env['ir.sequence'].get_sequence_code(code, rec.company_id.code)
    
    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        return super(TwAssetDistribution,self).create(vals_list)

    def unlink(self):
        raise Warning("Data Distribution Asset tidak bisa dihapus !")

    # 13: action methods
    def action_view_picking(self):
        self.ensure_one()
        pickings = self.env['stock.picking'].search([('origin', '=', self.name)])
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        if len(pickings) > 1:
            action['domain'] = [('id', 'in', pickings.ids)]
        elif len(pickings) == 1:
            action['views'] = [(self.env.ref('stock.view_picking_form').id, 'form')]
            action['res_id'] = pickings.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action
    def action_open_picking(self):
        self.ensure_one()
        if not self.picking_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Picking',
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'res_id': self.picking_id.id,
            'target': 'current',
        }

    def action_print_berita_acara_mutasi(self):
        self.ensure_one()
        return self.env.ref('tw_asset_mutation.action_report_berita_acara_mutasi_asset').report_action(self)

    # 14: private methods
        
    def action_confirm(self):
        if self.type == 'internal':
            # Internal mutation: hanya buat picking internal, tanpa asset adjustment
            for detail in self.detail_ids:
                if not detail.location_asset_id:
                    raise Warning("Lokasi Asset tidak boleh kosong!")
                if not detail.location_dest_id:
                    raise Warning("Lokasi Tujuan tidak boleh kosong!")
                self.action_create_picking(detail)
                self._update_asset_location(detail)
        else:
            # Distribution: buat asset adjustment + picking receipt
            for detail in self.detail_ids:
                if not detail.location_asset_id:
                    raise Warning("Lokasi Asset tidak boleh kosong!")
                
                self.action_create_picking(detail)
                
                vals = {
                    'company_id':detail.asset_id.company_id.id,
                    'asset_id':detail.asset_id.id,
                    'category_id':detail.asset_id.category_id.id,
                    'number_depreciation':detail.asset_id.method_number,
                    'purchase_value':detail.asset_id.real_purchase_value,
                    'purchase_date':detail.asset_id.purchase_date,
                    'new_category_id':detail.asset_id.category_id.id,
                    'new_number_depreciation':detail.asset_id.method_number,
                    'new_purchase_value':detail.asset_id.real_purchase_value,
                    'new_purchase_date':detail.asset_id.purchase_date,
                    'new_company_id':self.company_id.id,
                    'bool_journal_category':False,
                    'bool_journal_gross_value':False,
                }
                asset_adjusment_obj = self.env['tw.asset.adjustment'].suspend_security().create(vals)
                asset_adjusment_obj.suspend_security().post_adjustment()
                detail.asset_id.write({'employee_user_id':detail.new_employee_user_id.id})
                detail.write({'asset_adjusment_id':asset_adjusment_obj.id})

        self.write({
            'state':'done',
            'confirm_uid':self._uid,
            'confirm_date':self._get_default_date()
        })
        # Mutasi Request Update Done
        if self.mutation_request_id:
            self.mutation_request_id.suspend_security().write({'state':'done'})

    def action_create_picking(self, detail):
        """Dispatcher: panggil method sesuai type"""
        if self.type == 'internal':
            self._create_internal_picking(detail)
        else:
            self._create_distribution_picking(detail)

    # ==================== INTERNAL TRANSFER (1-step) ====================

    def _create_internal_picking(self, detail):
        """Buat picking internal transfer (1-step: lokasi asal → lokasi tujuan dalam 1 company)"""
        warehouse = self.company_id.warehouse_id
        if not warehouse:
            raise Warning(f"Please configure a warehouse for branch '{self.company_id.name}' first.")
        
        picking_type = warehouse.int_type_id
        if not picking_type:
            raise Warning(f"Internal transfer type not found for warehouse '{warehouse.name}'.")
        
        picking_obj = self.env['stock.picking'].with_company(self.company_id.id).create({
            'company_id': self.company_id.id,
            'division': self.division,
            'date': self.date,
            'origin': self.name,
            'type': 'internal',
            'picking_type_id': picking_type.id,
            'location_id': detail.location_asset_id.id,
            'location_dest_id': detail.location_dest_id.id,
        })

        # Create Stock Moves
        self._create_internal_stock_moves(picking_obj, detail, picking_type, warehouse)

        # Force Assign & Auto Validate
        picking_obj.action_assign()
        for move in picking_obj.move_ids_without_package:
            move.quantity = move.product_uom_qty
        picking_obj.with_context(skip_backorder=True, skip_immediate=True).button_validate()

    def _create_internal_stock_moves(self, picking, detail, picking_type, warehouse):
        """Buat stock moves untuk internal transfer"""
        moves_ids = []
        asset_lines = [detail] if detail else self.detail_ids
        for asset_line in asset_lines:
            if not asset_line.product_id:
                continue
            if asset_line.product_id.type in ('product', 'consu'):
                vals = {
                    'name': asset_line.asset_id.name + ' - ' + asset_line.product_id.name or '',
                    'product_id': asset_line.product_id.id,
                    'product_uom': asset_line.product_id.uom_id.id,
                    'product_uom_qty': 1,
                    'date': date.today(),
                    'location_id': asset_line.location_asset_id.id,
                    'location_dest_id': asset_line.location_dest_id.id,
                    'picking_id': picking.id,
                    'state': 'draft',
                    'price_unit': asset_line.book_value,
                    'picking_type_id': picking_type.id,
                    'origin': self.name,
                    'warehouse_id': warehouse.id,
                    'company_id': self.company_id.id,
                }
                stock_move_obj = self.env['stock.move'].create(vals)
                moves_ids.append(stock_move_obj.id)
        # Confirm stock moves
        for move_id in moves_ids:
            move_obj = self.env['stock.move'].browse(move_id)
            if move_obj:
                move_obj._action_confirm()

    # ==================== DISTRIBUTION (2-step interbranch) ====================

    def _create_distribution_picking(self, detail):
        """Buat picking interbranch OUT dari sender company (step 1 of 2).
        
        Flow: sender stock → transit (OUT) + transit → destination stock (IN)
        """
        warehouse = self.env['stock.warehouse'].suspend_security().search(
            [('company_id', '=', self.company_sender_id.id)], limit=1
        )
        if not warehouse:
            raise Warning(f"Please configure a warehouse for branch '{self.company_sender_id.name}' first.")
        
        picking_type = warehouse.interbranch_out_type_id
        if not picking_type:
            raise Warning(f"Please configure 'Interbranch Out Type' for warehouse '{warehouse.name}' first.")
        
        picking_obj = self.env['stock.picking'].with_company(self.company_sender_id).suspend_security().create({
            'company_id': self.company_sender_id.id,
            'division': self.division,
            'date': self.date,
            'partner_id': self.company_id.partner_id.id,
            'origin': self.name,
            'type': 'regular',
            'picking_type_id': picking_type.id,
            'min_date': self.date,
        })

        # Create Stock Moves
        self._create_distribution_stock_moves(picking_obj, detail, picking_type, warehouse)

        # Force Assign & Auto Validate
        picking_obj.suspend_security().action_assign()
        for move in picking_obj.move_ids_without_package:
            move.quantity = move.product_uom_qty
        picking_obj.suspend_security().with_context(skip_backorder=True, skip_immediate=True).button_validate()

        # Step 2: Create IN picking at destination company
        self._create_destination_picking(detail, picking_type)

    def _create_distribution_stock_moves(self, picking, detail, picking_type, warehouse):
        """Buat stock moves untuk distribution (interbranch OUT)"""
        moves_ids = []
        asset_lines = [detail] if detail else self.detail_ids
        transit_location = warehouse._get_transit_location()
        if not transit_location:
            raise Warning("Please configure a transit location for warehouse '%s' first." % self.company_sender_id.name)
        for asset_line in asset_lines:
            if not asset_line.product_id:
                continue
            if asset_line.product_id.type in ('product', 'consu'):
                vals = {
                    'name': asset_line.asset_id.name + ' - ' + asset_line.product_id.name or '',
                    'product_id': asset_line.product_id.id,
                    'product_uom': asset_line.product_id.uom_id.id,
                    'product_uom_qty': 1,
                    'date': date.today(),
                    'location_id': asset_line.location_source_id.id,
                    'location_dest_id': transit_location.id,
                    'picking_id': picking.id,
                    'state': 'draft',
                    'price_unit': asset_line.book_value,
                    'picking_type_id': picking_type.id,
                    'origin': self.name,
                    'warehouse_id': warehouse.id,
                    'company_id': self.company_sender_id.id,
                }
                stock_move_obj = self.env['stock.move'].suspend_security().create(vals)
                moves_ids.append(stock_move_obj.id)
        # Confirm stock moves
        for move_id in moves_ids:
            move_obj = self.env['stock.move'].browse(move_id)
            if move_obj:
                move_obj.suspend_security()._action_confirm()

    def _create_destination_picking(self, detail, source_picking_type):
        """Create IN picking at destination company (step 2 of 2).
        
        Moves product from transit location to the user-selected destination location.
        OUT (sender stock → transit) + IN (transit → destination stock).
        """
        dest_warehouse = self.env['stock.warehouse'].suspend_security().search(
            [('company_id', '=', self.company_id.id)], limit=1
        )
        if not dest_warehouse:
            raise Warning(f"Please configure a warehouse for branch '{self.company_id.name}' first.")

        dest_picking_type = dest_warehouse.interbranch_in_type_id
        if not dest_picking_type:
            raise Warning(f"Please configure 'Interbranch In Type' for warehouse '{dest_warehouse.name}' first.")

        transit_location = dest_warehouse._get_transit_location()
        if not transit_location:
            raise Warning("Please configure a transit location for warehouse '%s' first." % self.company_sender_id.name)    

        in_picking = self.env['stock.picking'].with_company(self.company_id).suspend_security().create({
            'company_id': self.company_id.id,
            'division': self.division,
            'date': self.date,
            'partner_id': self.company_sender_id.partner_id.id,
            'origin': self.name,
            'picking_type_id': dest_picking_type.id,
            'min_date': self.date,
        })

        # Create stock move: transit → destination location
        if detail.product_id and detail.product_id.type in ('product', 'consu'):
            move_vals = {
                'name': detail.asset_id.name + ' - ' + detail.product_id.name or '',
                'product_id': detail.product_id.id,
                'product_uom': detail.product_id.uom_id.id,
                'product_uom_qty': 1,
                'date': date.today(),
                'location_id': transit_location.id,
                'location_dest_id': detail.location_asset_id.id,
                'picking_id': in_picking.id,
                'state': 'draft',
                'price_unit': detail.book_value,
                'picking_type_id': dest_picking_type.id,
                'origin': self.name,
                'warehouse_id': dest_warehouse.id,
                'company_id': self.company_id.id,
            }
            move_obj = self.env['stock.move'].suspend_security().create(move_vals)
            move_obj.suspend_security()._action_confirm()

        # Auto validate
        in_picking.suspend_security().action_assign()
        for move in in_picking.move_ids_without_package:
            move.quantity = move.product_uom_qty
        in_picking.suspend_security().with_context(skip_backorder=True, skip_immediate=True).button_validate()
    
    def _update_asset_location(self, detail):
        if detail.location_dest_id:
            detail.asset_id.write({'location_id': detail.location_dest_id.id})