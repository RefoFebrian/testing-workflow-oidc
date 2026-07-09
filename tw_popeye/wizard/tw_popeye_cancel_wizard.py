# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning


class TwPopeyeCancelWizard(models.TransientModel):
    """
    Wizard untuk input alasan cancel transaksi Popeye.
    Digunakan oleh tw.account.payment dan tw.bank.transfer.
    """
    _name = "tw.popeye.cancel.wizard"
    _description = "Wizard to Cancel Popeye Transaction"

    cancel_reason = fields.Text(
        string='Alasan Cancel',
        required=True,
        help='Masukkan alasan pembatalan transaksi Popeye'
    )

    def action_confirm_cancel(self):
        """
        Konfirmasi cancel dan panggil action_cancel_popeye pada record target.
        """
        self.ensure_one()

        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')

        if not active_model or not active_id:
            raise Warning(_('Context tidak valid. Silakan coba lagi.'))

        record = self.env[active_model].browse(active_id)

        if not record.exists():
            raise Warning(_('Record tidak ditemukan.'))

        # Call action_cancel_popeye pada record target
        record.action_cancel_popeye(self.cancel_reason)

        return {'type': 'ir.actions.act_window_close'}
