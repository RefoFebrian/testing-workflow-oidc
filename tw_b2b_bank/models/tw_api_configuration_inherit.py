# 1: imports of python lib
from datetime import timedelta, datetime
import pytz
import json
import hashlib
import hmac
import base64
import requests

# 2: import of known third party lib
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class ApiConfigurationInherit(models.Model):
    _inherit = "tw.api.configuration"

    # 7: defaults methods

    # 8: fields
    corporate_id = fields.Char(string='Corporate ID')
    is_api_payment = fields.Boolean(string='API Payment', help='Flag untuk kebutuhan API Payment, ex: QRIS dan VA')
    creds_public_file = fields.Binary(string='Creds Public File', help='A file which is shared by Partner. The file is used to verify the signature sent by partner.')
    creds_public_filename = fields.Char(string='Creds Public Filename')
    creds_private_file = fields.Binary(string='Creds Private File', help='This file is used to generate signature that will be sent to partner. Then partner will verify the signature using public file we shared to them.')
    creds_private_filename = fields.Char(string='Creds Private Filename')

    # 9: relation fields
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', domain=['|', ('is_bank','=',True), ('is_fintech','=',True)], help='Kebutuhan untuk API Payment, ex: QRIS dan VA')
    area_id = fields.Many2one(comodel_name='res.area', string='Area', help='Kebutuhan untuk API Payment, ex: QRIS dan VA')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def get_hash_body(self, body):
        hash = hashlib.sha256(body.encode('utf-8')).hexdigest()
        
        return str(hash).lower()
    
    def get_timestamp(self):
        pst_now = pytz.UTC.localize(fields.Datetime.now()).astimezone(pytz.timezone(self.env.user.tz or 'Asia/Jakarta'))
        # pst_now = pst_now - timedelta(hours=7)
        pst_now = pst_now.isoformat(timespec='microseconds')
        pst_now = pst_now[:-13]
        pst_now += '.000+07:00'
        
        return pst_now
    
    def utilities_signature(self, api_secret, url):
        h = hmac.new(str(api_secret).encode('utf-8'), str(url).encode('utf-8'), hashlib.sha256)
        return str(h.hexdigest())

    # 14: private methods
    def _get_config_bank_by_name(self, bank_name, is_api_payment=False, company_obj=None, additional_domain=[]):
        filter_bank_name = self._get_actual_bank_name(bank_name)
        domain = [
            ('api_type_value','ilike',filter_bank_name),
            ('is_api_payment','=',is_api_payment),
        ]
        new_domain = domain.copy()
        if additional_domain:
            new_domain += additional_domain
        if company_obj:
            new_domain += [('area_id.company_ids','in',company_obj.id)]
        
        config_bank_obj = self.sudo().search(new_domain, limit=1)
        if not config_bank_obj:
            if additional_domain:
                domain += additional_domain
            config_bank_obj = self.sudo().search(domain, limit=1)
        if not config_bank_obj:
            raise Warning(f'Configuration API Bank/Fintech {bank_name} belum ada, harap buat dahulu !')
        
        return config_bank_obj

    def _create_api_log_bank(self, params):
        self.env['tw.api.log'].sudo().create_api_log(
            params.get('name'),
            params.get('url'),
            params.get('description'),
            params.get('ip_address'),
            params.get('response'),
            params.get('payload'),
            params.get('headers'),
            response_code=params.get('response_code'),
            status_code=params.get('status_code'),
            reference=params.get('reference'),
            transaction_id=params.get('transaction_id'),
            api_type_id=params.get('api_type_id'),
            method_id=params.get('method_id'),
            model_id=params.get('model_id')
        )

    def _get_actual_bank_name(self, bank_name):
        return bank_name
    
    def _get_timestamp_qris_token(self):
        return False
    
    def _generate_signature_qris_token(self, message):
        if self.is_api_payment and self.partner_id and self.creds_private_file:
            # load private key to generate signature as requested by X-SIGNATURE
            private_file = base64.decodebytes(self.creds_private_file)
            private_key = serialization.load_pem_private_key(
                private_file,
                password=None,
                backend=default_backend()
            )

            # apparently BRI doesn't need converted timezone,
            # since the converted Asia/Jakarta timezone always response an invalid signature
            encode_message = message.encode('utf-8')
            signature = private_key.sign(
                encode_message,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return base64.b64encode(signature)

        return False
    
    def _get_log_name_generate_qris_token(self):
        return False

    def _generate_qris_token(self):
        url = self.env['tw.api.url'].sudo()._get_api_url_by_type(self, 'get_token_qris', is_relative=False)
        timestamp = self._get_timestamp_qris_token()
        if not timestamp:
            raise Warning('Timestamp Get QRIS Token tidak ada!')
        
        # set message to sign
        x_client_key = self.client_id
        message = f'{x_client_key}|{timestamp}'
        x_signature = self._generate_signature_qris_token(message)
        if not x_signature:
            raise Warning('Gagal generate X-SIGNATURE QRIS Token!')
        
        # collecting all the headers content
        headers = {
            'X-SIGNATURE': x_signature.decode('utf-8'),
            'X-CLIENT-KEY': x_client_key,
            'X-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }
        payload = { 'grantType': 'client_credentials' }

        log_name = self._get_log_name_generate_qris_token()
        if not log_name:
            raise Warning('Log name Generate QRIS Token tidak ada!')

        request_type = 'post'
        method_obj = self.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
        model_obj = self.env['ir.model'].sudo().search([('model','=',self._name)], limit=1)
        try:
            response = requests.post(url=url, headers=headers, json=payload)
        except Exception as err:
            _logger.error(err)

            # * Create Failed Log
            # response_code = response.status_code
            params = {
                'name': log_name,
                'url': url,
                'description': err.args,
                'ip_address': '',
                'response': {},
                'payload': payload,
                'headers': headers,
                'response_code': 500,
                'status_code': 500,
                'reference': '',
                'transaction_id': None,
                'api_type_id': self.api_type_id.id,
                'method_id': method_obj.id if method_obj else False,
                'model_id': model_obj.id if model_obj else False
            }
            self._create_api_log_bank(params)
            # self._cr.commit()
            self._cr.rollback()
            raise Warning(err)
        
        content = response.content
        if response.status_code != 200:
            # * Create Failed Log
            response_code = response.status_code
            params = {
                'name': log_name,
                'url': url,
                'description': log_name,
                'ip_address': '',
                'response': content,
                'payload': payload,
                'headers': headers,
                'response_code': response_code,
                'status_code': response_code,
                'reference': '',
                'transaction_id': None,
                'api_type_id': self.api_type_id.id,
                'method_id': method_obj.id if method_obj else False,
                'model_id': model_obj.id if model_obj else False
            }
            self._create_api_log_bank(params)
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
            'response': json.loads(content),
            'payload': payload,
            'headers': headers,
            'response_code': response_code,
            'status_code': response_code,
            'reference': '',
            'transaction_id': None,
            'api_type_id': self.api_type_id.id,
            'method_id': method_obj.id if method_obj else False,
            'model_id': model_obj.id if model_obj else False
        }
        self._create_api_log_bank(params)
        
        return response.json()