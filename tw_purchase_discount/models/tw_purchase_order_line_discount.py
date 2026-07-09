# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools import get_lang

# 5: local imports

# 6: Import of unknown third party lib


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    # 8: fields
    is_discount = fields.Boolean(help="Hide this line from the purchase order")
    discount_amount = fields.Float(string='Discount Amount')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('discount_amount', 'is_discount')
    def _onchange_discount_amount(self):
        if self.discount_amount > 0:
            if self.is_discount:
                self.price_unit = -self.discount_amount
            else:
                self.price_unit = self.price_unit - self.discount_amount
        elif self.discount_amount < 0:
            raise Warning(_('Discount cannot be negative!'))
        else:
            self.price_unit = self.price_unit
        
    def _product_id_change(self):
        if not self.product_id or self.product_id.name.startswith('Discount'):
            self.product_uom = self.product_id.uom_po_id or self.product_id.uom_id
            product_lang = self.product_id.with_context(
                lang=get_lang(self.env, self.partner_id.lang).code,
                partner_id=None,
                company_id=self.company_id.id,
            )
            self.name = self._get_product_purchase_description(product_lang)

            self._compute_tax_id()
        else:
            super()._product_id_change()

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    def write(self, vals):
        return super().write(vals)

    # 13: action methods

    # 14: private methods
    def _get_product_purchase_description(self, product_lang):
        if product_lang.categ_id.name == 'Discount':
            return product_lang.default_code
        return super()._get_product_purchase_description(product_lang)

    def _create_discount_move_line(self, move, discount_name, discount_amount):
        self.ensure_one()
        aml_currency = move and move.currency_id or self.currency_id
        date = move and move.date or fields.Date.today()
        purchase = self.order_id
        
        res = {
            'display_type': self.display_type or 'discount',
            'name': f"{discount_name} {purchase.name}",
            'quantity': 1,
            'discount': 0,
            'credit': discount_amount,
            'amount_currency': discount_amount,
            'price_unit': discount_amount,
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'purchase_line_id': self.id,
            'is_downpayment': self.is_downpayment,
        }
        if self.analytic_distribution and not self.display_type:
            res['analytic_distribution'] = self.analytic_distribution
        return res
    