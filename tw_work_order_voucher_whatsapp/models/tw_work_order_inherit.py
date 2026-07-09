# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from random import randint

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrderVoucherWhatsapp(models.Model):
    _inherit = "tw.work.order"

    # 7: defaults methods

    # 8: fields
    otp_code = fields.Char(string='Kode OTP', size=4)
    otp_validation = fields.Char(string='Validation OTP', size=4)
    is_voucher = fields.Boolean(string="Voucher Used", default=False)

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('otp_validation')
    def _onchange_otp_validation(self):
        if self.otp_validation and not self.otp_validation.isdigit():
            return {
                'warning': {
                    'title': 'Kesalahan Validasi',
                    'message': 'Kode OTP harus berupa angka'
                },
                'value': {'otp_validation': False}
            }
        if self.otp_validation and len(str(self.otp_validation)) != 4:
            return {
                'warning': {
                    'title': 'Kesalahan Validasi',
                    'message': 'Kode OTP harus 4 digit'
                },
                'value': {'otp_validation': False}
            }

    # 12: override methods

    # 13: action methods
    def action_request_approval(self):
        rfa = super().action_request_approval()
        if self.sales_voucher_ids:
            self._send_otp_voucher()
        
        return rfa

    def action_confirm_otp_voucher(self):
        """Confirm OTP voucher validation.

        Uses return notification instead of raise to prevent
        otp_validation from persisting in the database on error.
        (raise causes transaction rollback, undoing the field reset)
        """
        self.ensure_one()
        try:
            if not self.sales_voucher_ids:
                self.suspend_security().write({'otp_validation': False})
                return self._otp_error_notification(f'Voucher tidak ditemukan pada Serial number {self.lot_id.name}')

            if not self.otp_validation:
                return self._otp_error_notification('Harap isi Kode OTP dengan benar!')

            if self.otp_validation != self.otp_code:
                self.suspend_security().write({'otp_validation': False})
                return self._otp_error_notification('Kode OTP Salah! Silahkan klik send otp untuk mengirim ulang kode OTP')

            message_obj = self._get_whatsapp_message()
            if not message_obj:
                self.suspend_security().write({'otp_validation': False})
                return self._otp_error_notification(
                    f"Whatsapp Outbox customer {self.customer_stnk_id.name} "
                    f"pada Work Order {self.name} tidak ditemukan,\n"
                    f"Silahkan klik send otp untuk mengirim ulang kode OTP"
                )

            if message_obj.expired_date < datetime.now():
                self.suspend_security().write({'otp_validation': False})
                return self._otp_error_notification(
                    f"Kode OTP untuk customer {self.customer_stnk_id.name} "
                    f"pada Work Order {self.name} sudah EXPIRED,\n"
                    f"Silahkan klik send otp untuk mengirim ulang kode OTP"
                )
            self.suspend_security().write({'is_voucher': True})

        except Exception as e:
            self.suspend_security().write({'otp_validation': False})
            return self._otp_error_notification(str(e))

    def action_send_otp_voucher(self):
        self.ensure_one()
        message_obj = self._get_whatsapp_message()
        if message_obj.expired_date < datetime.now():
            self._send_otp_voucher()
        else:
            if message_obj.state == 'failed':
                message_obj.action_send()
            else:
                raise Warning(f"Kode OTP masih aktif untuk customer {self.customer_stnk_id.name} pada Work Order {self.name},\nSilahkan tunggu hingga kode OTP EXPIRED")

    def action_view_confirm_voucher(self):
        self.ensure_one()
        form_id = self.env.ref('tw_work_order_voucher_whatsapp.tw_work_order_confirm_voucher_view').id
        return {
            'name': 'Confirm Voucher',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.work.order',
            'views': [(form_id, 'form')],
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    # 14: private methods
    def _otp_error_notification(self, message):
        """Return a danger notification action for OTP validation errors.

        Uses display_notification instead of raise to avoid transaction
        rollback, allowing field reset writes to persist.
        """
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Kesalahan Validasi',
                'message': message,
                'type': 'danger',
                'sticky': True,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def _send_otp_voucher(self):
        """Generate and send OTP voucher via WhatsApp message."""
        self.ensure_one()
        
        # Search template with cached model reference
        template = self.env['tw.whatsapp.content.template'].suspend_security().search([
            ('name', '=', 'Work Order Voucher OTP'),
            ('template_type_id.value', '=', 'work_order_voucher_otp')
        ], limit=1)
        if not template:
            raise Warning("Template OTP Voucher tidak ditemukan.")

        # Generate 4-digit OTP code efficiently
        otp_code = ''.join(str(randint(0, 9)) for __ in range(4))
        
        # Prepare message content with chained replacement
        message = template.content.replace('[wo_number]', self.name).replace('[otp_code]', otp_code)
        
        # Cache suspend_security model and prepare message data
        whatsapp_model = self.env['tw.whatsapp.message'].suspend_security()
        message_data = whatsapp_model._prepare_create_whatsapp_message([{
            'name': self.customer_stnk_id.name,
            'origin': self.name,
            'company_id': self.company_id.id,
            'phone_number': self.customer_stnk_id.mobile,
            'template_id': template.id,
            'message': message,
            'message_type': 'outbox',
            'otp_code': otp_code,
            'expired_date': datetime.now() + relativedelta(minutes=60),
        }])
        message_obj = whatsapp_model.create(message_data)
        message_obj.action_send()

        self.suspend_security().write({'otp_code': otp_code})

    def _get_whatsapp_message(self):
        self.ensure_one()
        message_obj = self.env['tw.whatsapp.message'].suspend_security().search([
            ('name', '=', self.customer_stnk_id.name),
            ('origin', '=', self.name),
            ('otp_code', '=', self.otp_code)
        ], limit=1)
        if message_obj:
            return message_obj

        return False