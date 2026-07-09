# 1: imports of python lib
from datetime import date, datetime, timedelta, time

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

# 4: imports from odoo modules
import logging
_logger = logging.getLogger(__name__)

# 5: local imports

# 6: Import of unknown third party lib

class StockPicking(models.Model):
    _inherit = "stock.picking"

    # 7: fields

    # 8: relation fields
    part_hotline_id = fields.Many2one('tw.part.hotline', 'No Hotline', compute='_compute_source_hotline', store=True)

    # 9: constraints & sql constraints

    # 10: compute/depends & on change methods
    @api.depends('origin', 'location_id.type_id')
    def _compute_source_hotline(self):
        for rec in self:
            rec.part_hotline_id = False
            if rec.origin:
                # Check PO Transaction
                po_obj = self.env['purchase.order'].sudo().search([('name', '=', rec.origin)], limit=1)
                if po_obj and po_obj.part_hotline_id:
                    rec.part_hotline_id = po_obj.part_hotline_id

                wo_obj = self.env['tw.work.order'].sudo().search([('name', '=', rec.origin)], limit=1)
                if wo_obj:
                    hotline = wo_obj.order_line.mapped('part_hotline_id')[:1]
                    if hotline:
                        rec.part_hotline_id = hotline

    # 11: override methods

    # 12: action methods
    def action_view_part_hotline(self):
        self.ensure_one()
        if not self.part_hotline_id:
            raise UserError('Part Hotline tidak ditemukan pada Picking ini!')
        return {
            'name': 'Part Hotline',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.part.hotline',
            'view_mode': 'form',
            'res_id': self.part_hotline_id.id,
        }

    # 13: compute/depends & on change methods

    # 14: private methods
    def _process_validate_move(self,move):
        res = super(StockPicking, self)._process_validate_move(move)
        if move.picking_id.part_hotline_id:
            hotline_id = self._validation_process_hotline_id(move)
            if hotline_id:
                hotline_id._check_po_done()
        return res

    def _validation_process_hotline_id(self,move):
        hotline_prod = self.env['tw.part.hotline.detail'].sudo().search([
            ('hotline_id', '=', move.picking_id.part_hotline_id.id),
            ('product_id', '=', move.product_id.id)
        ], limit=1)
        

        hotline_id = False
        wo_obj = self.env['tw.work.order'].sudo().search([('name', '=', move.picking_id.origin)], limit=1)
        ps_obj = self.env['tw.part.sales'].sudo().search([('name', '=', move.picking_id.origin)], limit=1)

        if not hotline_prod and (wo_obj or ps_obj):
            raise UserError('No Hotline %s tidak memesan product %s, Cek kembali No Hotline !' % 
                            (move.picking_id.part_hotline_id.name, move.product_id.display_name))
        if hotline_prod:
            vals_detail = {}
            qty_prod = hotline_prod.qty
            hotline_qty_available = hotline_prod.qty_available
            move_qty = move.quantity
            
            if wo_obj:
                # Work Order Picking
                if hotline_qty_available < move_qty:
                    raise UserError('Product Hotline %s, Qty sudah melebihi qty supply ! \n Qty Pada Move %s, Qty Tersedia untuk Hotline WO %s, Cek kembali No Hotline !' % 
                                    (move.product_id.display_name, move_qty, hotline_qty_available))

                # vals_detail['qty_reserved'] = hotline_qty_available - move_qty
                vals_detail['no_wo'] = self.origin

            elif ps_obj:
                # Part Sales Picking
                if hotline_qty_available < move_qty:
                    raise UserError('Product Hotline %s, Qty sudah melebihi qty supply ! \n Qty Pada Move %s, Qty Tersedia untuk Hotline PS %s, Cek kembali No Hotline !' % 
                                    (move.product_id.display_name, move_qty, hotline_qty_available))
                
                # vals_detail['qty_reserved'] = hotline_qty_available - move_qty
                vals_detail['no_ps'] = self.origin

            else:
                # Purchase Order Picking
                qty_spl_awal = hotline_prod.qty_po
                qty_spl_akhir = qty_spl_awal + move.quantity

                if hotline_prod.qty_po > hotline_prod.qty:
                    raise UserError('Product %s sudah disupply, Qty Spl PO %s !' % 
                                    (move.product_id.display_name, qty_spl_awal))
                
                if qty_spl_akhir > qty_prod:
                    raise UserError('Product Hotline %s, Qty sudah melebihi qty supply ! \n Qty Product %s, Qty Supply PO %s, Cek kembali No Hotline !' % 
                                    (move.product_id.display_name, qty_prod, qty_spl_akhir))
                
                # Tambahkan QTY PO Hotline Detail setelah Picking
                vals_detail['qty_po'] = qty_spl_akhir
                vals_detail['no_po'] = self.origin
                vals_detail['po_date'] = self.date 
            
            hotline_prod.sudo().write(vals_detail)
            hotline_id = hotline_prod.hotline_id

            # Cek apakah semua detail hotline sudah terpenuhi (WO/PS picking)
            if (wo_obj or ps_obj) and hotline_id and hotline_id.status_po == 'done':
                all_fulfilled = all(
                    detail.qty_reserved >= detail.qty
                    for detail in hotline_id.part_detail_ids
                )
                if all_fulfilled:
                    hotline_id.sudo().write({'state': 'done'})

        return hotline_id

    # karena destination location bisa diambil dari in_hotline_type_id
    def _get_to_store_picking_type(self, warehouse):
        result = super()._get_to_store_picking_type(warehouse)
        if warehouse.in_hotline_type_id:
            result = result + (warehouse.in_hotline_type_id.id,)
        elif self.part_hotline_id:
            raise UserError('Type Picking In Hotline tidak ditemukan di Warehouse %s !' % warehouse.name)
        _logger.info("result <<<<<< Get To Store Picking: %s", result)
        return result