from odoo import models, fields
from odoo.tools.float_utils import float_compare, float_round, float_is_zero
import logging

_logger = logging.getLogger(__name__)


class TWStockMove(models.Model):
    _inherit = "stock.move"

    consolidated_qty = fields.Float('Consolidated Qty')

    def _get_price_unit(self):
        """Override to fix incorrect SVL calculation when Extras moves share the same
        purchase_line_id as the main product (Motor/Unit) move.

        Root cause: purchase_mrp._prepare_phantom_move_values() propagates purchase_line_id
        to all BOM-exploded extras moves. This causes line.move_ids to return both the
        main product move AND all extras moves. When computing receipt_value from
        stock_valuation_layer_ids, extras SVLs are included, inflating receipt_value
        and causing price_unit = remaining_value / remaining_qty to be incorrect.

        Fix: Filter move_layer to only include SVLs from moves whose product_id matches
        the PO line product_id, excluding Extras moves.
        """
        self.ensure_one()

        if self._should_ignore_pol_price():
            return super()._get_price_unit()

        # Only apply fix when the move product matches the PO line product
        # (i.e. main product moves, not BOM kit components)
        line = self.purchase_line_id
        if not line:
            return super()._get_price_unit()

        # Check if this is an extras move (division == 'Extras')
        # Extras should use standard logic (ignore pol price via bom_line_id check in purchase_mrp)
        if self.division == 'Extras':
            return super()._get_price_unit()

        order = line.order_id
        received_qty = self._get_qty_received_without_self()
        price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')

        if line.product_id.purchase_method == 'purchase' and float_compare(
            line.qty_invoiced, received_qty, precision_rounding=line.product_uom.rounding
        ) > 0:
            # === FIX: Only include SVL from moves with the same product_id as PO line ===
            # Exclude extras moves that share purchase_line_id via BOM explosion
            main_product_moves = line.move_ids.sudo().filtered(
                lambda m: m.product_id == line.product_id
            )
            move_layer = main_product_moves.stock_valuation_layer_ids

            invoiced_layer = line.sudo().invoice_lines.stock_valuation_layer_ids

            # value on valuation layer is in company's currency,
            # while value on invoice line is in order's currency
            receipt_value = 0
            for layer in move_layer:
                if not layer._should_impact_price_unit_receipt_value():
                    continue
                receipt_value += layer.currency_id._convert(
                    layer.value, order.currency_id, order.company_id,
                    layer.create_date, round=False
                )
            if invoiced_layer:
                receipt_value += sum(invoiced_layer.mapped(
                    lambda l: l.currency_id._convert(
                        l.value, order.currency_id, order.company_id,
                        l.create_date, round=False
                    )
                ))

            total_invoiced_value = 0
            invoiced_qty = 0
            for invoice_line in line.sudo().invoice_lines:
                if invoice_line.move_id.state != 'posted':
                    continue
                adjusted_unit_price = (
                    invoice_line.price_unit * (1 - (invoice_line.discount / 100))
                    if invoice_line.discount else invoice_line.price_unit
                )
                if invoice_line.tax_ids:
                    invoice_line_value = invoice_line.tax_ids.compute_all(
                        adjusted_unit_price,
                        currency=invoice_line.currency_id,
                        quantity=invoice_line.quantity,
                        rounding_method="round_globally",
                    )['total_void']
                else:
                    invoice_line_value = adjusted_unit_price * invoice_line.quantity

                total_invoiced_value += invoice_line.currency_id._convert(
                    invoice_line_value, order.currency_id, order.company_id,
                    invoice_line.move_id.invoice_date, round=False
                )
                invoiced_qty += invoice_line.product_uom_id._compute_quantity(
                    invoice_line.quantity, line.product_id.uom_id, rounding_method="HALF-UP"
                )

            remaining_value = total_invoiced_value - receipt_value
            remaining_qty = invoiced_qty - line.product_uom._compute_quantity(
                received_qty, line.product_id.uom_id, rounding_method="HALF-UP"
            )
            has_remaining = (
                not order.currency_id.is_zero(remaining_value)
                and not float_is_zero(remaining_qty, precision_rounding=line.product_id.uom_id.rounding)
            )

            _logger.debug(
                "CI _get_price_unit: move=%s product=%s "
                "receipt_value=%.2f total_invoiced=%.2f remaining_value=%.2f remaining_qty=%.4f",
                self.id, self.product_id.display_name,
                receipt_value, total_invoiced_value, remaining_value, remaining_qty,
            )

            if order.currency_id != order.company_id.currency_id and has_remaining:
                price_unit = remaining_value / remaining_qty
            elif has_remaining:
                price_unit = float_round(remaining_value / remaining_qty, precision_digits=price_unit_prec)
            else:
                price_unit = line._get_gross_price_unit()
        else:
            price_unit = line._get_gross_price_unit()

        if order.currency_id != order.company_id.currency_id:
            convert_date = self._get_currency_convert_date()
            price_unit = order.currency_id._convert(
                price_unit, order.company_id.currency_id, order.company_id,
                convert_date, round=False
            )

        if self.product_id.lot_valuated:
            return dict.fromkeys(self.lot_ids, price_unit)
        return {self.env['stock.lot']: price_unit}

