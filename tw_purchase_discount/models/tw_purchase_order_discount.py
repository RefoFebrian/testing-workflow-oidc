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


class TwPurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # 7: defaults methods
    def _default_discount(self):
        discount_fields = {
            'discount_cash': 'Discount Cash',
            'discount_program': 'Discount Program',
            'discount_other': 'Discount Other'
        }
        
        discount_ids = []
        for field, name in discount_fields.items():
            discount = self._get_discount_product(name)
            discount_ids.append((0, 0, self._insert_discount_line(discount, 0)))

        return discount_ids
    
    # 8: fields
    
    # 9: relation fields
    order_line = fields.One2many('purchase.order.line', 'order_id', string='Order Lines', domain=[('is_discount', '=', False)])
    discount_ids = fields.One2many(
        'purchase.order.line', 'order_id', string="Discount Line",
        domain=[('is_discount', '=', True)], help="These purchases will be hidden in the forms (Disounts, Voucher etc.)", 
        default=_default_discount)
    product_category_ids = fields.Many2many(comodel_name="product.category", string="Product Category", store=False)
    
    # 10: constraints & sql constraints
    @api.constrains('discount_cash', 'discount_program', 'discount_other')
    def _check_discount(self):
        if self.discount_cash < 0 or self.discount_program < 0 or self.discount_other < 0:
            raise Warning(_('Discount cannot be negative!'))
    
    # 11: compute/depends & on change methods
    @api.depends_context('lang')
    @api.depends('order_line.price_subtotal', 'discount_ids.price_subtotal', 'currency_id', 'company_id')
    def _compute_tax_totals(self):
        AccountTax = self.env['account.tax']
        for order in self:
            if not order.company_id:
                order.tax_totals = False
                continue

            order_lines = []
            order_lines += order.order_line.filtered(lambda x: not x.display_type)
            order_lines += order.discount_ids.filtered(lambda x: x.is_discount)
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
            order.tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.currency_id or order.company_id.currency_id,
                company=order.company_id,
            )

    # 12: override methods
    
    # 13: action methods
    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)

    def write(self, vals):
        return super().write(vals)
    
    # 14: private methods
    def _get_discount_product(self, discount_name):
        product_category = self.env['product.category']
        parent_category = product_category.search([('name', '=', 'Discount')])
        prod_categ = product_category.search([('parent_id', 'child_of', parent_category.ids)])
        return self.env['product.product'].search([('default_code', '=', discount_name), ('categ_id', 'in', prod_categ.ids)], limit=1)
    
    def _insert_discount_line(self, discount, amount):
        return {
            'product_id': discount.id,
            'name': discount.default_code,
            'product_qty': 1,
            'product_uom': discount.uom_id.id,
            'price_unit': amount * -1,
            'taxes_id': [(6, 0, discount.supplier_taxes_id.ids or discount.product_tmpl_id.supplier_taxes_id.ids)],
            'is_discount': True
        }
