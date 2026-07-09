# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, api

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class InheritStockMoveLinePurchase(models.Model):
    _inherit = "stock.move.line"
    # INFO : Override Stock Move Line to connect Lot with Purchase Order
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._update_lot_purchase_order()
        return res

    def write(self, vals):
        res = super().write(vals)
        if vals.get('lot_id'):
            self._update_lot_purchase_order()
        return res

    # 13: action methods

    # 14: private methods
    def _prepare_new_lot_vals(self):
        """
        Override to add purchase_order_id to the lot values when 
        receiving from a Purchase Order.
        """
        vals = super()._prepare_new_lot_vals()
        if self.move_id.purchase_line_id:
            vals['purchase_order_id'] = self.move_id.purchase_line_id.order_id.id
        return vals

    def _update_lot_purchase_order(self):
        """
        Update purchase_order_id on existing lots when receiving from a PO.
        This handles cases where lot already exists but doesn't have purchase_order_id.
        """
        for move_line in self:
            # Only update if:
            # 1. lot_id exists
            # 2. move has purchase_line_id (from PO)
            # 3. lot doesn't have purchase_order_id yet
            if (move_line.lot_id 
                and move_line.move_id.purchase_line_id 
                and not move_line.lot_id.purchase_order_id):
                move_line.lot_id.sudo().write({
                    'purchase_order_id': move_line.move_id.purchase_line_id.order_id.id
                })

