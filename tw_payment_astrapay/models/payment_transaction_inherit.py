# 1: imports of python lib
import json
import random
import requests
import hashlib
import hmac
import base64
import io
import qrcode
from datetime import datetime

# 2: import of known third party lib
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class PaymentTransactionInherit(models.Model):
    _inherit = "payment.transaction"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _get_payload_api_payment_qris(self, setting_api_payment_config_obj, api_payment_config_obj, process_type):
        payload = super()._get_payload_api_payment_qris(setting_api_payment_config_obj, api_payment_config_obj, process_type)
        if api_payment_config_obj:
            if api_payment_config_obj.api_type_value.upper() == 'ASTRAPAY' and api_payment_config_obj.is_api_payment:
                vals = {
                    'partnerReferenceNo': self.transaction_keys,
                    'amount': {
                        'value': '%.2f' % float(self.amount),
                        'currency': 'IDR' # set default for indonesian Currency
                    },
                    'merchantId': setting_api_payment_config_obj.merchant_id,
                    'terminalId': setting_api_payment_config_obj.terminal_id,
                    'additionalInfo': {
                        'tip': '0.00'
                    }
                }
                
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                validity_period = self.env['ir.config_parameter'].sudo().get_param('tw_payment_astrapay.validity_period')
                if validity_period and eval(validity_period) <= 24:
                    validityPeriod = (datetime.strptime(now, '%Y-%m-%d %H:%M:%S') + relativedelta(hours=7+int(validity_period))).isoformat()
                    vals.update({'validityPeriod': validityPeriod})

                if process_type == 'inquiry':
                    del vals['partnerReferenceNo']
                    del vals['amount']
                    del vals['terminalId']
                    if vals.get('validityPeriod'):
                        del vals['validityPeriod']
                    vals.update({
                        'originalReferenceNo': self.reference_number,
                        'serviceCode': setting_api_payment_config_obj.service_code,
                        'additionalInfo': {
                            'terminalId': setting_api_payment_config_obj.terminal_id
                        },
                        'originalPartnerReferenceNo': self.transaction_id
                    })

                if payload:
                    payload.update(vals)
                else:
                    payload = vals

        return payload
    
    def _generate_signature_headers(self, config_obj, str_to_sign):
        signature = super()._generate_signature_headers(config_obj, str_to_sign)
        if config_obj:
            if config_obj.api_type_value.upper() == 'ASTRAPAY' and config_obj.is_api_payment:
                signature = hmac.new(str(config_obj.client_secret).encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha512).digest()
                signature = base64.b64encode(signature).decode('utf-8')

        return signature
    
    def _get_log_name_generate_api_payment_qris(self, api_payment_config_obj):
        log_name = super()._get_log_name_generate_api_payment_qris(api_payment_config_obj)
        if api_payment_config_obj:
            if api_payment_config_obj.api_type_value.upper() == 'ASTRAPAY' and api_payment_config_obj.is_api_payment:
                log_name = 'Generate QRIS Payment AstraPay'

        return log_name
    
    def _get_log_name_inquiry_api_payment_qris(self, api_payment_config_obj):
        log_name = super()._get_log_name_inquiry_api_payment_qris(api_payment_config_obj)
        if api_payment_config_obj:
            if api_payment_config_obj.api_type_value.upper() == 'ASTRAPAY' and api_payment_config_obj.is_api_payment:
                log_name = 'Inquiry QRIS Payment ASTRAPAY'

        return log_name
    
    def _prepare_api_payment_qris_image_response(self, qris_obj, api_payment_config_obj):
        response = super()._prepare_api_payment_qris_image_response(qris_obj, api_payment_config_obj)
        if api_payment_config_obj:
            if api_payment_config_obj.api_type_value.upper() == 'ASTRAPAY' and api_payment_config_obj.is_api_payment:
                if not response:
                    response = qris_obj
                image = qrcode.make(response.get('qrContent'))
                
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                
                b64_image = base64.b64encode(buffer.getvalue())
                response['b64_image'] = b64_image

        return response
    
    def _process_inquiry_api_payment_qris_response_content(self, response_content, api_payment_config_obj):
        values = {}
        response = super()._process_inquiry_api_payment_qris_response_content(response_content, api_payment_config_obj)
        if response:
            values = response
        else:
            if api_payment_config_obj:
                if api_payment_config_obj.api_type_value.upper() == 'ASTRAPAY' and api_payment_config_obj.is_api_payment:
                    if not response:
                        response = response_content
                    values = super()._prepare_inquiry_response_values(response_content, values)

                    # draft --> Draft
                    # pending --> Pending
                    # authorized --> Authorized
                    # done --> Done
                    # cancel --> Cancel
                    # error --> Error

                    # STATE_MAPPING = {
                    #     'success': 'unpaid',
                    #     'initiated': 'draft',
                    #     'paying': 'paid',
                    #     'pending': 'unpaid',
                    #     'refunded': 'declined',
                    #     'canceled': 'declined',
                    #     'failed': 'invalid',
                    #     'not found': 'invalid',
                    #     'Successfully': 'paid'
                    # }
                    if values.get('state') == 'declined':
                        values['state'] = 'cancel'
                    elif values.get('state') == 'invalid':
                        values['state'] = 'error'
                    elif values.get('state') == 'unpaid':
                        values['state'] = 'pending'
                    elif values.get('state') == 'paid':
                        values['state'] = 'done'
                    elif not values.get('state'):
                        values['state'] = 'error'
                    
                    if 'additionalInfo' in response_content:
                        additional_info = response_content.get('additionalInfo')
                        add_info = 'tip: {tip}\ncustomerPan: {customerPan}\ncustomerReferenceNumber: {customerReferenceNumber}\nissuerName: {issuerName}\nbatchNo: {batchNo}\nmerchantId: {merchantId}\nuserName: {userName}\nmerchantPan: {merchantPan}\nphoneNumber: {phoneNumber}\ntransactionId: {transactionId}\ngracePeriod: {gracePeriod}'.format(
                            tip=additional_info.get('tip', '0.00'),
                            customerPan=additional_info.get('customerPan', ''),
                            customerReferenceNumber=additional_info.get('customerReferenceNumber', ''),
                            issuerName=additional_info.get('issuerName', ''),
                            batchNo=additional_info.get('batchNo', ''),
                            merchantId=additional_info.get('merchantId', ''),
                            userName=additional_info.get('userName', ''),
                            merchantPan=additional_info.get('merchantPan', ''),
                            phoneNumber=additional_info.get('phoneNumber', ''),
                            transactionId=additional_info.get('transactionId', ''),
                            gracePeriod=str(additional_info.get('gracePeriod')) if additional_info.get('gracePeriod') else '0'
                        )
                        values.update({'additional_info': add_info})

        return values