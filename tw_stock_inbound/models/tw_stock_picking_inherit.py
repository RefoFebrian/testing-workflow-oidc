# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwStockPickingInherit(models.Model):
    _inherit = "stock.picking"
    _description = "Stock Picking"

    # 7: defaults methods

    # 8: fields
    is_return_picking = fields.Boolean(string="Is Return Picking", compute="_compute_is_return_picking", help="True jika picking ini merupakan hasil Return.")

    # 9: relation fields
    stock_inbound_id = fields.Many2one(comodel_name='tw.stock.inbound', string="Stock Inbound")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('move_ids.origin_returned_move_id')
    def _compute_is_return_picking(self):
        for picking in self:
            picking.is_return_picking = any(move.origin_returned_move_id for move in picking.move_ids)

    # 12: override methods

    # 13: action methods
    def _prepare_update_lot(self, picking_obj, move, move_line):
        res = super(TwStockPickingInherit, self)._prepare_update_lot(picking_obj, move, move_line)
        if picking_obj.stock_inbound_id:
            res.update({'stock_inbound_id': picking_obj.stock_inbound_id.id})
            picking_obj.stock_inbound_id.suspend_security().action_done()
        return res

    def _process_validate_picking(self):
        res = super(TwStockPickingInherit, self)._process_validate_picking()
        
        # Sync values from batch if it has a stock inbound ID
        if self.batch_id and self.batch_id.stock_inbound_id:
            self.batch_id.suspend_security()._set_stock_inbound_id(self)
            
        if self.stock_inbound_id:
            self._add_qty_receipt()
            self.stock_inbound_id.suspend_security().action_done()
        return res
    
    def _add_qty_receipt(self):
        """Update amount_receipt on stock inbound when picking is validated."""
        for picking in self:
            if picking.stock_inbound_id:
                inbound_division = picking.stock_inbound_id.division
                inbound_uom = picking.stock_inbound_id.amount_of_load_uom
                
                # Filter moves that are done and match the inbound division
                valid_moves = picking.move_ids.filtered(
                    lambda m: m.state == 'done' and m.division == inbound_division
                )
                
                if inbound_uom == 'package':
                    # Count unique destination packages from move lines
                    unique_packages = set()
                    for move in valid_moves:
                        for move_line in move.move_line_ids:
                            if move_line.result_package_id:
                                unique_packages.add(move_line.result_package_id.id)
                    qty_received = len(unique_packages)
                else:
                    # Default: sum of move quantities (for 'unit' UoM)
                    qty_received = sum(move.quantity for move in valid_moves)
                
                if qty_received > 0:
                    current_receipt = picking.stock_inbound_id.amount_receipt
                    new_receipt = current_receipt + int(qty_received)
                    if new_receipt > picking.stock_inbound_id.amount_of_load:
                        raise Warning(
                            "Qty pada Receipt %s lebih besar dari pada Qty Load %s"
                            % (new_receipt, picking.stock_inbound_id.amount_of_load)
                        )
                    picking.stock_inbound_id.suspend_security().write({
                        'amount_receipt': new_receipt
                    })
