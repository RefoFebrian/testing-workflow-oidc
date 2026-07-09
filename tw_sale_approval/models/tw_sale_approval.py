# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.tools import float_is_zero

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class InheritSaleOrder(models.Model):
    _name = "tw.sale.order"
    _inherit = ["tw.sale.order", "tw.approval.mixin"]

    # 7: defaults methods

    # 8: fields
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('approved', 'Approved'),
        ('sale',),
        ('done',),
    ], string="Status")

    approval_amount = fields.Float(
        string='Approval Amount',
        compute='_compute_approval_amount',
        help="Sparepart: max discount %% across lines. Unit: total qty."
    )

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('order_line.price_unit', 'order_line.product_uom_qty',
                 'order_line.price_subtotal', 'order_line.cogs',
                 'order_line.tax_id', 'division')
    def _compute_approval_amount(self):
        """Compute approval amount based on division.

        Ported from Odoo 8 teds_approval_so.py:
        - Sparepart: max discount % = (1 - (margin_after_disc / margin_before_disc)) * 100
        - Unit: total product_uom_qty
        """
        for order in self:
            amount = 0.0
            if order.division == 'Sparepart':
                currency_rounding = order.currency_id.rounding or 0.01
                for line in order.order_line:
                    if line.display_type or line.product_uom_qty <= 0:
                        continue

                    qty = line.product_uom_qty
                    hpp_total = (line.cogs or 0.0) * qty

                    # Calculate sum of tax percentages
                    tax_amount = 0.0
                    for tax in line.tax_id:
                        if tax.amount_type == 'percent':
                            tax_amount += tax.amount / 100.0

                    # margin_bawah: Margin Asli (Profit Harapan sebelum diskon)
                    margin_bawah = ((line.price_unit / (tax_amount + 1.0)) * qty) - hpp_total
                    
                    # V8 exact fallback untuk cegah bagi nol
                    if margin_bawah == 0:
                        margin_bawah = 0.001
                        
                    # margin_atas: Margin Aktual (Profit sesudah diskon)
                    margin_atas = line.price_subtotal - hpp_total
                    
                    # V8 calculation: Erosi Margin
                    value = (1 - (margin_atas / margin_bawah)) * 100

                    if amount < value:
                        amount = value

                amount = round(amount, 2)

            elif order.division == 'Unit':
                for line in order.order_line:
                    if line.display_type:
                        continue
                    amount += line.product_uom_qty

            order.approval_amount = amount

    # 12: override methods
    def _get_state_value(self):
        """Mengambil value yang sesuai dengan key di state."""
        selection = self._fields.get('state') and self._fields['state'].selection
        return dict(selection).get(self.state, self.state) if selection else self.state

    def _get_amount_field(self):
        """Override mixin: use approval_amount as the value for approval matrix."""
        return "approval_amount"

    # 13: action methods
    def validate_order(self):
        self._validate_order()
        return super().validate_order()

    def action_request_approval(self):
        """Request for approval with validations ported from Odoo 8."""
        if self.state not in ('draft','none'):
            raise Warning(f'Silakan refresh halaman SO ini, karena state sudah {self._get_state_value()}')
        self.ensure_one()

        if not self.order_line:
            raise ValidationError("Produk belum diisi")

        for line in self.order_line:
            if line.display_type:
                continue
            if line.price_unit < 1:
                raise ValidationError(
                    "Unit Price Product '%s' tidak boleh '%s'" % (line.product_id.name, line.price_unit)
                )

        return super().action_request_approval(code='sale')