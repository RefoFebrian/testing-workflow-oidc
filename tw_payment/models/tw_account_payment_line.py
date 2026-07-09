# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class AccountPaymentLine(models.Model):
    _name = "tw.account.payment.line"
    _description = "Payment Line"

    # 7: defaults methods
             
    @api.depends('currency_id')            
    def _get_currency_id(self):
        for record in self:
            move_line = record.move_line_id
            if move_line:
                currency_id =  move_line.currency_id and move_line.currency_id.id or move_line.company_id.currency_id.id
            else:
                currency_id =  record.payment_id.currency_id and self.payment_id.currency_id.id or self.payment_id.company_id.currency_id.id
            return currency_id


    # 8: fields
    name = fields.Char(string="Description")
    note = fields.Char('Note')
    type = fields.Selection([
        ('dr','Debit'),
        ('cr','Credit'),
        ('wo','Writeoff')], 'Dr/Cr/Wo')
    is_reconciled = fields.Boolean('Full Reconcile')
    date_original =  fields.Date(related='move_line_id.date', string='Date', readonly=True)
    date_due =  fields.Date(related='move_line_id.date_maturity', string='Due Date', readonly=True)
    
    amount = fields.Float('Amount', digits='Product Price', help='Amount yang di input user')
    amount_included = fields.Float('Amount Included', digits='Product Price',compute='_compute_amount_subtotal')
    amount_untaxed = fields.Float('Amount Untaxed', digits='Product Price')
    amount_subtotal = fields.Float('Subtotal Amount', digits='Product Price',compute='_compute_amount_subtotal', help='Amount hasil perhitungan pajak')
    amount_original = fields.Float(string='Original Amount', store=True, digits='Product Price', compute='_compute_balance')
    amount_unreconciled = fields.Float(string='Open Balance', store=True, digits='Product Price', compute='_compute_balance')
     
    # 9: relation fields 
    payment_id = fields.Many2one('tw.account.payment', 'Voucher', required=True, ondelete='cascade')
    account_id = fields.Many2one('account.account','Account', required=True)
    available_account_ids = fields.Many2many(comodel_name='account.account',compute='_compute_available_account_ids')
    partner_id = fields.Many2one(related='payment_id.partner_id', string='Partner', store=True)
    move_line_id = fields.Many2one('account.move.line', 'Journal Item', copy=False)
    company_id = fields.Many2one(related='payment_id.company_id',string='Branch', store=True, readonly=True)
    beneficiary_company_id = fields.Many2one('res.company', 'Beneficiary Branch', index=True, domain="[('parent_id', '!=', False)]")
    currency_id = fields.Many2one('res.currency', string='Currency',readonly=True,store=True, compute='_get_currency_id')
    tax_ids = fields.Many2many('account.tax', string='Tax')
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('payment_id.company_id','payment_id.type')
    def _compute_available_account_ids(self):
        for record in self:
            domain = [('company_ids', 'parent_of', record.payment_id.company_id.id)]
            payment_type = (record.payment_id.type or record.payment_id.payment_type) + '_detail'
            account_filter_domain = self.env['tw.account.filter'].get_account_domain(payment_type)
            if account_filter_domain:
                domain += account_filter_domain
            record.available_account_ids = self.env['account.account'].sudo().search(domain)

    @api.depends('amount', 'tax_ids')
    def _compute_amount_subtotal(self):
        for line in self:
            amount = line.amount
            price_subtotal = amount
            amount_included = amount
            if amount <= 0:
                if line.type != 'wo' and line.create_date:
                    raise Warning("Nilai Debit/Credit di detil harus lebih dari 0.")
    
            if line.tax_ids:
                computed_tax = line.tax_ids.compute_all(amount,line.currency_id)
                price_subtotal = computed_tax.get('total_void',0)
                amount_included = computed_tax.get('total_included',0)
                
            line.amount_included = amount_included
            line.amount_subtotal = price_subtotal
            
    @api.depends('move_line_id')
    def _compute_balance(self):
        res = {}
        for record in self:
            move_line = record.move_line_id or False
            company_currency = record.payment_id.journal_id.company_id.currency_id.id
            voucher_currency = record.payment_id.currency_id and record.payment_id.currency_id.id or company_currency
                        
            if not move_line:
                record.amount_original = 0.0
                record.amount_unreconciled = 0.0
            elif move_line.currency_id and voucher_currency == move_line.currency_id.id:
                record.amount_original = abs(move_line.amount_currency)
                record.amount_unreconciled = abs(move_line.amount_residual_currency)
            else :
                record.amount_original = record.env['res.currency'].compute(company_currency, voucher_currency, move_line.credit or move_line.debit or 0.0)
                record.amount_unreconciled = record.env['res.currency'].compute(company_currency, voucher_currency, abs(move_line.amount_residual))

    @api.onchange('is_reconciled')
    def onchange_reconcile(self):
        reconcile = self.is_reconciled
        if reconcile:
            self.amount = self.amount_unreconciled

    @api.onchange('amount')
    def _onchange_amount(self):
        if self.amount and self.type in ('dr','cr') and self.move_line_id:
            if self.amount > self.amount_unreconciled:
                raise Warning('Amount tidak boleh lebih besar dari Open Balance !')
            if self.amount != self.amount_unreconciled:
                self.is_reconciled = False
            else:
                self.is_reconciled = True

    @api.onchange('move_line_id')
    def onchange_move_line_id(self):
        if not self.payment_id.journal_id:
            return {
                'warning': {
                    'message': _("Harap isi Payment Method terlebih dahulu !"),
                }
            }

        if self.move_line_id:
            move_line = self.move_line_id
            ttype = 'dr' if move_line.credit else 'cr'
            journal = self.payment_id.journal_id.sudo()
            currency_id = self.currency_id.id or journal.company_id.currency_id.id
            company_currency = journal.company_id.currency_id.id

            if move_line.currency_id and currency_id == move_line.currency_id.id:
                amount_original = abs(move_line.amount_currency)
                amount_unreconciled = abs(move_line.amount_residual_currency)
            else:
                amount_original = move_line.company_id.currency_id._convert(
                    move_line.credit or move_line.debit or 0.0,
                    self.currency_id,
                    self.company_id,
                    self.payment_id.date,
                )
                amount_unreconciled = move_line.company_id.currency_id._convert(
                    abs(move_line.amount_residual),
                    self.currency_id,
                    self.company_id,
                    self.payment_id.date,
                )

            self.update({
                'name': move_line.move_id.name,
                'amount_original': amount_original,
                'amount': amount_unreconciled,
                'date_original': move_line.date,
                'date_due': move_line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'account_id': move_line.account_id.id,
                'type': ttype,
                'currency_id': move_line.currency_id.id or move_line.company_id.currency_id.id,
            })

    # 12: override methods

    # 13: action methods

    # 14: private methods
