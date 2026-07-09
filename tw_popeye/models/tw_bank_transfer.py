# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TwBankTransferPopeye(models.Model):
    _name = "tw.bank.transfer"
    _inherit = ['tw.bank.transfer', 'popeye.integration.mixin']

    # Extend state selection to add 'wfp' (Waiting For Payment) after 'draft'
    state = fields.Selection(selection_add=[
        ('wfp', 'Waiting For Payment'),
        ('posted',),
    ], ondelete={'wfp': 'set default'})

    # Related field for view visibility conditions
    payment_method = fields.Char(related='payment_method_id.code', string='Payment Method Code')

    def _popeye_prepare_payload(self):
        """Builds the specific JSON payload for a Bank Transfer."""
        self.ensure_one()
        
        details = []
        first_line = self.line_ids and self.line_ids[0]
        if not first_line:
             raise UserError(_("Bank Transfer must have at least one detail line."))

        for line in self.line_ids:
            # Get vendor_invoice_date: confirm_date is Datetime, self.date is Date
            vendor_invoice_date = line.reimbursement_id.confirm_date
            if vendor_invoice_date:
                vendor_invoice_date = vendor_invoice_date.strftime('%Y-%m-%d')
            else:
                vendor_invoice_date = self.date.strftime('%Y-%m-%d')
            
            details.append({
                "voucher_number": self.name,
                "voucher_date": self.date.strftime('%Y-%m-%d'),
                "vendor_invoice_number": line.reimbursement_id.name or self.description,
                "vendor_invoice_date": vendor_invoice_date,
                "voucher_amount": line.amount,
            })

        # Determine vendor account type from partner (like Odoo 8: partner_obj.supplier_type)
        # In Odoo 18, use partner_id.company_type
        vendor_account_type = ''
        if self.partner_id and self.partner_id.company_type:
            vendor_account_type = self.partner_id.company_type.title()
            if vendor_account_type == 'Person':
                vendor_account_type = 'Perorangan'
            elif vendor_account_type == 'Company':
                vendor_account_type = 'Perusahaan'

        payload = {
            "company_code": '15',
            "branch_code": self.company_id.profit_centre,
            "transaction_no": self.name,
            "transaction_date": self.date.strftime('%Y-%m-%d'),
            "transaction_currency": "IDR",
            "transaction_type": self.bulky_type,
            "transaction_due_date": self.date.strftime('%Y-%m-%d'),
            "transaction_cheque_number": self.name,
            "transaction_schedule_date": self.date.strftime('%Y-%m-%d'),
            # Vendor info - using payment_to_id.bank_account_id (Odoo 18 equivalent of Odoo 8's payment_to_id.partner_bank_id)
            "vendor_account_type": vendor_account_type,
            "vendor_account_resident": "WNI",
            "vendor_name": self.partner_id.name if self.partner_id else '',
            "vendor_email": self.partner_id.email or '' if self.partner_id else '',
            "vendor_account_bank": first_line.payment_to_id.bank_account_id.bank_id.bic if first_line.payment_to_id and first_line.payment_to_id.bank_account_id and first_line.payment_to_id.bank_account_id.bank_id else '',
            "vendor_account_number": first_line.payment_to_id.bank_account_id.acc_number if first_line.payment_to_id and first_line.payment_to_id.bank_account_id else '',
            "vendor_account_name": first_line.payment_to_id.bank_account_id.acc_holder_name if first_line.payment_to_id and first_line.payment_to_id.bank_account_id else '',
            "transaction_amount": self.amount,
            "created_by": self.create_uid.name or '',
            "created_on": self.create_date.strftime('%Y-%m-%d %H:%M:%S'),
            # Fund account - using journal_id fields directly like tw_account_payment
            "fund_account_bank": self.journal_id.bank_id.bic if self.journal_id and self.journal_id.bank_id else '',
            "fund_account_number": self.journal_id.bank_acc_number or '',
            "transaction_remark": self.description or self.name,
            "transaction_details": details
        }
        return payload

    def _popeye_post_payment(self):
        """Final action to run after Popeye confirms 'Paid' status."""
        self.ensure_one()
        if self.state != 'posted':
            self.action_confirm()
        return True

    def _get_payment_lines_for_allocation_check(self):
        """
        Override mixin abstract method.
        Bank Transfer does not allocate to invoices, so return empty dict.
        """
        self.ensure_one()
        return {}

    def _get_payment_line_table_name(self):
        """Returns the table name for tw.bank.transfer.line"""
        return 'tw_bank_transfer_line'

    def _get_payment_table_name(self):
        """Returns the table name for tw.bank.transfer"""
        return 'tw_bank_transfer'