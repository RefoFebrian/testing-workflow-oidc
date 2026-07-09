# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwAccountPaymentLineVoucher(models.Model):
    _inherit = "tw.account.payment.line"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    def _warning_response(self, title, message):
        """Helper method untuk membuat response warning dengan reset move_line_id."""
        return {
            'warning': {'title': title, 'message': message},
            'value': {'move_line_id': False}
        }

    @api.onchange('move_line_id')
    def onchange_move_line_id(self):
        move_line = self.move_line_id
        if move_line.journal_id.code != 'HV':
            return super().onchange_move_line_id()

        # Validasi customer hanya punya 1 WO yang belum selesai
        partner = move_line.move_id.partner_id
        work_orders = self.env['tw.work.order'].suspend_security().search([
            ('company_id', '=', self.company_id.id),
            ('customer_stnk_id', '=', partner.id),
            ('state', 'not in', ['done', 'cancel', 'unused']),
        ])
        if not work_orders:
            return self._warning_response(
                'Kesalahan Validasi',
                f'Customer {partner.name} tidak memiliki WO yang sedang berjalan'
            )
            
        if len(work_orders) > 1:
            return self._warning_response(
                'Kesalahan Validasi',
                f'Customer {partner.name} memiliki lebih dari satu WO yang sedang berjalan'
            )

        # Validasi OTP jika ada WO
        if work_orders and work_orders.otp_code != work_orders.otp_validation:
            return self._warning_response(
                'Kode OTP tidak valid',
                f'Silahkan cek kembali WO {work_orders.name}, pastikan sudah confirm voucher dan memasukkan OTP dengan benar!'
            )

        return super().onchange_move_line_id()

    # 12: override methods

    # 13: private methods
