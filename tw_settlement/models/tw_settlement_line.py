# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning
from odoo.tools import SQL

# 5: local imports
import logging

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)


class TwSettlementLine(models.Model):
    _name = "tw.settlement.line"
    _description = "Settlement Line"

    
    
    # 8: fields
    amount = fields.Float(string='Amount',required=True)

    price_tax = fields.Float(string='Price Tax', digits='Product Price', compute='_compute_subtotal')
    price_subtotal = fields.Float(string='Subtotal Untaxed', digits='Product Price', compute='_compute_subtotal')
    price_total = fields.Float(string='Total', digits='Product Price', compute='_compute_subtotal')

    # 9: relation fields
    settlement_id = fields.Many2one('tw.settlement',ondelete='cascade')
    account_id = fields.Many2one('account.account',string='Account',domain="[('company_ids', 'in', company_id)]",required=True)
    company_id = fields.Many2one('res.company', string='Branch')
    supplier_id = fields.Many2one('res.partner', string='Supplier', domain="[('category_id.name','in',('Principle','Supplier'))]")
    tax_id = fields.Many2many('account.tax','avp_settlement_tax', 'settlement_id', 'tax_id', 'Taxes', domain=[('price_include','=',False)])         
    
    @api.depends('amount','tax_id')
    def _compute_subtotal(self):
        for line in self:
            currency = line.company_id.currency_id if line.company_id else False
            price_subtotal = price_total = total = line.amount
            tax = 0.0
            
            if line.tax_id and currency:
                computed_tax = line.tax_id.compute_all(total, currency)
                price_subtotal = computed_tax.get('total_excluded')
                price_total = computed_tax.get('total_included')
                tax = sum([tax['amount'] for tax in computed_tax['taxes']])

            line.price_tax = tax
            line.price_subtotal = price_subtotal
            line.price_total = price_total

    @api.onchange('amount')
    def onchange_amount(self):
        if self.amount:
            if self.amount < 0:
                raise Warning('Tidak boleh input nilai negatif')
            
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
            'tax_ids': self.tax_id,
            'quantity': 1,
            'partner_id': self.supplier_id,
            'currency_id': self.settlement_id.company_id.currency_id,
            'price_unit': self.amount,
        }
