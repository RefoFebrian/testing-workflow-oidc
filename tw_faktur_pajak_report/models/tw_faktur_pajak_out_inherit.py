# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TwFakturPajakOutInherit(models.Model):
    """
    Inherit tw.faktur.pajak.out untuk menambahkan fungsionalitas print report.
    """
    _inherit = "tw.faktur.pajak.out"
    
    # Fields untuk print report
    transaction_code = fields.Char(string="Transaction Code")
    note = fields.Text(string="Note")
    
    def action_print_faktur_pajak(self):
        """
        Membuka wizard untuk print Faktur Pajak.
        Wizard akan meminta user mengisi signature_id dan keterangan.
        """
        self.ensure_one()
        
        # Validasi: Partner harus PKP
        if self.partner_id and hasattr(self.partner_id, 'pkp') and not self.partner_id.pkp:
            raise UserError(_("Customer is not PKP (Pengusaha Kena Pajak)!"))
        
        return {
            'name': _('Print Faktur Pajak'),
            'type': 'ir.actions.act_window',
            'res_model': 'tw.faktur.pajak.print.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_faktur_pajak_out_id': self.id,
                'default_signature_id': self.signature_id.id if self.signature_id else False,
                'default_transaction_code': self.transaction_code or '',
                'default_note': self.note or '',
            },
        }
    
    def get_faktur_pajak_name(self):
        """
        Mengembalikan nama faktur pajak berdasarkan tipe.
        """
        self.ensure_one()
        if self.is_combined_tax:
            return 'FAKTUR PAJAK GABUNGAN'
        return 'FAKTUR PAJAK'
    
    def get_remark_for_report(self):
        """
        Mengembalikan remark untuk report berdasarkan model transaksi.
        Jika model_id tidak ditemukan di master remark, return note atau empty string.
        """
        self.ensure_one()
        
        if not self.model_id:
            return self.note or ''
        
        # Cari remark di master
        remark_obj = self.env['tw.remark'].search([
            ('model_id', '=', self.model_id.id)
        ], limit=1)
        
        if not remark_obj:
            # Jika tidak ditemukan, return note atau empty string
            # Validasi sudah dilakukan di wizard sebelum print
            return self.note or ''
        
        # Untuk tw.account.payment, gunakan keterangan dari record
        if self.model_id.model == 'tw.account.payment':
            return self.note or remark_obj.remark
        
        remark_text = remark_obj.remark
        
        # Tambahkan invoice number jika ada (untuk work order dan sale order)
        if self.model_id.model == 'tw.work.order' and self.transaction_id:
            wo = self.env['tw.work.order'].browse(self.transaction_id)
            if wo.exists():
                # Cari invoice terkait
                invoices = self.env['account.move'].search([
                    ('invoice_origin', '=', wo.name),
                    ('amount_tax', '!=', 0)
                ], limit=1)
                if invoices:
                    remark_text += f' ( {invoices.name} )'
        
        elif self.model_id.model == 'tw.dealer.sale.order' and self.transaction_id:
            dso = self.env['tw.dealer.sale.order'].browse(self.transaction_id)
            if dso.exists():
                # Cari invoice terkait
                invoices = self.env['account.move'].search([
                    ('invoice_origin', '=', dso.name),
                    ('amount_tax', '!=', 0)
                ])
                for inv in invoices:
                    remark_text += f' ( {inv.name} )'
        
        return remark_text
    
    def action_update_print_count(self):
        """
        Update jumlah cetak dan state setelah print.
        """
        self.ensure_one()
        self.write({
            'printed_count': self.printed_count + 1,
            'state': 'print',
        })
