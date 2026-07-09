from collections import defaultdict

import markupsafe

from odoo import Command, models, fields, api, _
from odoo.exceptions import UserError as Warning
from odoo.tools import frozendict, SQL


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _compute_currency_amount(self, move_line, amount):
        company_currency = self.journal_id.company_id.currency_id.id
        voucher_currency = self.currency_id and self.currency_id.id or company_currency
        
        if move_line.currency_id and voucher_currency == move_line.currency_id.id:
            return abs(amount)
        else :
            return self.env['res.currency'].compute(company_currency, voucher_currency, abs(amount))

    def _prepare_line_ids_vals(self, invoice_line):
        vals = []
        for line in invoice_line:
            amount = self._compute_currency_amount(line, line.amount_residual)
            is_reconciled = sum([amount, line.amount_residual]) == 0
            vals.append([0, 0, {
                'name': line.name,
                'type': 'dr' if line.move_type == 'in_invoice' else 'cr',
                'is_reconciled': is_reconciled,
                'date_original': line.date,
                'date_due': line.date_maturity,
                'amount': amount,
                'amount_untaxed': amount, # temporary using amount, since tax usually is inserted into write off lines
                'amount_original': line.credit if line.credit > 0 else line.debit,
                'amount_unreconciled': line.amount_residual,
                'account_id': line.account_id.id,
                'partner_id': line.partner_id.id,
                'move_line_id': line.id,
                'company_id': line.company_id.id,
                'currency_id': line.currency_id.id
            }])

        return vals

    # TODO: this methods could be superceded by _create_payment_vals_from_batch
    #       from other modules, prepare for modularization ✊ (e.g. tw_purchase_order)
    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        context = self.env.context
        model = context.get('active_model')
        ids = context.get('active_ids')
        
        invoice = self.env[model].browse(ids).move_id
        payment_values = batch_result.get('payment_values')
        payment_type = payment_values.get('payment_type')
        
        if payment_type == 'outbound':
            payment_vals['type'] = 'supplier_payment'
            payable_line = invoice.line_ids.filtered(lambda x: x.credit > 0 and x.account_id.account_type == 'liability_payable')
            payment_vals['line_dr_ids'] = self._prepare_line_ids_vals(payable_line)
        else:
            payment_vals['type'] = 'customer_payment'
            receivable_line = invoice.line_ids.filtered(lambda x: x.debit > 0 and x.account_id.account_type == 'asset_receivable')
            payment_vals['line_cr_ids'] = self._prepare_line_ids_vals(receivable_line)
                
        return payment_vals

    def _create_payment_vals_from_batch(self, batch_result):
        payment_vals = super()._create_payment_vals_from_batch(batch_result)
        print ('\n_create_payment_vals_from_batch\n')
        return payment_vals

