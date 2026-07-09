# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwDealerSaleOrderSummary(models.Model):
    _name = "tw.dealer.sale.order.summary"
    _description = "Summary Discount Dealer Sales Order"

    # 7: defaults methods

    # 8: fields
    product_qty = fields.Integer('Qty')
    price_unit = fields.Float('Price Unit')
    price_unit_untaxed = fields.Monetary('Price Unit Untaxed', compute='_compute_price_unit_untaxed', currency_field='currency_id', precompute=True, store=True)
    price_unit_purchase = fields.Float('Price Purchase')
    discount_regular = fields.Float('Discount Regular')
    direct_discount = fields.Float('Direct Discount')
    average_gross_profit = fields.Monetary('Average Gross Profit', compute='_compute_average_gross_profit', currency_field='currency_id', precompute=True, store=True)
    average_discount = fields.Monetary('Average Discount', compute='_compute_average_discount', currency_field='currency_id', precompute=True, store=True)
    gross_profit_unit = fields.Float('GP Unit')

    # 9: relation fields
    currency_id = fields.Many2one(comodel_name='res.currency',string='Currency',compute='_compute_currency_id', store=True, readonly=False, precompute=True)
    tax_id = fields.Many2many(comodel_name='account.tax',string="Taxes",relation='tw_dealer_sale_order_summary_tax_rel',column1='summary_id', column2='tax_id')
    order_id = fields.Many2one('tw.dealer.sale.order')
    product_id = fields.Many2one('product.product','Product')

    @api.depends('order_id')
    def _compute_currency_id(self):
        for summary in self:
            summary.currency_id = summary.order_id.currency_id or summary.order_id.company_id.currency_id
    
    @api.depends('price_unit','tax_id','currency_id','product_qty','product_id')
    def _compute_price_unit_untaxed(self):
        for summary in self:
            currency = summary.currency_id
            tax_result = summary.tax_id.compute_all(summary.price_unit, currency=currency, quantity=summary.product_qty, product=summary.product_id)
            summary.price_unit_untaxed = tax_result['total_excluded']
            
    @api.depends('product_qty','price_unit','price_unit_purchase','discount_regular')
    def _compute_average_gross_profit(self):
        for summary in self:
            gp_total = summary._get_gp()
            summary.average_gross_profit = gp_total / summary.product_qty

    @api.depends('product_qty','discount_regular')
    def _compute_average_discount(self):
        for summary in self:
            diskon = summary._get_discount()
            summary.average_discount = diskon / summary.product_qty

    def _get_gp(self):
        self.ensure_one()
        return self.gross_profit_unit

    def _get_discount(self):
        self.ensure_one()
        return self.discount_regular