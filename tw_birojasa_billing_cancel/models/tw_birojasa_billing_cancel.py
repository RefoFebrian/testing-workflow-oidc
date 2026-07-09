# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError as Warning
from datetime import datetime

class TwBirojasaBillingCancel(models.Model):
    _name = "tw.birojasa.billing.cancel"
    _description = 'Tagihan Birojasa Cancel'
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _order = 'id desc'


    def _get_default_date(self): 
        return datetime.now()

    birojasa_billing_id = fields.Many2one(
        'tw.birojasa.billing.process',
        string='Birojasa Billing',
        required=True,
    )
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.birojasa_billing_id = False

    # Override Methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('birojasa_billing_id'):
                birojasa_billing_id = self.env['tw.birojasa.billing.process'].browse(vals['birojasa_billing_id'])
                vals['transaction_name'] = birojasa_billing_id.name
                name = "X" + birojasa_billing_id.name
                self._check_duplicate_transaction(name)
                vals['name'] = "X" + birojasa_billing_id.name
                vals['date'] = self._get_default_date()
        return super().create(vals_list)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('You can only delete draft cancellations.'))
        return super().unlink()

    # Business Methods
    def action_request_approval(self):
        return super().action_request_approval(value=5)

    def check_invoices(self):
        invoice_ids = self.birojasa_billing_id.invoice_id
        message = ""
        checked_invoices = set()
        for invoice_id in invoice_ids:
            if invoice_id.name in checked_invoices:
                continue
            
            # Check payment_state - if already paid (partial/paid/in_payment), cannot cancel
            if invoice_id.payment_state in ('paid', 'partial', 'in_payment'):
                message += invoice_id.name + ", "
                checked_invoices.add(invoice_id.name)
                continue

            # Alternative: check if there are reconciled lines
            for line_id in invoice_id.line_ids:
                if line_id.reconciled or line_id.full_reconcile_id:
                    message += invoice_id.name + ", "
                    checked_invoices.add(invoice_id.name)
                    break
        return message.rstrip(", ")
    
    def invoice_cancel(self):
        """
        Reverse the PRBJ invoice and release the accrual reconciliation.
        Flow:
          1. Un-reconcile lines on the accrual account (21210301) that were
             created when billing was confirmed, so accrual can be reused.
          2. Create a standard reversal for the invoice.
        """
        invoice_ids = self.birojasa_billing_id.invoice_id
        branch_config_obj = self.company_id.branch_setting_id
        for invoice in invoice_ids:
            journal_birojasa_billing_cancel_id = branch_config_obj.account_setting_id.journal_birojasa_billing_cancel_id.id
            if not journal_birojasa_billing_cancel_id:
                raise Warning("Attention! The Birojasa Billing Cancel Journal hasn't been Created. Please Set it up First.")

            # ── Lepas reconcile accrual lines sebelum reversal ──────────────
            # Cari semua invoice lines PRBJ yang punya partial reconcile
            # dengan lines LUAR invoice (= accrual BBN lines dari DSO),
            # lalu lepas via remove_move_reconcile() (standard Odoo API).
            for inv_line in invoice.line_ids.filtered(lambda l: l.reconciled):
                external_reconciled = (inv_line.matched_debit_ids + inv_line.matched_credit_ids).filtered(
                    lambda p: p.debit_move_id.move_id.id != invoice.id
                              or p.credit_move_id.move_id.id != invoice.id
                )
                if external_reconciled:
                    inv_line.remove_move_reconcile()
            # ── End unreconcile ─────────────────────────────────────────────


            move_reversal = self.env['account.move.reversal'].sudo().with_context(
                active_model='account.move', active_ids=invoice.ids
            ).create({
                'date': datetime.now(),
                'journal_id': journal_birojasa_billing_cancel_id,
            })
            reversal = move_reversal.sudo().reverse_moves()
            if reversal:
                self.move_id = reversal.get('res_id', False)

        
    def action_confirm(self):
        # if self.state == 'approved' and self.purchase_order_id:
        if self.birojasa_billing_id:    
            self._check_validity()
            self.invoice_cancel()
            self.birojasa_billing_id.action_cancel()
            self.move_id.sudo().action_post()
        return self.cancellation_id.action_confirm()
        

    def _check_duplicate_transaction(self,name):
        return self.cancellation_id._check_duplicate_transaction(name)
    
    def action_request_approval(self):
        return super().action_request_approval(value=self.birojasa_billing_id.amount_total)

    def _check_validity(self):
        for rec in self:
            rec.check_invoices()
            if not rec.birojasa_billing_id:
                raise Warning(_('Please select a Birojasa Billing to cancel.'))
            if rec.birojasa_billing_id.state != 'confirmed':
                raise Warning(_('Only Confirmed Birojasa Billing can be cancelled.'))
        return True
