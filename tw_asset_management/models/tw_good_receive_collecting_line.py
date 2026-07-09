# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command
from odoo.osv import expression

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from datetime import date, datetime

# 5: local imports

# 6: Import of unknown third party lib



class TwGoodReceiveCollectingLine(models.Model):
    _name= "tw.good.receive.collecting.line"
    _description= 'Collecting Good Receive Lines'
    _order = "id DESC"

    @api.depends('price','discount','tax_ids')
    def _compute_subtotal(self):
        for line in self:
            currency = line.collecting_id.company_id.currency_id
            if not line.price:
                 line.price = line.purchase_order_line_id.price_unit
            price_subtotal = price_total = total = (line.price * line.qty) - line.discount
            tax = 0.0

            if line.tax_ids:
                computed_tax = line.tax_ids.compute_all(total, currency)
                price_subtotal = computed_tax.get('total_excluded')
                price_total = computed_tax.get('total_included')
                tax = sum([tax['amount'] for tax in computed_tax['taxes']])

            line.price_tax = tax
            line.price_subtotal = price_subtotal
            line.price_total = price_total
    
    references_1 = fields.Char(string='Reference 1')
    references_2 = fields.Char(string='Reference 2')
    references_3 = fields.Char(string='Reference 3')
    references_4 = fields.Char(string='Reference 4')
    references_5 = fields.Char(string='Reference 5')

    date_maturity = fields.Date('Due Date')
    document_date = fields.Date('Document Date')
    price_accrual = fields.Float(string='Accrual', digits='Account')
    price = fields.Float(string='Price Actual', digits='Account')
    description = fields.Char('Description')
    origin = fields.Char('Origin')
    discount = fields.Float(string='Discount', digits='Account')
    qty = fields.Integer(string='Qty',default=1)
    is_asset = fields.Boolean(string='Asset?',related='product_id.is_asset')

    price_subtotal = fields.Float(string='Subtotal', digits='Account', compute='_compute_subtotal',precompute=True,store=True)
    price_total = fields.Float(string='Total', digits='Account', compute='_compute_subtotal',precompute=True,store=True)
    price_tax = fields.Float(string='Price Tax', digits='Account', compute='_compute_subtotal',precompute=True,store=True)

    collecting_id = fields.Many2one(comodel_name='tw.good.receive.collecting', string='Collecting ID')
    company_id = fields.Many2one(comodel_name='res.company', string='Branch')
    product_id = fields.Many2one(comodel_name='product.product',string='Product')
    account_id = fields.Many2one('account.account', 'Account')
    partner_id = fields.Many2one('res.partner', string='Partner')
    collecting_good_receive_id = fields.Many2one(comodel_name='tw.good.receive.asset.line', string='Collecting Good Receive')
    tax_ids = fields.Many2many('account.tax', 'invoice_good_receive_collecting_item_tax', 'invoice_good_recieve_collecting_line_id', 'tax_id', 'Taxes')
    purchase_order_line_id = fields.Many2one('purchase.order.asset.line',string='Purchase Order Line')
    purchase_order_id = fields.Many2one('purchase.order.asset',string='Purchase Order')
    
    @api.onchange('discount')
    def _onchange_discount(self):
        if self.discount < 0:
            raise Warning('Diskon tidak boleh minus, silahkan input kelebihan amount di actual price!')

    @api.model_create_multi
    def create(self, vals_list):
        create = super(TwGoodReceiveCollectingLine, self).create(vals_list)
        return create
    
    def _prepare_base_line_for_taxes_computation(self, **kwargs):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        additional_params = self._get_tax_base_line_additional_params()
        return self.env['account.tax']._prepare_base_line_for_taxes_computation(
            self,
            **additional_params,
        )

    def _get_tax_base_line_additional_params(self):
        self.ensure_one()
        return {
            'tax_ids': self.tax_ids,
            'quantity': self.qty,
            'partner_id': self.collecting_id.partner_id,
            'currency_id': self.collecting_id.company_id.currency_id,
            'price_unit': self._get_price_after_discount(),
        }

    def _get_price_after_discount(self):
        self.ensure_one()
        return self.price - self.discount

     
    
