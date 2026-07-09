# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError as Warning

class TwAccountPaymentPopeye(models.Model):
    _name = "tw.account.payment"
    _inherit = ['tw.account.payment', 'popeye.integration.mixin']

    # 7: Fields
    state = fields.Selection(
        selection_add=[
            ('wfp','Waiting For Payment'),
            ('in_process',)
        ], 
        ondelete={
            'wfp': 'set default',
        }
    )

    branch_code = fields.Char('Branch Code',related="company_id.code")

    # 10: Override Methods
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to trigger allocation check"""
        payment = super(TwAccountPaymentPopeye, self).create(vals_list)
        
        # Only check allocation if payment has lines
        if payment.line_dr_ids or payment.line_cr_ids:
            payment._check_allocation()
        
        return payment
    
    def write(self, vals):
        """Override write to trigger allocation check"""
        result = super(TwAccountPaymentPopeye, self).write(vals)
        
        # Only check allocation if not yet posted/paid and has lines
        for payment in self:
            if payment.state not in ['posted', 'paid']:
                if payment.line_dr_ids or payment.line_cr_ids:
                    payment._check_allocation()
        
        return result

    # 11: Private Methods
    def _popeye_prepare_payload(self):
        """Membangun payload JSON spesifik dan LENGKAP untuk Account Payment."""
        self.ensure_one()
        
        # Validations
        if not self.partner_bank_id:
            raise Warning('Silahkan isi Supplier Bank terlebih dahulu')
        if not self.partner_bank_id.acc_number:
            raise Warning(f"Account Number pada Bank {self.partner_bank_id.bank_id.name} kosong silahkan isi terlebih dahulu")
        if not self.partner_bank_id.acc_holder_name:
            raise Warning(f"Account Holder pada Bank {self.partner_bank_id.bank_id.name} kosong silahkan isi terlebih dahulu")
        
        if not self.journal_id.bank_id:
             raise Warning(f"Silahkan isi Bank Account terlebih dahulu di master journal {self.journal_id.name}")

        if not self.partner_id.company_type:
            raise Warning(f"Silahkan isi Tipe Supplier terlebih dahulu di Data Partner {self.partner_id.name}")

        if not self.name:
            raise Warning(f"Silahkan isi memo untuk send to popeye")
        
        if not self.schedule_date:
            raise Warning(f"Silahkan isi Schedule Date untuk send to popeye")

        details = []

        for line in self.line_dr_ids:
            details.append({
                "voucher_number": self.name,
                "voucher_date": self.date.strftime('%Y-%m-%d'),
                "vendor_invoice_number": line.move_line_id.move_id.name or self.name,
                "vendor_invoice_date": line.move_line_id.date.strftime('%Y-%m-%d'),
                "voucher_amount": line.amount,
            })

        for line in self.line_cr_ids:
            details.append({
                "voucher_number": self.name,
                "voucher_date": self.date.strftime('%Y-%m-%d'),
                "vendor_invoice_number": line.move_line_id.move_id.name or f"Credit Note {line.id}",
                "vendor_invoice_date": line.move_line_id.date.strftime('%Y-%m-%d'),
                "voucher_amount": line.amount * -1,
            })
        
        for line in self.line_wo_ids:
            details.append({
                "voucher_number": self.name + " - WriteOff",
                "voucher_date": self.date.strftime('%Y-%m-%d'),
                "vendor_invoice_number": "WriteOff - " + line.account_id.name,
                "vendor_invoice_date": self.date.strftime('%Y-%m-%d'),
                "voucher_amount": line.amount,
            })
        
        rounding = self.currency_id.rounding or 0.01
        if not float_is_zero(self.writeoff_amount, precision_rounding=rounding):
            # Asumsi akun pembulatan diambil dari konfigurasi
            account_rounding_id, _ = self._get_rounding_configuration()
            rounding_account = self.env['account.account'].browse(account_rounding_id)
            rounding_account_name = rounding_account.name if rounding_account else "Rounding Difference"
            details.append({
                "voucher_number": self.name + " - DifferenceAmount",
                "voucher_date": self.date.strftime('%Y-%m-%d'),
                "vendor_invoice_number": "Difference Amount - " + rounding_account_name,
                "vendor_invoice_date": self.date.strftime('%Y-%m-%d'),
                "voucher_amount": self.writeoff_amount,
            })

        vendor_account_type = self.partner_id.company_type.title() if self.partner_id.company_type else ''
        if vendor_account_type == 'Person':
            vendor_account_type = 'Perorangan'
        elif vendor_account_type == 'Company':
            vendor_account_type = 'Perusahaan'
        payload = {
            "company_code": '15',
            "branch_code": self.company_id.profit_centre,
            "transaction_no": self.name,
            "transaction_cheque_number": self.name,
            "transaction_date": self.date.strftime('%Y-%m-%d'),
            "transaction_currency": self.currency_id.name,
            "transaction_type": self.bulky_type,
            "transaction_due_date": self.due_date.strftime('%Y-%m-%d') if self.due_date else (self.schedule_date.strftime('%Y-%m-%d') if self.schedule_date else self.date.strftime('%Y-%m-%d')),
            "transaction_schedule_date": self.schedule_date.strftime('%Y-%m-%d') if self.schedule_date else '',
            "vendor_name": self.partner_id.name,
            "vendor_email": self.partner_id.email or '',
            "vendor_account_bank": self.partner_bank_id.bank_id.bic or '',
            "vendor_account_type":vendor_account_type,
            "vendor_account_resident": "WNI",
            "vendor_account_number": self.partner_bank_id.acc_number,
            "vendor_account_name": self.partner_bank_id.acc_holder_name,
            "transaction_amount": self.amount,
            "created_by": self.create_uid.name or '',
            "created_on": self.create_date.strftime('%Y-%m-%d %H:%M:%S'),
            "fund_account_bank": self.journal_id.bank_id.bic or '',
            "fund_account_number": self.journal_id.bank_acc_number,
            "transaction_remark": self.narration or self.name,
            "transaction_details": details
        }
        return payload

    def _popeye_post_payment(self):
        """Aksi yang dijalankan setelah Popeye mengonfirmasi 'Paid' status."""
        self.ensure_one()       
        if self.state not in ['posted', 'paid']:
            self.action_validate()
        return True
    
    def _get_payment_lines_for_allocation_check(self):
        """
        Override mixin abstract method.
        Returns dictionary of {move_line_id: amount} untuk validasi alokasi.
        """
        self.ensure_one()
        lines_to_check = {}
        
        # Aggregate debit lines
        for line in self.line_dr_ids:
            if line.move_line_id:
                move_line_id = line.move_line_id.id
                amount = line.amount
                lines_to_check[move_line_id] = lines_to_check.get(move_line_id, 0.0) + amount
        
        # Aggregate credit lines (if applicable)
        for line in self.line_cr_ids:
            if line.move_line_id:
                move_line_id = line.move_line_id.id
                amount = line.amount
                lines_to_check[move_line_id] = lines_to_check.get(move_line_id, 0.0) + amount
        
        return lines_to_check
    
    def _get_payment_line_table_name(self):
        """Returns the table name for tw.account.payment.line"""
        return 'tw_account_payment_line'
    
    def _get_payment_table_name(self):
        """Returns the table name for tw.account.payment"""
        return 'tw_account_payment'
    
