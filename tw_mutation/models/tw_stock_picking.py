from odoo import models, fields, api, _
from odoo.osv import expression

from datetime import date, datetime 
from odoo.exceptions import UserError as Warning

class stockPickingMutation(models.Model):
    _inherit = "stock.picking"

    mutation_order_id = fields.Many2one('tw.mutation.order', string='Mutation Order', check_company=False)

    def button_validate(self):
        self._update_destination_company_lot_ids()
        res = super(stockPickingMutation,self).button_validate()
        return res

    def _process_validate_picking(self):
        res = super(stockPickingMutation, self)._process_validate_picking()
        if self.sudo().mutation_order_id and self.picking_type_id.code == 'outgoing':
            is_return = any(m.origin_returned_move_id for m in self.move_ids)
            # Only create WH/IN when picking is fully done.
            # Non-blocking for backorders: backorder picking has state 'assigned', not 'done'.
            if not is_return and self.state == 'done':
                company_obj = self.env['res.company'].sudo().search([('partner_id', '=', self.partner_id.id)], limit=1)
                if not company_obj:
                    raise Warning(f"Please configure a partner for branch '{self.partner_id.name}' first.")

                self.sudo()._create_picking_intransit_dealer(company_obj)
        
        # Update Mutation Order state when incoming picking is validated (skip returns)
        if self.sudo().mutation_order_id and self.picking_type_id.code == 'incoming':
            is_return = any(m.origin_returned_move_id for m in self.move_ids)
            if not is_return:
                self.sudo()._update_mutation_order_state()
        
        # Recompute qty_outgoing and qty_incoming on lines
        if self.sudo().mutation_order_id:
            self.sudo().mutation_order_id.mutation_order_ids._compute_picking_qty()
        
        return res


    def _update_mutation_order_state(self):
        """Update Mutation Order state to 'done' when all incoming pickings are validated."""
        if not self.sudo().mutation_order_id:
            return
        
        mutation_order = self.sudo().mutation_order_id
        
        # Check if all incoming pickings are done
        incoming_pickings = self.env['stock.picking'].search([
            ('mutation_order_id', '=', mutation_order.id),
            ('picking_type_id.code', '=', 'incoming')
        ])
        
        all_done = all(p.state == 'done' for p in incoming_pickings) if incoming_pickings else False
        
        if all_done:
            mutation_order.action_done()



    def _create_picking_intransit_dealer(self, company_obj):
        """Create WH/IN picking at receiver's warehouse when WH/OUT is validated.
        
        Uses intercompany transit location (company_id=False) as source
        to ensure Odoo classifies the move as 'in' and creates journal entries.
        """
        if not company_obj:
            raise Warning(f"Please configure a partner for branch '{company_obj.name}' first.")
        
        warehouse = company_obj.sudo().with_company(company_obj.id).warehouse_id
        if not warehouse:
            raise Warning(f"Please configure a warehouse for branch '{company_obj.name}' first.")
        
        # Use interbranch in picking type based on division
        if self.division == 'Sparepart':
            picking_type_obj = warehouse.sudo().with_company(company_obj.id).interbranch_in_sparepart_type_id
        else:
            picking_type_obj = warehouse.sudo().with_company(company_obj.id).interbranch_in_unit_type_id

        if not picking_type_obj:
            division_label = self.division or 'Unit'
            raise Warning(_(
                "No interbranch in picking type (%(division)s) found for warehouse %(warehouse)s. "
                "Please configure interbranch picking types in warehouse settings.",
                division=division_label, warehouse=warehouse.name))
        
        # Gunakan intercompany transit (company_id=False) sebagai source location
        # agar Odoo mengklasifikasikan move sebagai IN dan membuat journal entry
        location_src_id = picking_type_obj.default_location_src_id.id
        
        # TODO: Hidupkan untuk skema lebih dari 1 STEP
        # if self.location_dest_id.id != location_src_id and self.mutation_order_id:
        #     raise Warning(f"Perhatian! Lokasi tujuan pengiriman (WHO) '{self.location_dest_id.display_name}' tidak selaras dengan lokasi transit penerimaan (WHI).\n Hal ini dapat menyebabkan stock nyangkut di proses transit. Setting operation type dan Pastikan keduanya sama.")
        
        location_dest_id = picking_type_obj.default_location_dest_id.id

        # Create Stock Picking
        picking_obj = self.env['stock.picking'].sudo().with_company(company_obj).create({
            'company_id': company_obj.id,
            'division': self.division,
            'date': date.today(),
            'partner_id': self.company_id.partner_id.id,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'origin': self.origin,
            'mutation_order_id': self.sudo().mutation_order_id.id, 
            'picking_type_id': picking_type_obj.id,
            'min_date': self.end_date,
            'location_id': location_src_id,
            'location_dest_id': location_dest_id,
        })

        # Create Stock Moves
        for move in self.move_ids_without_package:
            lot_ids = move.move_line_ids.mapped('lot_id')
            move_vals = {
                'company_id': company_obj.id,
                'picking_id': picking_obj.id,
                'picking_type_id': picking_type_obj.id,
                'origin': self.origin,
                'name': move.product_id.default_code or '',
                'product_uom': move.product_id.product_tmpl_id.uom_id.id,
                'product_id': move.product_id.id,
                'product_uom_qty': move.product_uom_qty,
                'price_unit': move.price_unit,
                'date': datetime.now(),
                'location_id': location_src_id,
                'location_dest_id': location_dest_id,
                'restrict_lot_ids': [(6, 0, lot_ids.ids)],
            }
            if move.bom_line_id:
                move_vals['bom_line_id'] = move.bom_line_id.id
            
            # Use bypass_entire_pack context to prevent duplicate BoM explosion on the receiving end
            move_obj = self.env['stock.move'].sudo().with_company(company_obj).with_context(bypass_entire_pack=True).create(move_vals)
            if move_obj:
                move_obj.with_context(bypass_entire_pack=True)._action_confirm()
                # * update company transfer lot - mark lot as in transit to receiver
                if move.move_line_ids:
                    self._update_company_transfer_lot(move.move_line_ids, company_obj)

        # Force Assign then Unreserve: action_assign populates detailed operations,
        # do_unreserve resets qty to 0 so receiver must fill manually (no auto FIFO).
        # Note: lot.company_id is NOT updated here intentionally — it is updated at
        # WH/IN validation time (button_validate / batch action_done) to prevent the lot
        # from appearing as "already at receiver" before the incoming picking is validated.
        picking_obj.sudo().with_company(company_obj).action_assign()
        picking_obj.do_unreserve()

    def _update_destination_company_lot_ids(self):
        for picking in self:
            if picking.sudo().mutation_order_id and picking.picking_type_id.code == 'incoming':
                self._process_update_company_lot_id_move_lines(picking)

    def _process_update_company_lot_id_move_lines(self, picking_obj):
        for move_obj in picking_obj.move_ids:
            move_line_objs = move_obj.move_line_ids
            if move_line_objs:
                for move_line_obj in move_line_objs:
                    lot_obj = move_line_obj.lot_id
                    if lot_obj and lot_obj.company_id != picking_obj.company_id:
                        lot_obj.suspend_security().write({
                            'company_id': picking_obj.company_id.id,
                            'company_transfer_id': False
                        })

    def _update_company_transfer_lot(self, stock_move_line_objs, branch_requester_obj):
        for stock_move in stock_move_line_objs:
            if stock_move.lot_id:
                stock_move.lot_id.suspend_security().write({
                    'company_transfer_id': branch_requester_obj.id
                })