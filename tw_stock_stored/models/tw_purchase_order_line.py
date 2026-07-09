
from odoo import SUPERUSER_ID, api, Command, fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def copy_data(self, default=None):
        if default is None:
            default = {}
        default['consolidated_qty'] = 0
        return super(PurchaseOrderLine, self).copy_data(default)

    @api.depends('move_ids.state', 'move_ids.product_uom', 'move_ids.quantity')
    def _compute_qty_received(self):
        from_stock_lines = self.filtered(lambda order_line: order_line.qty_received_method == 'stock_moves')
        super(PurchaseOrderLine, self - from_stock_lines)._compute_qty_received()
        for line in self:
            if line.qty_received_method == 'stock_moves':
                total = 0.0
                # In case of a BOM in kit, the products delivered do not correspond to the products in
                # the PO. Therefore, we can skip them since they will be handled later on.
                for move in line._get_po_line_moves():
                    if move.state == 'done' or move.picking_id.state == 'stored':
                        if move._is_purchase_return():
                            if not move.origin_returned_move_id or move.to_refund:
                                total -= move.product_uom._compute_quantity(move.quantity, line.product_uom, rounding_method='HALF-UP')
                        elif move.origin_returned_move_id and move.origin_returned_move_id._is_dropshipped() and not move._is_dropshipped_returned():
                            # Edge case: the dropship is returned to the stock, no to the supplier.
                            # In this case, the received quantity on the PO is set although we didn't
                            # receive the product physically in our stock. To avoid counting the
                            # quantity twice, we do nothing.
                            pass
                        elif move.origin_returned_move_id and move.origin_returned_move_id._is_purchase_return() and not move.to_refund:
                            pass
                        else:
                            if move._is_last_move_from_route():
                                total += move.product_uom._compute_quantity(move.quantity, line.product_uom, rounding_method='HALF-UP')
                line._track_qty_received(total)
                line.qty_received = total