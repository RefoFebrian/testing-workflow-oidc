# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning


class TwFakturPajakPrintWizard(models.TransientModel):
    """
    Wizard untuk print Faktur Pajak.
    User harus mengisi signature dan bisa mengisi kode transaksi serta keterangan.
    """
    _name = "tw.faktur.pajak.print.wizard"
    _description = "Print Faktur Pajak Wizard"
    
    faktur_pajak_out_id = fields.Many2one(
        'tw.faktur.pajak.out',
        string='Faktur Pajak',
        required=True,
        readonly=True,
    )
    signature_id = fields.Many2one(
        'tw.signature',
        string='Signature By',
        required=True,
    )
    transaction_code = fields.Char(
        string='Kode Transaksi',
        help='Contoh: 010',
    )
    note = fields.Text(
        string='Keterangan',
    )
    
    def _validate_remark(self):
        """
        Validasi bahwa remark sudah ada di master untuk model transaksi.
        Raise UserError jika tidak ditemukan.
        """
        self.ensure_one()
        faktur = self.faktur_pajak_out_id
        
        if not faktur.model_id:
            return True
        
        # Cari remark di master
        remark_obj = self.env['tw.remark'].search([
            ('model_id', '=', faktur.model_id.id)
        ], limit=1)
        
        if not remark_obj:
            raise Warning(
                _("Model '%s' tidak ditemukan dalam form Remark.\n"
                  "Mohon isi data Remark terlebih dahulu di menu:\n"
                  "Pengaturan > Remark") % faktur.model_id.model
            )
        
        return True
    
    def action_print(self):
        """
        Update data pada faktur pajak out dan print report.
        """
        self.ensure_one()
        
        # Validasi remark sebelum print
        self._validate_remark()
        
        # Update faktur pajak out dengan data dari wizard
        self.faktur_pajak_out_id.write({
            'signature_id': self.signature_id.id,
            'transaction_code': self.transaction_code or '',
            'note': self.note or '',
        })
        
        # Update print count
        self.faktur_pajak_out_id.action_update_print_count()
        
        # Return report action
        return self.env.ref('tw_faktur_pajak_report.action_report_faktur_pajak').report_action(
            self.faktur_pajak_out_id
        )

