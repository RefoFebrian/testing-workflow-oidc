# 1: imports of python lib
import json
import random
import hashlib
import requests
from datetime import datetime

# 2: import of known third party lib
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.addons.tw_payment_b2b_bank.helpers import STATE_MAPPING, STATE_CODE_MAPPING

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


MANDATORY_DESCRIPTION = """
    This data must be informed on the proof of
    the transaction provided to the customer
"""

TRASACTION_STATUS = {
    'FAILED': '0',
    'SUCCESS': '1',
    'PENDING': '2'
}

STATE_HELP = """
    Equivalent TEDS state and API transaction state:
    - invalid (Invalid): Transaction state could be
        (NOT FOUND, MID / TID NOT REGISTERED, INVALID LENGTH)
        Or transaction model is not found or unmatched
    - unpaid (Unpaid): Transaction state could be UNPAID or TIMEOUT
    - declined (Declined):
        Transaction state could be
        DECLINED or CAN NOT BE PROCESSED
    - paid (Paid): Transaction state should be SUCCESS
"""

class PaymentTransactionInherit(models.Model):
    _inherit = "payment.transaction"

    # 7: defaults methods

    # 8: fields
    transaction_id = fields.Char(string='Transaction ID', size=36, help='Transaction identity, response from API Generate QR')
    currency_code = fields.Char(string='Currency Code', size=3, help='Transaction currency code')
    approval_code = fields.Char(string='Approval Code', size=6, help='Approval code from host for success transaction')
    batch_number = fields.Char(string='Batch Number', size=3, help='Transaction batch number recorded in QRIS Server')
    issuer_reference_number = fields.Char(string='RRN', size=12, help=MANDATORY_DESCRIPTION)
    customer_pan = fields.Char(string='Buyer card number', size=19, help=MANDATORY_DESCRIPTION)
    issuer_name = fields.Char(string='Issuer Name', help=MANDATORY_DESCRIPTION)
    acquirer_name = fields.Char(string='Acquirer Name', help=MANDATORY_DESCRIPTION)
    payer_name = fields.Char(string='Payer Name', help=MANDATORY_DESCRIPTION)
    payer_phone_number = fields.Char(string='Payer Phone Number')
    terminal_id = fields.Char(string='Terminal ID')
    transaction_keys = fields.Char(string='Transaction Keys', help='Unique identifier for each transaction generated from the TDM (unique for each transaction)')
    reference_number = fields.Char(string='Reference No', size=36)
    va_no = fields.Char(string='Virtual Account No', size=36, help='Virtual Account No, generate by Co Partner')
    detail_info = fields.Char(string='Detail Info')
    additional_info = fields.Text(string='Additional Info')
    reason = fields.Text(string='Reason')
    convenience_fee = fields.Float(string='Convenience Fee', help=MANDATORY_DESCRIPTION)
    transaction_date = fields.Datetime(string='Transaction Date')

    transaction_status = fields.Selection([
        ('0', 'FAILED'),
        ('1', 'SUCCESS'),
        ('2', 'PENDING')
    ], string='Transaction Status')

    qr_file = fields.Binary(string='File', compute='_compute_qris_image')
    qr_filename = fields.Char(string='Filename')

    # 9: relation fields
    customer_id = fields.Many2one(comodel_name='res.partner', string='Customers', domain=[('category_id.name','=','Customer')])
    merchant_id = fields.Many2one(comodel_name='res.partner', string='Merchant')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('qr_filename')
    def _compute_qris_image(self):
        for rec in self:
            if rec.qr_filename:
                image_file = self.env['tw.config.files'].suspend_security().with_context(name='QR').get_file(rec.qr_filename)
                rec.qr_file = image_file
            else:
                rec.qr_file = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('qr_file'):
                config_file_model = self.env['tw.config.files']
                file_name = vals.get('reference').replace('/', '-')
                model_name = self._context.get('params').get('model') if self._context.get('params') else 'tw.account.payment'
                filename = f'{file_name}_{model_name}.jpg'
                config_file_model.suspend_security().with_context(name='QR').upload_file(filename, vals['qr_file'])
                vals['qr_file'] = False
                vals['qr_filename'] = filename

        create = super(PaymentTransactionInherit, self).create(vals_list)

        if create.company_id != vals.get('company_id'):
            create.company_id = vals.get('company_id')

        return create
    
    def write(self, vals):
        if vals.get('qr_file'):
            config_file_model = self.env['tw.config.files']
            file_name = self.reference.replace('/', '-')
            model_name = self._context.get('params').get('model') if self._context.get('params') else 'tw.account.payment'
            filename = f'{file_name}_{model_name}.jpg'
            config_file_model.suspend_security().with_context(name='QR').upload_file(filename, vals.get('qr_file'))
            vals['qr_file'] = False
            vals['qr_filename'] = filename
            
        write = super(PaymentTransactionInherit, self).write(vals)
        
        return write

    # 13: action methods
    def generate_api_payment_qris(self, setting_api_payment_config_obj, api_payment_config_obj):
        # * get url api payment qris object
        url_obj = self.env['tw.api.url'].sudo()._get_api_url_by_type(api_payment_config_obj, 'generate_qris', is_relative=False, is_get_object=True)
        
        # * get headers and payload
        headers, payload = self.suspend_security()._prepare_headers_payload_api_payment_qris(url_obj, setting_api_payment_config_obj, api_payment_config_obj)

        log_name = self._get_log_name_generate_api_payment_qris(api_payment_config_obj)
        if not log_name:
            raise Warning('Log name Generate API Payment QRIS tidak ada!')
        
        # * process generate QR
        request_type = 'post'
        method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
        model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)
        url = api_payment_config_obj.base_url + url_obj.url
        try:
            response = requests.post(url=url, headers=headers, data=payload)
        except requests.exceptions.RequestException as err:
            _logger.error(err)

            # * Create Failed Log
            response_code = response.status_code
            params = {
                'name': log_name,
                'url': url,
                'description': log_name,
                'ip_address': '',
                'response': json.loads(response.content),
                'payload': json.loads(payload),
                'headers': headers,
                'response_code': response_code,
                'status_code': response_code,
                'reference': '',
                'transaction_id': None,
                'api_type_id': api_payment_config_obj.api_type_id.id,
                'method_id': method_obj.id if method_obj else False,
                'model_id': model_obj.id if model_obj else False
            }
            api_payment_config_obj._create_api_log_bank(params)
            # self._cr.commit()
            self._cr.rollback()
            raise Warning(f"""
                Gagal terhubung dengan {url}
                Detail: {err.args}
            """)
        
        status_code = response.status_code
        content = json.loads(response.content)
        if status_code not in (200, 201):
            # * Create Failed Log
            response_code = response.status_code
            params = {
                'name': log_name,
                'url': url,
                'description': log_name,
                'ip_address': '',
                'response': content,
                'payload': json.loads(payload),
                'headers': headers,
                'response_code': response_code,
                'status_code': response_code,
                'reference': '',
                'transaction_id': None,
                'api_type_id': api_payment_config_obj.api_type_id.id,
                'method_id': method_obj.id if method_obj else False,
                'model_id': model_obj.id if model_obj else False
            }
            api_payment_config_obj._create_api_log_bank(params)
            self._cr.commit()
            warning_message = ''
            for key, value in content.items():
                warning_message += f'{key} : {value}\n'

            raise Warning(warning_message)

        # * Create Success Log
        response_code = response.status_code
        params = {
            'name': log_name,
            'url': url,
            'description': log_name,
            'ip_address': '',
            'response': content,
            'payload': json.loads(payload),
            'headers': headers,
            'response_code': response_code,
            'status_code': response_code,
            'reference': '',
            'transaction_id': None,
            'api_type_id': api_payment_config_obj.api_type_id.id,
            'method_id': method_obj.id if method_obj else False,
            'model_id': model_obj.id if model_obj else False
        }
        api_payment_config_obj._create_api_log_bank(params)

        return json.loads(response.content)
    
    def set_api_payment_qris_image(self, qris_obj, api_payment_config_obj):
        response = self._prepare_api_payment_qris_image_response(qris_obj, api_payment_config_obj)
        if not response:
            raise Warning('Image Response QRIS tidak ada!')
        
        new_response = {}
        new_response['qr_file'] = response.get('b64_image')
        new_response['transaction_id'] = response.get('partnerReferenceNo')
        new_response['reference_number'] = response.get('referenceNo')
        
        # * update response to api payment object
        self.suspend_security().write(new_response)

        return True
    
    def inquiry_api_payment_qris(self, setting_api_payment_config_obj, api_payment_config_obj):
        # * get url api payment qris object
        url_obj = self.env['tw.api.url'].sudo()._get_api_url_by_type(api_payment_config_obj, 'inquiry_payment_qris', is_relative=False, is_get_object=True)
        
        # * get headers and payload
        headers, payload = self.suspend_security()._prepare_headers_payload_api_payment_qris(url_obj, setting_api_payment_config_obj, api_payment_config_obj, process_type='inquiry')
        
        log_name = self._get_log_name_inquiry_api_payment_qris(api_payment_config_obj)
        if not log_name:
            raise Warning('Log name Inquiry API Payment QRIS tidak ada!')
        
        # * process inquiry QR
        request_type = 'post'
        method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
        model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)
        url = api_payment_config_obj.base_url + url_obj.url
        try:
            response = requests.post(url=url, headers=headers, data=payload)
        except requests.exceptions.RequestException as err:
            _logger.error(err)

            # * Create Failed Log
            response_code = response.status_code
            params = {
                'name': log_name,
                'url': url,
                'description': log_name,
                'ip_address': '',
                'response': json.loads(response.content),
                'payload': json.loads(payload),
                'headers': headers,
                'response_code': response_code,
                'status_code': response_code,
                'reference': '',
                'transaction_id': None,
                'api_type_id': api_payment_config_obj.api_type_id.id,
                'method_id': method_obj.id if method_obj else False,
                'model_id': model_obj.id if model_obj else False
            }
            api_payment_config_obj._create_api_log_bank(params)
            self._cr.commit()
            raise Warning(f"""
                Gagal terhubung dengan {url}
                Detail: {err.args}
            """)
        
        status_code = response.status_code
        content = json.loads(response.content)
        if status_code not in (200, 201):
            # * Create Failed Log
            response_code = response.status_code
            params = {
                'name': log_name,
                'url': url,
                'description': log_name,
                'ip_address': '',
                'response': content,
                'payload': json.loads(payload),
                'headers': headers,
                'response_code': response_code,
                'status_code': response_code,
                'reference': '',
                'transaction_id': None,
                'api_type_id': api_payment_config_obj.api_type_id.id,
                'method_id': method_obj.id if method_obj else False,
                'model_id': model_obj.id if model_obj else False
            }
            api_payment_config_obj._create_api_log_bank(params)
            self._cr.commit()
            warning_message = ''
            for key, value in content.items():
                warning_message += f'{key} : {value}\n'

            raise Warning(warning_message)

        # * Create Success Log
        response_code = response.status_code
        params = {
            'name': log_name,
            'url': url,
            'description': log_name,
            'ip_address': '',
            'response': content,
            'payload': json.loads(payload),
            'headers': headers,
            'response_code': response_code,
            'status_code': response_code,
            'reference': '',
            'transaction_id': None,
            'api_type_id': api_payment_config_obj.api_type_id.id,
            'method_id': method_obj.id if method_obj else False,
            'model_id': model_obj.id if model_obj else False
        }
        api_payment_config_obj._create_api_log_bank(params)

        return json.loads(response.content)
    
    def consume_inquiry_api_payment_qris_response(self, response_content, api_payment_config_obj):
        values = self._process_inquiry_api_payment_qris_response_content(response_content, api_payment_config_obj)
        if not values:
            raise Warning('Inquiry Response Content QRIS tidak ada!')
        
        # * update response to api payment object
        self.suspend_security().write(values)

        return True
    
    def inquiry_api_payment_va(self, setting_api_payment_config_obj, api_payment_config_obj):
        # * get url api payment qris object
        url_obj = self.env['tw.api.url'].sudo()._get_api_url_by_type(api_payment_config_obj, 'inquiry_payment_va', is_relative=False, is_get_object=True)
        
        # * get headers and payload
        headers, payload = self.suspend_security()._prepare_headers_payload_api_payment_qris(url_obj, setting_api_payment_config_obj, api_payment_config_obj, process_type='inquiry')
        
        log_name = self._get_log_name_inquiry_api_payment_qris(api_payment_config_obj)
        if not log_name:
            raise Warning('Log name Inquiry API Payment VA tidak ada!')
        
        # * process inquiry Virtual Account
        request_type = 'post'
        method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
        model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)
        url = api_payment_config_obj.base_url + url_obj.url
        try:
            response = requests.post(url=url, headers=headers, data=payload)
            # TODO: sementara, untuk testing callback saja di server tes. hapus nanti
            conf_params_obj = self.env['ir.config_parameter'].sudo().get_param('tw_payment_b2b_bank.dummy_data_callback_va')
            if conf_params_obj:
                results = eval(conf_params_obj)
                response = type(
                    'Response', (), {
                        'status_code': 200,
                        'content': json.dumps(results).encode('utf-8'),
                    }
                )()
        except requests.exceptions.RequestException as err:
            _logger.error(err)

            # * Create Failed Log
            response_code = response.status_code
            params = {
                'name': log_name,
                'url': url,
                'description': log_name,
                'ip_address': '',
                'response': json.loads(response.content),
                'payload': json.loads(payload),
                'headers': headers,
                'response_code': response_code,
                'status_code': response_code,
                'reference': '',
                'transaction_id': None,
                'api_type_id': api_payment_config_obj.api_type_id.id,
                'method_id': method_obj.id if method_obj else False,
                'model_id': model_obj.id if model_obj else False
            }
            api_payment_config_obj._create_api_log_bank(params)
            self._cr.commit()
            raise Warning(f"""
                Gagal terhubung dengan {url}
                Detail: {err.args}
            """)
        
        status_code = response.status_code
        content = json.loads(response.content)
        if status_code not in (200, 201):
            # * Create Failed Log
            response_code = response.status_code
            params = {
                'name': log_name,
                'url': url,
                'description': log_name,
                'ip_address': '',
                'response': content,
                'payload': json.loads(payload),
                'headers': headers,
                'response_code': response_code,
                'status_code': response_code,
                'reference': '',
                'transaction_id': None,
                'api_type_id': api_payment_config_obj.api_type_id.id,
                'method_id': method_obj.id if method_obj else False,
                'model_id': model_obj.id if model_obj else False
            }
            api_payment_config_obj._create_api_log_bank(params)
            self._cr.commit()
            warning_message = ''
            for key, value in content.items():
                warning_message += f'{key} : {value}\n'

            raise Warning(warning_message)

        # * Create Success Log
        response_code = response.status_code
        params = {
            'name': log_name,
            'url': url,
            'description': log_name,
            'ip_address': '',
            'response': content,
            'payload': json.loads(payload),
            'headers': headers,
            'response_code': response_code,
            'status_code': response_code,
            'reference': '',
            'transaction_id': None,
            'api_type_id': api_payment_config_obj.api_type_id.id,
            'method_id': method_obj.id if method_obj else False,
            'model_id': model_obj.id if model_obj else False
        }
        api_payment_config_obj._create_api_log_bank(params)

        return json.loads(response.content)
    
    def consume_inquiry_api_payment_va_response(self, response_content, api_payment_config_obj):
        values = self._process_inquiry_api_payment_va_response_content(response_content, api_payment_config_obj)
        if not values:
            raise Warning('Inquiry Response Content VA tidak ada!')
        
        # * update response to api payment object
        self.suspend_security().write(values)

        return True

    # 14: private methods
    def _get_log_name_generate_api_payment_qris(self, api_payment_config_obj):
        return False
    
    def _get_log_name_inquiry_api_payment_qris(self, api_payment_config_obj):
        return False
    
    def _get_payload_api_payment_qris(self, setting_api_payment_config_obj, api_payment_config_obj, process_type):
        return False
    
    def _generate_signature_headers(self, config_obj, str_to_sign):
        return False
    
    def _hash_payload(self, payload):
        minified_request_body = json.dumps(payload, separators=(',', ':')) # Minify the JSON string
        sha256_hash = hashlib.sha256(minified_request_body.encode('utf-8')).hexdigest() # Calculate SHA-256 hash
        
        return sha256_hash.lower() # HexEncode the SHA-256 hash
    
    def _get_access_token_qris_payment(self, api_payment_config_obj):
        results = api_payment_config_obj.suspend_security()._generate_qris_token()
        access_token = results.get('accessToken')
        
        return access_token
    
    def _get_headers_api_payment_qris(self, config_obj, access_token, url_obj, payload, setting_api_payment_config_obj):
        x_external_id = random.randint(10000, 99999)
        encoded_payload = self._hash_payload(payload)
        headers = self._generate_headers(config_obj, 'POST', access_token, url_obj, encoded_payload)
        headers.update({
            'X-PARTNER-ID': setting_api_payment_config_obj.x_partner_id,
            'CHANNEL-ID': str(setting_api_payment_config_obj.channel_id),
            'X-EXTERNAL-ID': str(x_external_id)
        })

        return headers
    
    def _generate_headers(self, config_obj, api_method, access_token, url_obj, encoded_payload):
        # * get timestamp
        timestamp = config_obj.suspend_security()._get_timestamp_qris_token()
        if not timestamp:
            raise Warning('Timestamp Generate Headers tidak ada!')
        
        str_to_sign = str(f'{api_method}:{url_obj.url}:{access_token}:{encoded_payload}:{timestamp}')
        signature = self._generate_signature_headers(config_obj, str_to_sign)
        if not signature:
            raise Warning('X-SIGNATURE Headers tidak ada!')
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-TIMESTAMP': timestamp,
            'X-SIGNATURE': str(signature),
            'Content-Type': 'application/json',
        }
            
        return headers
    
    def _prepare_headers_payload_api_payment_qris(self, url_obj, setting_api_payment_config_obj, api_payment_config_obj, process_type='generate_qris'):
        payload = self._get_payload_api_payment_qris(setting_api_payment_config_obj, api_payment_config_obj, process_type)
        if not payload:
            raise Warning('Data Payload kosong!')
        
        access_token = self._get_access_token_qris_payment(api_payment_config_obj)
        if not access_token:
            raise Warning('Data Access Token kosong!')
        
        headers = self._get_headers_api_payment_qris(api_payment_config_obj, access_token, url_obj, payload, setting_api_payment_config_obj)
        if not headers:
            raise Warning('Data Headers kosong!')

        return headers, json.dumps(payload)
    
    def _prepare_api_payment_qris_image_response(self, qris_obj, api_payment_config_obj):
        return False
    
    def _process_inquiry_api_payment_qris_response_content(self, response_content, api_payment_config_obj):
        return False
    
    def _process_inquiry_api_payment_va_response_content(self, response_content, api_payment_config_obj):
        return False
    
    def _prepare_inquiry_response_values(self, response, vals):
        additional_info = response.get('additionalInfo')
        amount = response.get('amount')
        transaction_status_desc = 'not found'
        if response.get('transactionStatusDesc'):
            transaction_status_desc = response.get('transactionStatusDesc').split()[0].lower()
            if transaction_status_desc == 'success':
                transaction_status_desc = 'Successfully'
        latest_transaction_status = response.get('latestTransactionStatus')
        
        response_code = response.get('responseCode')
        original_reference_no = response.get('originalReferenceNo')

        vals.update({
            'state': STATE_MAPPING.get(transaction_status_desc),
            'transaction_status': STATE_CODE_MAPPING.get(latest_transaction_status),
            'approval_code': response_code,
            'batch_number': original_reference_no,
            'terminal_id': response.get('terminalId'),
            'reason': response.get('responseMessage')
        })

        if amount:
            vals.update({
                'amount': amount.get('value'),
                'currency_code': amount.get('currency')
            })
            
        if additional_info:
            vals.update({
                'convenience_fee': additional_info.get('convenienceFee'),
                'issuer_reference_number': additional_info.get('issuerReferenceNumber'),
                'issuer_name': additional_info.get('issuerName'),
                'payer_name': additional_info.get('payerName'),
                'payer_phone_number': additional_info.get('payerPhoneNumber'),
                'customer_pan': additional_info.get('customerPan'),
                'acquirer_name': additional_info.get('acquirerName'),
                'detail_info': f"invoiceNumber: {additional_info.get('invoiceNumber')}" if additional_info.get('invoiceNumber') else False
            })
            
            merchant_info = additional_info.get('merchantInfo')
            if merchant_info:
                merchant_obj = self.env['res.partner'].suspend_security().search([
                    ('merchant_id', '=', merchant_info.get('merchantId'))
                ], limit=1)
                country_obj = self.env['res.country'].sudo().search([
                    ('code','=',merchant_info.get('country'))
                ], limit=1)
                if merchant_obj:
                    merchant_obj.suspend_security().write({
                        'name': merchant_info.get('name'),
                        'city': merchant_info.get('city'),
                        'zip': merchant_info.get('postalCode'),
                        'country_id': country_obj.id if country_obj else False,
                        'email': merchant_info.get('email'),
                        'merchant_pan': merchant_info.get('merchantPan'),
                        'payment_channel_name': merchant_info.get('paymentChannelName'),
                        'terminal_id': merchant_info.get('terminalId')
                    })
                else:
                    merchant_obj = merchant_obj.suspend_security().create({
                        'name': merchant_info.get('name'),
                        'city': merchant_info.get('city'),
                        'zip': merchant_info.get('postalCode'),
                        'country_id': country_obj.id if country_obj else False,
                        'email': merchant_info.get('email'),
                        'merchant_id': merchant_info.get('merchantId'),
                        'merchant_pan': merchant_info.get('merchantPan'),
                        'payment_channel_name': merchant_info.get('paymentChannelName'),
                        'terminal_id': merchant_info.get('terminalId')
                    })
                vals.update({'merchant_id': merchant_obj.id})
                
        return vals