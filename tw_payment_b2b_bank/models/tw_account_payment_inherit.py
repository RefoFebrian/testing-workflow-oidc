# 1: imports of python lib
from datetime import datetime
import random

# 2: import of known third party lib
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _, SUPERUSER_ID

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class AccountPaymentInherit(models.Model):
    _inherit = "tw.account.payment"

    # 7: defaults methods

    # 8: fields
    va_no = fields.Char(string='Virtual Account No', related='payment_transaction_id.va_no')
    qris_qr_image = fields.Binary(string='QR Code', compute='_compute_qris_image')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('payment_transaction_id')
    def _compute_qris_image(self):
        for rec in self:
            if rec.payment_transaction_id:
                image_file = self.env['tw.config.files'].suspend_security().with_context(name='QR').get_file(rec.payment_transaction_id.qr_filename)
                rec.qris_qr_image = image_file
            else: 
                rec.qris_qr_image = False

    # 12: override methods

    # 13: action methods
    def action_generate_api_payment_qris(self):
        self.generate_api_payment_trx()

    def action_inquiry_api_payment_qris(self):
        self.inquiry_api_payment_trx()

    def action_generate_api_payment_va(self):
        self.generate_api_payment_trx()

    def action_inquiry_api_payment_va(self):
        self.inquiry_api_payment_trx()

    def action_auto_post_api_payment(self):
        self.suspend_security().with_company(self.company_id).with_user(SUPERUSER_ID).action_post()

    def generate_api_payment_trx(self):
        """ Generate API Payment (QRIS or Virtual Account) """
        self.ensure_one()

        if not self.payment_method_line_id:
            raise Warning('Payment Method belum ada!')
        
        provider_obj = self.payment_method_line_id.payment_provider_id
        if not provider_obj:
            raise Warning('Payment Provider belum ada!')
        
        if self.payment_method == 'virtual_account':
            payment_usage = 'va'
        else:
            payment_usage = self.payment_method
        
        api_payment_config_obj = self._get_api_payment_config(provider_obj)
        setting_api_payment_config_obj = provider_obj.api_payment_setting_ids.filtered(lambda sap: sap.payment_usage == payment_usage and sap.division == self.division and sap.provider_id == api_payment_config_obj.partner_id)
        if not setting_api_payment_config_obj:
            raise Warning(f'Master API Payment Settings untuk Provider {provider_obj.name} belum ada!')
        
        # * create payment transaction obj
        payment_transaction_obj = self.suspend_security()._create_api_payment_trx(provider_obj=provider_obj, setting_api_payment_config_obj=setting_api_payment_config_obj)
        if not payment_transaction_obj:
            raise Warning('Gagal create Payment Transaction!')
        
        # * update payment_transaction_id to account payment
        self.payment_transaction_id = payment_transaction_obj.id
        
        if self.payment_method == 'qris':
            # * process generate QR
            try:
                qris_obj = payment_transaction_obj.suspend_security().generate_api_payment_qris(setting_api_payment_config_obj, api_payment_config_obj)
            except Exception as err:
                raise Warning(err)
            
            # * update image QR
            try:
                result = payment_transaction_obj.suspend_security().set_api_payment_qris_image(qris_obj, api_payment_config_obj)
            except Exception as err:
                raise Warning(err)

        elif self.payment_method == 'virtual_account':
            # TODO: send whatsapp to customer for virtual account transaction
            self.suspend_security()._send_wa_notif_api_payment_trx_virtual_account()
        
        return True
    
    def inquiry_api_payment_trx(self):
        """ Inquiry API Payment (QRIS or Virtual Account) """
        self.ensure_one()

        provider_obj = self.payment_method_line_id.payment_provider_id
        if not provider_obj:
            raise Warning('Payment Provider belum ada!')

        if not self.payment_transaction_id:
            raise Warning('Payment Transaction belum ada, lakukan generate dahulu!')
        
        payment_method = self.payment_method.replace('_', ' ').upper() if '_' in self.payment_method else self.payment_method.upper()
        if self.payment_transaction_id.state == 'done':
            raise Warning(f'Transaksi payment {self.name} sudah dibayarkan menggunakan {payment_method}!')
        
        if self.payment_method == 'virtual_account':
            payment_usage = 'va'
        else:
            payment_usage = self.payment_method
        
        api_payment_config_obj = self._get_api_payment_config(provider_obj)
        setting_api_payment_config_obj = provider_obj.api_payment_setting_ids.filtered(lambda sap: sap.payment_usage == payment_usage and sap.division == self.division and sap.provider_id == api_payment_config_obj.partner_id)
        if not setting_api_payment_config_obj:
            raise Warning(f'Master API Payment Settings untuk Provider {provider_obj.name} belum ada!')
        
        if self.payment_method == 'qris':
            # # * process inquiry QR
            try:
                qris_obj = self.payment_transaction_id.suspend_security().inquiry_api_payment_qris(setting_api_payment_config_obj, api_payment_config_obj)
            except Exception as err:
                raise Warning(err)
            
            # * consume inquiry QR results
            try:
                result = self.payment_transaction_id.suspend_security().consume_inquiry_api_payment_qris_response(qris_obj, api_payment_config_obj)
            except Exception as err:
                raise Warning(err)

        elif self.payment_method == 'virtual_account':
            # # * process inquiry VA
            try:
                va_obj = self.payment_transaction_id.suspend_security().inquiry_api_payment_va(setting_api_payment_config_obj, api_payment_config_obj)
            except Exception as err:
                raise Warning(err)
            
            # * consume inquiry VA results
            try:
                result = self.payment_transaction_id.suspend_security().consume_inquiry_api_payment_va_response(va_obj, api_payment_config_obj)
            except Exception as err:
                raise Warning(err)
            
            if self.state != 'paid' and self.payment_transaction_id.state == 'done':
                self.action_auto_post_api_payment()
        
        return True

    # 14: private methods
    def _get_api_payment_config(self, provider_obj):
        """ Get Master of API Payment Configuration """
        config_obj = self.env['tw.api.configuration'].sudo()._get_config_bank_by_name(provider_obj.code, is_api_payment=True, company_obj=self.company_id)
        
        return config_obj
    
    def _create_api_payment_trx(self, provider_obj=None, setting_api_payment_config_obj=None):
        if not provider_obj:
            provider_obj = self.payment_method_line_id.payment_provider_id

        # Get or create QRIS payment method
        payment_method_obj = self.env['payment.method'].sudo().search([
            ('code','=',self.payment_method_id.code),
            ('provider_ids','in',provider_obj.id),
        ], limit=1)
        if not payment_method_obj:
            payment_method_obj = self.env['payment.method'].create({
                'name': self.payment_method_id.name,
                'code': self.payment_method_id.code,
                'provider_ids': [(6, 0, [provider_obj.id])],
                'active': True,
                'support_tokenization': False,
                'support_express_checkout': False,
            })
        
        # Prepare transaction values
        now = fields.Datetime.now() + relativedelta(hours=7)
        name = self.name if (self.name and self.name != '/') else f'PAY-{self.id}'
        note = self.payment_method_id.name + f' [{provider_obj.name}]' + ' of ' + self.partner_id.name
        note += ' ' + name + ' ' + now.strftime('%Y-%m-%d')
        note += ' ' + now.strftime('%H:%M')
        trx_keys = self.company_id.code + name.replace('/', '').replace('-', '')
        random_keys = f'{random.randint(10000, 99999)}'
        is_use_random_keys_partner_ref_param = self.env['ir.config_parameter'].sudo().get_param('tw_payment_b2b_bank.is_use_random_keys_partner_ref')
        if is_use_random_keys_partner_ref_param:
            is_use_random_keys_partner_ref = eval(is_use_random_keys_partner_ref_param)
        else:
            is_use_random_keys_partner_ref = False
        
        transaction_keys = trx_keys
        if is_use_random_keys_partner_ref:
            transaction_keys = trx_keys + random_keys

        tx_values = {
            'company_id': self.company_id.id,
            'provider_id': provider_obj.id,
            'payment_method_id': payment_method_obj.id,
            'transaction_keys': transaction_keys,
            'amount': self.amount,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'reference': name,
            # Name di note adalah nomor yang dikirim ke xendit
            'note': note,
            'state': 'draft',
            'payment_method_code': self.payment_method_id.name,
        }
        if self.payment_method == 'virtual_account':
            mobile = self.partner_id.mobile
            if not mobile:
                raise Warning(f'No HP konsumen kosong, mohon dilengkapi dahulu!')
            if not setting_api_payment_config_obj.x_partner_id:
                raise Warning(f'Data X Partner ID kosong pada Master API Payment Settings, mohon dilengkapi dahulu!')
            custom_mobile = mobile.replace('+62', '0').replace('-', '').replace(' ', '').strip()
            x_partner_id = setting_api_payment_config_obj.x_partner_id
            trx_keys = custom_mobile + ''.join(self.name.split('/')[4:])
            tx_values.update({
                'transaction_keys': trx_keys,
                'va_no': x_partner_id + trx_keys
            })

        # Add partner details for Xendit
        if self.partner_id.email:
            tx_values['partner_email'] = self.partner_id.email
        if self.partner_id.phone or self.partner_id.mobile:
            tx_values['partner_phone'] = self.partner_id.phone or self.partner_id.mobile
        if self.partner_id.city:
            tx_values['partner_city'] = self.partner_id.city
        if self.partner_id.country_id:
            tx_values['partner_country_id'] = self.partner_id.country_id.id
        if self.partner_id.zip:
            tx_values['partner_zip'] = self.partner_id.zip
        if self.partner_id.state_id:
            tx_values['partner_state_id'] = self.partner_id.state_id.id
        if self.partner_id.street:
            tx_values['partner_address'] = self.partner_id.street

        add_context = {'params': {
            'id': self.id,
            'model': self._name,
        }}

        # Create payment transaction
        try:
            transaction_obj = self.env['payment.transaction'].suspend_security().with_company(self.company_id).with_context(**add_context).create(tx_values)
        except Exception as err:
            self._cr.rollback()
            raise Warning(f'Gagal create Payment Transaction, error: {err}')

        return transaction_obj
    
    def _send_wa_notif_api_payment_trx_virtual_account(self):
        return False