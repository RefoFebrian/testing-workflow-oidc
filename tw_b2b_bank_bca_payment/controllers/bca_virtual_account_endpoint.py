# 1: imports of python lib
import json
import hashlib
import hmac
import base64
from datetime import datetime

# 2: import of known third party lib
from dateutil.relativedelta import relativedelta
from dateutil import parser

# 3:  imports of odoo
import odoo
from odoo import models, fields, api, _
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request
from odoo.http import Response
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.addons.tw_payment_b2b_bank.helpers import STATE_MAPPING, STATE_CODE_MAPPING
from odoo.addons.rest_api.rest_exception import valid_response_api, invalid_response_api
from odoo.addons.rest_api.controllers.main import verify_token

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class ControllerREST(http.Controller):
    @http.route('/api/ext/openapi/v1.0/access-token/b2b', methods=['POST'], type='json', auth='public', csrf=False, json_rpc=False)
    def _qr_dynamic_token_bca(self, **kwargs):
        _log = request.env['tw.api.log']
        headers = request.httprequest.headers
        x_client_key = headers.get('X-CLIENT-KEY')
        x_signature = headers.get('X-SIGNATURE')
        x_timestamp = headers.get('X-TIMESTAMP')
        new_headers = {
            'Content-Type': str(headers.get('Content-Type')),
            'X-CLIENT-KEY': str(x_client_key),
            'X-SIGNATURE': str(x_signature),
            'X-TIMESTAMP': str(x_timestamp)
        }
        name = 'BCA Qris Token'
        url = request.httprequest.url

        request_type = 'post'
        method_obj = request.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
        model_obj = request.env['ir.model'].sudo().search([('model','=','payment.transaction')], limit=1)

        if 'X-CLIENT-KEY' not in headers:
            response = {
                'responseCode': '4007301',
                'responseMessage': 'Invalid Field Format [clientId]'
            }
            _log.sudo().create_api_log(
                name,
                url,
                'Invalid Field Format [clientId]!',
                '',
                response,
                request.httprequest.json,
                new_headers,
                response_code=400,
                status_code=400,
                reference='',
                transaction_id=None,
                api_type_id=None,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(400, 'Invalid Field Format [clientId]', 'Invalid Field Format [clientId]', custom_response=response)

        client_obj = request.env['res.users'].sudo().search([('client_id', '=', str(x_client_key))], limit=1)
        if not client_obj:
            response = {
                'responseCode': '4017300',
                'responseMessage': 'Unauthorized. [Unknown client]'
            }
            _log.sudo().create_api_log(
                name,
                url,
                'Partner does not exist!',
                '',
                response,
                request.httprequest.json,
                new_headers,
                response_code=401,
                status_code=401,
                reference='',
                transaction_id=None,
                api_type_id=None,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(401, 'Unauthorized. [Unknown client]', 'Unauthorized. [Unknown client]', custom_response=response)
        
        api_config_obj = request.env['tw.api.configuration'].sudo()._get_config_bank_by_name(client_obj.partner_id.code, is_api_payment=True, additional_domain=[('partner_id','=',client_obj.partner_id.id)])
        try:
            # verify client signature
            str_to_sign = f'{x_client_key}|{x_timestamp}'
            client_obj.verify_signature(str_to_sign, x_signature)
        except Exception as err:
            logging.error(err)
            response = {
                'responseCode': '4017300',
                'responseMessage': 'Unauthorized. [Signature]'
            }
            _log.sudo().create_api_log(
                name,
                url,
                err.args,
                '',
                response,
                request.httprequest.json,
                new_headers,
                response_code=401,
                status_code=401,
                reference='',
                transaction_id=None,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(401, 'Unauthorized. [Signature]', 'Unauthorized. [Signature]', custom_response=response)
        
        if x_timestamp:
            try:
                check_timestamp = parser.parse(x_timestamp)
            except ValueError:
                response = {
                    'responseCode': '4007301',
                    'responseMessage': 'Invalid field format [X-TIMESTAMP]'
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    'Invalid field format [X-TIMESTAMP]!',
                    '',
                    response,
                    request.httprequest.json,
                    new_headers,
                    response_code=400,
                    status_code=400,
                    reference='',
                    transaction_id=None,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(400, 'Invalid field format [X-TIMESTAMP]', 'Invalid field format [X-TIMESTAMP]', custom_response=response)
    
        payload = request.httprequest.json
        if payload.get('grantType') == 'client_credentials':
            token_obj = request.env['res.users.apikeys'].sudo()._generate_jwt(client_obj.id, {
                'client_id': client_obj.client_id,
                'client_secret': client_obj.client_secret,
                'grant_type': 'bearer'
            }, expired_time=900, is_force_create=True)

            response = {
                'responseCode': '2007300',
                'responseMessage': 'Successful',
                'accessToken': token_obj.get('token').decode('utf-8') if not isinstance(token_obj.get('token'), str) else token_obj.get('token'),
                'tokenType': 'bearer',
                'expiresIn': 900 # request from BCA
            }
            _log.sudo().create_api_log(
                name,
                url,
                'Success Generate Token',
                '',
                response,
                payload,
                new_headers,
                response_code=200,
                status_code=200,
                reference='',
                transaction_id=None,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return valid_response_api(200, response)
        
        else:
            response = {
                'responseCode': '4007301',
                'responseMessage': 'Invalid Field Format [clientId/clientSecret/grantType]'
            }
            _log.sudo().create_api_log(
                name,
                url,
                'Parameter grantType is invalid!',
                '',
                response,
                payload,
                new_headers,
                response_code=400,
                status_code=400,
                reference='',
                transaction_id=None,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(400, 'Invalid Field Format [clientId/clientSecret/grantType]', 'Invalid Field Format [clientId/clientSecret/grantType]', custom_response=response)

    # @http.route('/api/ext/openapi/v1.0/transfer-va/inquiry', methods=['POST'], type='json', auth='public', csrf=False, json_rpc=False)
    @http.route('/openapi/v1.0/transfer-va/inquiry', methods=['POST'], type='json', auth='public', csrf=False, json_rpc=False)
    @verify_token
    def _transfer_va_inquiry(self, **kwargs):
        _log = request.env['tw.api.log']
        headers = request.httprequest.headers
        x_signature = headers.get('X-SIGNATURE')
        x_timestamp = headers.get('X-TIMESTAMP')
        channel_id = headers.get('CHANNEL-ID')
        x_partner_id = headers.get('X-PARTNER-ID')
        x_external_id = headers.get('X-EXTERNAL-ID')
        token = headers.get('Authorization', '').split(' ')[-1]
        new_headers = {
            'Content-Type': headers.get('Content-Type'),
            'X-SIGNATURE': x_signature,
            'X-TIMESTAMP': x_timestamp,
            'CHANNEL-ID': channel_id,
            'X-PARTNER-ID': x_partner_id,
            'X-EXTERNAL-ID': x_external_id,
            'Authorization': headers.get('Authorization')
        }

        name = 'BCA Transfer Virtual Account Inquiry'
        url = request.httprequest.url
        
        request_type = 'post'
        method_obj = request.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
        model_obj = request.env['ir.model'].sudo().search([('model','=','payment.transaction')], limit=1)
        today = datetime.now().date()

        payload = request.httprequest.json
        minified_request_body = json.dumps(payload, separators=(',', ':')) # Minify the JSON string
        
        partner_obj = request.env['res.partner']
        client_obj = request.env['res.users'].browse(request.session.uid)
        if not client_obj:
            response = {
                'responseCode': '4012400',
                'responseMessage': 'Unauthorized. [Unknown client]'
            }
            _log.sudo().create_api_log(
                name,
                url,
                'User is not found!',
                '',
                response,
                payload,
                new_headers,
                response_code=401,
                status_code=401,
                reference='',
                transaction_id=None,
                api_type_id=None,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(401, 'Unauthorized. [Unknown client]', 'Unauthorized. [Unknown client]', custom_response=response)
        
        api_config_obj = request.env['tw.api.configuration'].sudo()._get_config_bank_by_name(client_obj.partner_id.code, is_api_payment=True, additional_domain=[('partner_id','=',client_obj.partner_id.id)])
        setting_api_payment_obj = request.env['tw.setting.api.payment'].sudo().search([
            ('payment_usage','=','va'),
            ('provider_id','=',client_obj.partner_id.sudo().id)
        ], limit=1)
        if setting_api_payment_obj:
            if channel_id != setting_api_payment_obj.channel_id:
                response = {
                    'responseCode': '4012400',
                    'responseMessage': 'Unauthorized. [Unknown client]'
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    'Channel ID is invalid!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=401,
                    status_code=401,
                    reference='',
                    transaction_id=None,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(401, 'Unauthorized. [Unknown client]', 'Unauthorized. [Unknown client]', custom_response=response)
            
            if x_partner_id != setting_api_payment_obj.x_partner_id:
                response = {
                    'responseCode': '4012400',
                    'responseMessage': 'Unauthorized. [Unknown client]'
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    'X-Partner-ID is invalid!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=401,
                    status_code=401,
                    reference='',
                    transaction_id=None,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(401, 'Unauthorized. [Unknown client]', 'Unauthorized. [Unknown client]', custom_response=response)
        
        # TODO: hanya testing untuk di server tes. ubah lagi nanti kalau sudah production
        # relative_url = '/api/ext/openapi/' + url.split('/api/ext/openapi/')[-1]
        relative_url = '/openapi/' + url.split('/openapi/')[-1]
        sha256_hash = hashlib.sha256(minified_request_body.encode('utf-8')).hexdigest()
        body = sha256_hash.lower() # HexEncode the SHA-256 hash
        try:
            # verify client signature
            str_to_sign = ':'.join(['POST', relative_url, token, body, x_timestamp])
            verifier = base64.b64encode(
                hmac.new(
                    key=client_obj.client_secret.encode('utf-8'),
                    msg=str_to_sign.encode('utf-8'),
                    digestmod=hashlib.sha512
                ).digest()
            ).decode('utf-8')
            check_signature = hmac.compare_digest(x_signature, verifier)
            if not check_signature:
                raise Warning('Invalid Signature VA Inquiry BCA!')
        except Exception as err:
            logging.error(err)
            response = {
                'responseCode': '4012400',
                'responseMessage': 'Unauthorized. [Signature]'
            }
            _log.sudo().create_api_log(
                name,
                url,
                err.args,
                '',
                response,
                payload,
                new_headers,
                response_code=401,
                status_code=401,
                reference='',
                transaction_id=None,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(401, 'Unauthorized. [Signature]', 'Unauthorized. [Signature]', custom_response=response)
        
        if x_timestamp:
            try:
                check_timestamp = parser.parse(x_timestamp)
            except ValueError:
                response = {
                    'responseCode': '4007301',
                    'responseMessage': 'Invalid field format [X-TIMESTAMP]'
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    'Invalid field format [X-TIMESTAMP]!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=400,
                    status_code=400,
                    reference='',
                    transaction_id=None,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(400, 'Invalid field format [X-TIMESTAMP]', 'Invalid field format [X-TIMESTAMP]', custom_response=response)
            
        # check duplicate X-EXTERNAL-ID
        is_duplicate_x_external_id = False
        if x_external_id:
            start_of_day = datetime.strftime(today, '%Y-%m-%d 00:00:00')
            end_of_day = datetime.strftime(today, '%Y-%m-%d 23:59:59')
            filter_value = '%'+f'"X-EXTERNAL-ID": "{x_external_id}"'+'%'
            filter_log_name = 'BCA'
            query = f"""
                SELECT
                    tald.id
                FROM tw_api_log_detail tald
                LEFT JOIN tw_api_log tal ON tald.api_log_id = tal.id
                WHERE 1=1
                AND tal.name ILIKE '%{filter_log_name}%'
                AND tald.type = 'header'
                AND tald.value IS NOT NULL
                AND tald.create_date >= '{start_of_day}'
                AND tald.create_date <= '{end_of_day}'
                AND tald.value::TEXT ILIKE '{filter_value}'
            """
            request._cr.execute(query)
            log_duplicate_x_external_id_obj = request._cr.dictfetchall()
            if log_duplicate_x_external_id_obj:
                is_duplicate_x_external_id = True
        
        data = payload
        partnerServiceId = data.get('partnerServiceId') # Mandatory
        customerNo = data.get('customerNo') # Mandatory
        virtualAccountNo = data.get('virtualAccountNo') # Mandatory
        trxDateInit = data.get('trxDateInit')
        channelCode = data.get('channelCode')
        additionalInfo = data.get('additionalInfo')
        inquiryRequestId = data.get('inquiryRequestId') # Mandatory
        
        virtual_account_data_response = {
            'inquiryStatus': '01',
            'inquiryReason': {
                'english': 'Failed',
                'indonesia': 'Gagal'
            },
            'partnerServiceId': partnerServiceId,
            'customerNo': customerNo,
            'virtualAccountNo': virtualAccountNo,
            'virtualAccountName': '',
            'inquiryRequestId': inquiryRequestId,
            'totalAmount': {
                'value': '',
                'currency': ''
            },
            'subCompany': '',
            'billDetails': [],
            'freeTexts': []
        }

        # * check mandatory fields
        mandatory_fields = ['partnerServiceId', 'customerNo', 'virtualAccountNo', 'inquiryRequestId']
        for mandatory in mandatory_fields:
            if not data.get(mandatory):
                response = {
                    'responseCode': '4002402',
                    'responseMessage': f'Invalid Mandatory Field {mandatory}',
                    'virtualAccountData': virtual_account_data_response,
                    'additionalInfo': {}
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    f'Trx VA {customerNo} invalid mandatory fields!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=400,
                    status_code=400,
                    reference='',
                    transaction_id=None,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(400, f'Invalid Mandatory Field {mandatory}', f'Invalid Mandatory Field {mandatory}', custom_response=response)
            
            # * check value of fields is invalid format or not
            if not data.get(mandatory).strip().isdigit():
                response = {
                    'responseCode': '4002401',
                    'responseMessage': f'Invalid Field Format {mandatory}',
                    'virtualAccountData': virtual_account_data_response,
                    'additionalInfo': {}
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    f'Trx VA {customerNo} invalid field format!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=400,
                    status_code=400,
                    reference='',
                    transaction_id=None,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(400, f'Invalid Field Format {mandatory}', f'Invalid Field Format {mandatory}', custom_response=response)

        # TODO: sementara, untuk testing callback saja di server tes. hapus nanti
        conf_params_obj = request.env['ir.config_parameter'].sudo().get_param('tw_b2b_bank_bca_payment.dummy_data_va')
        if conf_params_obj:
            conf_params_obj = eval(conf_params_obj)
            customerNo = conf_params_obj.get('customer_no')
        payment_trx_model = request.env['payment.transaction']
        payment_trx_obj = payment_trx_model.sudo().search([('transaction_keys','=',customerNo.strip())], limit=1)
        if not payment_trx_obj:
            virtual_account_data_response.get('inquiryReason').update({
                'english': 'Virtual Account Not Found',
                'indonesia': 'Virtual Account Tidak Ditemukan'
            })
            if is_duplicate_x_external_id:
                virtual_account_data_response.get('inquiryReason').update({
                    'english': 'Cannot use the same X-EXTERNAL-ID',
                    'indonesia': 'Tidak bisa menggunakan X-EXTERNAL-ID yang sama'
                })
                response = {
                    'responseCode': '4092400',
                    'responseMessage': 'Conflict',
                    'virtualAccountData': virtual_account_data_response,
                    'additionalInfo': {}
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    f'Trx VA {customerNo} not found and duplicate X-EXTERNAL-ID!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=409,
                    status_code=409,
                    reference='',
                    transaction_id=None,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(409, 'Conflict', 'Conflict', custom_response=response)
            
            response = {
                'responseCode': '4042412',
                'responseMessage': 'Invalid Bill/Virtual Account [Not Found]',
                'virtualAccountData': virtual_account_data_response,
                'additionalInfo': {}
            }
            _log.sudo().create_api_log(
                name,
                url,
                f'Trx VA {customerNo} not found!',
                '',
                response,
                payload,
                new_headers,
                response_code=404,
                status_code=404,
                reference='',
                transaction_id=None,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(404, 'Invalid Bill/Virtual Account [Not Found]', 'Invalid Bill/Virtual Account [Not Found]', custom_response=response)
        
        # * check is virtual account expired or not (24 hours)
        create_date = payment_trx_obj.create_date
        conf_param_exp_date_va = request.env['ir.config_parameter'].sudo().get_param('tw_b2b_bank_bca_payment.expiry_date_va')
        if conf_param_exp_date_va:
            conf_param_exp_date_va = eval(conf_param_exp_date_va)
        else:
            conf_param_exp_date_va = 24
        expiry_date_va = create_date + relativedelta(hours=conf_param_exp_date_va)
        if payment_trx_obj.state != 'done' and datetime.now() > expiry_date_va:
            virtual_account_data_response.get('inquiryReason').update({
                'english': 'Bill Expired',
                'indonesia': 'Tagihan sudah kedaluwarsa'
            })
            if is_duplicate_x_external_id:
                virtual_account_data_response.get('inquiryReason').update({
                    'english': 'Cannot use the same X-EXTERNAL-ID',
                    'indonesia': 'Tidak bisa menggunakan X-EXTERNAL-ID yang sama'
                })
                response = {
                    'responseCode': '4092400',
                    'responseMessage': 'Conflict',
                    'virtualAccountData': virtual_account_data_response,
                    'additionalInfo': {}
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    f'Trx VA {customerNo} already expired and duplicate X-EXTERNAL-ID!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=409,
                    status_code=409,
                    reference='',
                    transaction_id=payment_trx_obj.id,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(409, 'Conflict', 'Conflict', custom_response=response)
            
            response = {
                'responseCode': '4042419',
                'responseMessage': 'Invalid Bill/Virtual Account',
                'virtualAccountData': virtual_account_data_response,
                'additionalInfo': {}
            }
            _log.sudo().create_api_log(
                name,
                url,
                f'Trx VA {customerNo} already expired!',
                '',
                response,
                payload,
                new_headers,
                response_code=404,
                status_code=404,
                reference='',
                transaction_id=payment_trx_obj.id,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(404, 'Invalid Bill/Virtual Account', 'Invalid Bill/Virtual Account', custom_response=response)
        
        virtual_account_data_response['virtualAccountName'] = 'TDM' or payment_trx_obj.customer_id.sudo().name
        if payment_trx_obj.state == 'done':
            virtual_account_data_response.get('inquiryReason').update({
                'english': 'Bill Has Been Paid',
                'indonesia': 'Tagihan sudah lunas'
            })
            if is_duplicate_x_external_id:
                virtual_account_data_response.get('inquiryReason').update({
                    'english': 'Cannot use the same X-EXTERNAL-ID',
                    'indonesia': 'Tidak bisa menggunakan X-EXTERNAL-ID yang sama'
                })
                response = {
                    'responseCode': '4092400',
                    'responseMessage': 'Conflict',
                    'virtualAccountData': virtual_account_data_response,
                    'additionalInfo': {}
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    f'Trx VA {customerNo} already Paid and duplicate X-EXTERNAL-ID!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=409,
                    status_code=409,
                    reference='',
                    transaction_id=payment_trx_obj.id,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(409, 'Conflict', 'Conflict', custom_response=response)
            
            response = {
                'responseCode': '4042414',
                'responseMessage': 'Paid Bill',
                'virtualAccountData': virtual_account_data_response,
                'additionalInfo': {}
            }
            _log.sudo().create_api_log(
                name,
                url,
                f'Trx VA {customerNo} already Paid!',
                '',
                response,
                payload,
                new_headers,
                response_code=404,
                status_code=404,
                reference='',
                transaction_id=payment_trx_obj.id,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(404, 'Paid Bill', 'Paid Bill', custom_response=response)
        
        vals = {
            'acquirer_name': partnerServiceId,
            'payer_name': customerNo,
            'payer_phone_number': payment_trx_obj.customer_id.mobile if payment_trx_obj.customer_id else False,
            'transaction_id': inquiryRequestId,
            'va_no': virtualAccountNo,
            'transaction_status': '2', #?: pending ketika BCA hit
            'state': 'pending'
        }
        detail_info = f'partnerServiceId: {partnerServiceId}\n'
        detail_info += f'customerNo: {customerNo}\n'
        detail_info += f'virtualAccountNo: {virtualAccountNo}\n'
        detail_info += f'inquiryRequestId: {inquiryRequestId}\n'
        if trxDateInit:
            detail_info += f'trxDateInit: {str(trxDateInit)}\n'
        if channelCode:
            detail_info += f'channelCode: {str(channelCode)}\n'
        if additionalInfo:
            detail_info += f'additionalInfo: {str(additionalInfo)}\n'
        vals['detail_info'] = detail_info
        # * update va obj
        payment_trx_obj.suspend_security().write(vals)

        # * get trx obj
        trx_obj = request.env['tw.account.payment'].sudo().search([
            ('name','=',payment_trx_obj.reference)
        ], limit=1)
        if trx_obj:
            value_totalAmount = 0
            if hasattr(trx_obj, 'amount_total'):
                value_totalAmount = trx_obj.amount_total
            elif hasattr(trx_obj, 'amount'):
                value_totalAmount = trx_obj.amount
            virtual_account_data_response.update({
                'inquiryStatus': '00',
                'inquiryReason': {
                    'english': 'Success',
                    'indonesia': 'Sukses'
                },
                'totalAmount': {
                    'value': str(value_totalAmount).replace('.0', '.00'),
                    'currency': 'IDR'
                },
                'subCompany': setting_api_payment_obj.sub_company if setting_api_payment_obj.sub_company else '00000'
            })

        response = {
            'responseCode': '2002400',
            'responseMessage': 'Successful',
            'virtualAccountData': virtual_account_data_response,
            'additionalInfo': {}
        }
        if is_duplicate_x_external_id:
            virtual_account_data_response.get('inquiryReason').update({
                'indonesia': 'Tidak bisa menggunakan X-EXTERNAL-ID yang sama',
                'english': 'Cannot use the same X-EXTERNAL-ID'
            })
            response.update({
                'responseMessage': 'Conflict'
            })

        if is_duplicate_x_external_id:
            _log.sudo().create_api_log(
                name,
                url,
                'Failed Notification Inquiry API Payment Trx VA BCA because duplicate X-EXTERNAL-ID (Conflict)!',
                '',
                response,
                payload,
                new_headers,
                response_code=409,
                status_code=409,
                reference='',
                transaction_id=payment_trx_obj.id,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(409, 'Conflict', 'Conflict', custom_response=response)
        else:
            _log.sudo().create_api_log(
                name,
                url,
                'Success Notification Inquiry API Payment Trx VA BCA',
                '',
                response,
                payload,
                new_headers,
                response_code=200,
                status_code=200,
                reference='',
                transaction_id=payment_trx_obj.id,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return valid_response_api(200, response)
        
    # @http.route('/api/ext/openapi/v1.0/transfer-va/payment', methods=['POST'], type='json', auth='public', csrf=False, json_rpc=False)
    @http.route('/openapi/v1.0/transfer-va/payment', methods=['POST'], type='json', auth='public', csrf=False, json_rpc=False)
    @verify_token
    def _transfer_va_payment(self, **kwargs):
        _log = request.env['tw.api.log']
        headers = request.httprequest.headers
        x_signature = headers.get('X-SIGNATURE')
        x_timestamp = headers.get('X-TIMESTAMP')
        channel_id = headers.get('CHANNEL-ID')
        x_partner_id = headers.get('X-PARTNER-ID')
        x_external_id = headers.get('X-EXTERNAL-ID')
        token = headers.get('Authorization', '').split(' ')[-1]
        new_headers = {
            'Content-Type': headers.get('Content-Type'),
            'X-SIGNATURE': x_signature,
            'X-TIMESTAMP': x_timestamp,
            'CHANNEL-ID': channel_id,
            'X-PARTNER-ID': x_partner_id,
            'X-EXTERNAL-ID': x_external_id,
            'Authorization': headers.get('Authorization')
        }

        name = 'BCA Transfer Virtual Account Payment'
        url = request.httprequest.url

        request_type = 'post'
        method_obj = request.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
        model_obj = request.env['ir.model'].sudo().search([('model','=','payment.transaction')], limit=1)
        today = datetime.now().date()

        payload = request.httprequest.json
        minified_request_body = json.dumps(payload, separators=(',', ':')) # Minify the JSON string
        
        partner_obj = request.env['res.partner']
        client_obj = request.env['res.users'].browse(request.session.uid)
        if not client_obj:
            response = {
                'responseCode': '4012500',
                'responseMessage': 'Unauthorized. [Unknown client]'
            }
            _log.sudo().create_api_log(
                name,
                url,
                'User is not found!',
                '',
                response,
                payload,
                new_headers,
                response_code=401,
                status_code=401,
                reference='',
                transaction_id=None,
                api_type_id=None,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(401, 'Unauthorized. [Unknown client]', 'Unauthorized. [Unknown client]', custom_response=response)
        
        api_config_obj = request.env['tw.api.configuration'].sudo()._get_config_bank_by_name(client_obj.partner_id.code, is_api_payment=True, additional_domain=[('partner_id','=',client_obj.partner_id.id)])
        setting_api_payment_obj = request.env['tw.setting.api.payment'].sudo().search([
            ('payment_usage','=','va'),
            ('provider_id','=',client_obj.partner_id.sudo().id)
        ], limit=1)
        if setting_api_payment_obj:
            if channel_id != setting_api_payment_obj.channel_id:
                response = {
                    'responseCode': '4012500',
                    'responseMessage': 'Unauthorized. [Unknown client]'
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    'Channel ID is invalid!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=401,
                    status_code=401,
                    reference='',
                    transaction_id=None,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(401, 'Unauthorized. [Unknown client]', 'Unauthorized. [Unknown client]', custom_response=response)
            
            if x_partner_id != setting_api_payment_obj.x_partner_id:
                response = {
                    'responseCode': '4012500',
                    'responseMessage': 'Unauthorized. [Unknown client]'
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    'X-Partner-ID is invalid!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=401,
                    status_code=401,
                    reference='',
                    transaction_id=None,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(401, 'Unauthorized. [Unknown client]', 'Unauthorized. [Unknown client]', custom_response=response)
        
        # TODO: hanya testing untuk di server tes. ubah lagi nanti kalau sudah production
        # relative_url = '/api/ext/openapi/' + url.split('/api/ext/openapi/')[-1]
        relative_url = '/openapi/' + url.split('/openapi/')[-1]
        sha256_hash = hashlib.sha256(minified_request_body.encode('utf-8')).hexdigest()
        body = sha256_hash.lower() # HexEncode the SHA-256 hash
        try:
            # verify client signature
            str_to_sign = ':'.join(['POST', relative_url, token, body, x_timestamp])
            verifier = base64.b64encode(
                hmac.new(
                    key=client_obj.client_secret.encode('utf-8'),
                    msg=str_to_sign.encode('utf-8'),
                    digestmod=hashlib.sha512
                ).digest()
            ).decode('utf-8')
            check_signature = hmac.compare_digest(x_signature, verifier)
            if not check_signature:
                raise Warning('Invalid Signature VA Payment BCA!')
        except Exception as err:
            logging.error(err)
            response = {
                'responseCode': '4012500',
                'responseMessage': 'Unauthorized. [Signature]'
            }
            _log.sudo().create_api_log(
                name,
                url,
                err.args,
                '',
                response,
                payload,
                new_headers,
                response_code=401,
                status_code=401,
                reference='',
                transaction_id=None,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(401, 'Unauthorized. [Signature]', 'Unauthorized. [Signature]', custom_response=response)
        
        if x_timestamp:
            try:
                check_timestamp = parser.parse(x_timestamp)
            except ValueError:
                response = {
                    'responseCode': '4007301',
                    'responseMessage': 'Invalid field format [X-TIMESTAMP]'
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    'Invalid field format [X-TIMESTAMP]!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=400,
                    status_code=400,
                    reference='',
                    transaction_id=None,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(400, 'Invalid field format [X-TIMESTAMP]', 'Invalid field format [X-TIMESTAMP]', custom_response=response)
            
        # check duplicate X-EXTERNAL-ID
        is_duplicate_x_external_id = False
        if x_external_id:
            start_of_day = datetime.strftime(today, '%Y-%m-%d 00:00:00')
            end_of_day = datetime.strftime(today, '%Y-%m-%d 23:59:59')
            filter_value = '%'+f'"X-EXTERNAL-ID": "{x_external_id}"'+'%'
            filter_log_name = 'BCA'
            query = f"""
                SELECT
                    tald.id
                FROM tw_api_log_detail tald
                LEFT JOIN tw_api_log tal ON tald.api_log_id = tal.id
                WHERE 1=1
                AND tal.name ILIKE '%{filter_log_name}%'
                AND tald.type = 'header'
                AND tald.value IS NOT NULL
                AND tald.create_date >= '{start_of_day}'
                AND tald.create_date <= '{end_of_day}'
                AND tald.value::TEXT ILIKE '{filter_value}'
            """
            request._cr.execute(query)
            log_duplicate_x_external_id_obj = request._cr.dictfetchall()
            if log_duplicate_x_external_id_obj:
                is_duplicate_x_external_id = True
        
        data = payload
        partnerServiceId = data.get('partnerServiceId') # Mandatory
        customerNo = data.get('customerNo') # Mandatory
        virtualAccountNo = data.get('virtualAccountNo') # Mandatory
        virtualAccountName = data.get('virtualAccountName')
        paymentRequestId = data.get('paymentRequestId') # Mandatory
        channelCode = data.get('channelCode')
        hashedSourceAccountNo = data.get('hashedSourceAccountNo')
        sourceBankCode = data.get('sourceBankCode')
        paidAmount = data.get('paidAmount') # Mandatory
        cumulativePaymentAmount = data.get('cumulativePaymentAmount')
        paidBills = data.get('paidBills')
        totalAmount = data.get('totalAmount')
        trxDateTime = data.get('trxDateTime')
        referenceNo = data.get('referenceNo')
        flagAdvise = data.get('flagAdvise')
        subCompany = data.get('subCompany')
        billDetails = data.get('billDetails', [None])
        additionalInfo = data.get('additionalInfo')

        # check inconsistent request X-EXTERNAL-ID & paymentRequestId duplicate (2x). already hit before.
        is_inconsistent_req = False
        if x_external_id and paymentRequestId:
            filter_request_value = '%'+f'"paymentRequestId": "{paymentRequestId}"'+'%'
            filter_request_value_2 = '%'+f'"paymentRequestId":"{paymentRequestId}"'+'%'
            query = f"""
                SELECT
                    tald.id
                FROM tw_api_log_detail tald
                LEFT JOIN tw_api_log tal ON tald.api_log_id = tal.id
                WHERE 1=1
                AND tal.name ILIKE '%{filter_log_name}%'
                AND tald.type IN ('header', 'payload')
                AND tald.value IS NOT NULL
                AND tald.value::TEXT ILIKE '{filter_value}'
                AND (
                    tald.value::TEXT ILIKE '{filter_request_value}'
                    OR
                    tald.value::TEXT ILIKE '{filter_request_value_2}'
                )
            """
            request._cr.execute(query)
            log_duplicate_inconsisten_req_obj = request._cr.dictfetchall()
            if log_duplicate_inconsisten_req_obj:
                is_inconsistent_req = True

        if not trxDateTime:
            timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            trxDateTime = (parser.parse(timestamp[:-5]) + relativedelta(hours=7)).isoformat() + '+07:00'

        virtual_account_data_response = {
            'paymentFlagReason': {
                'english': 'Failed',
                'indonesia': 'Gagal'
            },
            'partnerServiceId': partnerServiceId,
            'customerNo': customerNo,
            'virtualAccountNo': virtualAccountNo,
            'virtualAccountName': virtualAccountName or client_obj.partner_id.sudo().name,
            'paymentRequestId': paymentRequestId,
            'paidAmount': {
                'value': paidAmount.get('value'),
                'currency': paidAmount.get('currency')
            },
            'trxDateTime': trxDateTime,
            'referenceNo': referenceNo,
            'paymentFlagStatus': '01',
            'billDetails': [],
            'freeTexts': []
        }
        billTotalAmount, billCurrency = 0, 0
        if billDetails[0]:
            billAmount = billDetails[0].get('billAmount')
            billTotalAmount = billAmount.get('value')
            billCurrency = billAmount.get('value')
            virtual_account_data_response.update({
                'billDetails': [
                    {
                        'billerReferenceId': billDetails[0].get('billReferenceNo'),
                        'billNo': billDetails[0].get('billNo'),
                        'billDescription': {
                            'english': billDetails[0].get('billDescription').get('english'),
                            'indonesia': billDetails[0].get('billDescription').get('indonesia')
                        },
                        'billSubCompany': billDetails[0].get('billSubCompany'),
                        'billAmount': {
                            'value': billDetails[0].get('billAmount').get('value'),
                            'currency': billDetails[0].get('billAmount').get('currency')
                        },
                        'additionalInfo': billDetails[0].get('additionalInfo'),
                        'status': '01',
                        'reason': {
                            'english': 'Failed',
                            'indonesia': 'Gagal'
                        }
                    }
                ]
            })
        if not totalAmount:
            totalAmount = {
                'value': billTotalAmount if billTotalAmount else paidAmount.get('value'),
                'currency': billCurrency if billCurrency else paidAmount.get('currency')
            }
        virtual_account_data_response.update({'totalAmount': totalAmount})
        
        if totalAmount:
            if '.00' not in totalAmount.get('value'):
                # * Invalid Amount
                response = {
                    'responseCode': '4042513',
                    'responseMessage': 'Invalid Amount',
                    'virtualAccountData': virtual_account_data_response,
                    'additionalInfo': {}
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    f'Trx VA {customerNo} has invalid Amount (invalid format value of totalAmount)!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=404,
                    status_code=404,
                    reference='',
                    transaction_id=None,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(404, 'Invalid Amount', 'Invalid Amount', custom_response=response)

        # * check mandatory fields
        mandatory_fields = ['partnerServiceId', 'customerNo', 'virtualAccountNo', 'paymentRequestId', 'paidAmount']
        for mandatory in mandatory_fields:
            if not data.get(mandatory):
                response = {
                    'responseCode': '4002502',
                    'responseMessage': 'Invalid Mandatory Field {%s}' % (mandatory),
                    'virtualAccountData': virtual_account_data_response,
                    'additionalInfo': {}
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    f'Trx VA {customerNo} invalid mandatory fields!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=400,
                    status_code=400,
                    reference='',
                    transaction_id=None,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(400, f'Invalid Mandatory Field {mandatory}', f'Invalid Mandatory Field {mandatory}', custom_response=response)
            
            # * check value of fields is invalid format or not
            if mandatory == 'paidAmount':
                paid_amount_obj = data.get(mandatory)
                if '.00' not in paid_amount_obj.get('value'):
                    # * Invalid Amount
                    response = {
                        'responseCode': '4042513',
                        'responseMessage': 'Invalid Amount',
                        'virtualAccountData': virtual_account_data_response,
                        'additionalInfo': {}
                    }
                    _log.sudo().create_api_log(
                        name,
                        url,
                        f'Trx VA {customerNo} has invalid Amount (invalid format value of paidAmount)!',
                        '',
                        response,
                        payload,
                        new_headers,
                        response_code=404,
                        status_code=404,
                        reference='',
                        transaction_id=None,
                        api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                        method_id=method_obj.id if method_obj else False,
                        model_id=model_obj.id if model_obj else False
                    )
                    return invalid_response_api(404, 'Invalid Amount', 'Invalid Amount', custom_response=response)
            else:
                if not data.get(mandatory).strip().isdigit():
                    response = {
                        'responseCode': '4002501',
                        'responseMessage': 'Invalid Field Format {%s}' % (mandatory),
                        'virtualAccountData': virtual_account_data_response,
                        'additionalInfo': {}
                    }
                    _log.sudo().create_api_log(
                        name,
                        url,
                        f'Trx VA {customerNo} invalid field format!',
                        '',
                        response,
                        payload,
                        new_headers,
                        response_code=400,
                        status_code=400,
                        reference='',
                        transaction_id=None,
                        api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                        method_id=method_obj.id if method_obj else False,
                        model_id=model_obj.id if model_obj else False
                    )
                    return invalid_response_api(400, f'Invalid Field Format {mandatory}', f'Invalid Field Format {mandatory}', custom_response=response)

        # TODO: sementara, untuk testing callback saja di server tes. hapus nanti
        conf_params_obj = request.env['ir.config_parameter'].sudo().get_param('tw_b2b_bank_bca_payment.dummy_data_va')
        if conf_params_obj:
            conf_params_obj = eval(conf_params_obj)
            customerNo = conf_params_obj.get('customer_no')
            amount = conf_params_obj.get('amount')
            paidAmount['value'] = amount
        payment_trx_model = request.env['payment.transaction']
        payment_trx_obj = payment_trx_model.sudo().search([('transaction_keys','=',customerNo.strip())], limit=1)
        if not payment_trx_obj:
            virtual_account_data_response.get('paymentFlagReason').update({
                'english': 'Virtual Account Not Found',
                'indonesia': 'Virtual Account Tidak Ditemukan'
            })
            virtual_account_data_response['virtualAccountName'] = ''
            virtual_account_data_response.get('paidAmount').update({
                'value': '',
                'currency': ''
            })
            virtual_account_data_response.get('totalAmount').update({
                'value': '',
                'currency': ''
            })
            if is_inconsistent_req:
                response = {
                    'responseCode': '4042518',
                    'responseMessage': 'Inconsistent Request',
                    'virtualAccountData': virtual_account_data_response,
                    'additionalInfo': {}
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    f'Trx VA {customerNo} not found and duplicate X-EXTERNAL-ID & paymentRequestId (Inconsistent Request)!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=404,
                    status_code=404,
                    reference='',
                    transaction_id=None,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(404, 'Inconsistent Request', 'Inconsistent Request', custom_response=response)
            
            if is_duplicate_x_external_id:
                virtual_account_data_response.get('paymentFlagReason').update({
                    'english': 'Cannot use the same X-EXTERNAL-ID',
                    'indonesia': 'Tidak bisa menggunakan X-EXTERNAL-ID yang sama'
                })
                response = {
                    'responseCode': '4092500',
                    'responseMessage': 'Conflict',
                    'virtualAccountData': virtual_account_data_response,
                    'additionalInfo': {}
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    f'Trx VA {customerNo} not found and duplicate X-EXTERNAL-ID (Conflict)!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=409,
                    status_code=409,
                    reference='',
                    transaction_id=None,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(409, 'Conflict', 'Conflict', custom_response=response)
            
            response = {
                'responseCode': '4042512',
                'responseMessage': 'Invalid Bill/Virtual Account [Not Found]',
                'virtualAccountData': virtual_account_data_response,
                'additionalInfo': {}
            }
            _log.sudo().create_api_log(
                name,
                url,
                f'Trx VA {customerNo} not found!',
                '',
                response,
                payload,
                new_headers,
                response_code=404,
                status_code=404,
                reference='',
                transaction_id=None,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(404, 'Invalid Bill/Virtual Account [Not Found]', 'Invalid Bill/Virtual Account [Not Found]', custom_response=response)
        
        # * check is virtual account expired or not (24 hours)
        create_date = payment_trx_obj.create_date
        conf_param_exp_date_va = request.env['ir.config_parameter'].sudo().get_param('tw_b2b_bank_bca_payment.expiry_date_va')
        if conf_param_exp_date_va:
            conf_param_exp_date_va = eval(conf_param_exp_date_va)
        else:
            conf_param_exp_date_va = 24
        expiry_date_va = create_date + relativedelta(hours=conf_param_exp_date_va)
        if payment_trx_obj.state != 'done' and datetime.now() > expiry_date_va:
            virtual_account_data_response.get('paymentFlagReason').update({
                'english': 'Bill Expired',
                'indonesia': 'Tagihan sudah kedaluwarsa'
            })
            if is_inconsistent_req:
                virtual_account_data_response['paymentFlagStatus'] = '00'
                virtual_account_data_response.get('paymentFlagReason').update({
                    'english': 'Success',
                    'indonesia': 'Sukses'
                })
                response = {
                    'responseCode': '4042518',
                    'responseMessage': 'Inconsistent Request',
                    'virtualAccountData': virtual_account_data_response,
                    'additionalInfo': {}
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    f'Trx VA {customerNo} already expired and duplicate X-EXTERNAL-ID & paymentRequestId (Inconsistent Request)!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=404,
                    status_code=404,
                    reference='',
                    transaction_id=payment_trx_obj.id,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(404, 'Inconsistent Request', 'Inconsistent Request', custom_response=response)
            
            if is_duplicate_x_external_id:
                virtual_account_data_response.get('paymentFlagReason').update({
                    'english': 'Cannot use the same X-EXTERNAL-ID',
                    'indonesia': 'Tidak bisa menggunakan X-EXTERNAL-ID yang sama'
                })
                response = {
                    'responseCode': '4092500',
                    'responseMessage': 'Conflict',
                    'virtualAccountData': virtual_account_data_response,
                    'additionalInfo': {}
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    f'Trx VA {customerNo} already expired and duplicate X-EXTERNAL-ID (Conflict)!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=409,
                    status_code=409,
                    reference='',
                    transaction_id=payment_trx_obj.id,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(409, 'Conflict', 'Conflict', custom_response=response)
            
            response = {
                'responseCode': '4042519',
                'responseMessage': 'Invalid Bill/Virtual Account',
                'virtualAccountData': virtual_account_data_response,
                'additionalInfo': {}
            }
            _log.sudo().create_api_log(
                name,
                url,
                f'Trx VA {customerNo} already expired!',
                '',
                response,
                payload,
                new_headers,
                response_code=404,
                status_code=404,
                reference='',
                transaction_id=payment_trx_obj.id,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(404, 'Invalid Bill/Virtual Account', 'Invalid Bill/Virtual Account', custom_response=response)
        
        if payment_trx_obj.state == 'done':
            virtual_account_data_response.get('paymentFlagReason').update({
                'english': 'Bill Has Been Paid',
                'indonesia': 'Tagihan sudah lunas'
            })
            if is_inconsistent_req:
                virtual_account_data_response['paymentFlagStatus'] = '00'
                virtual_account_data_response.get('paymentFlagReason').update({
                    'english': 'Success',
                    'indonesia': 'Sukses'
                })
                response = {
                    'responseCode': '4042518',
                    'responseMessage': 'Inconsistent Request',
                    'virtualAccountData': virtual_account_data_response,
                    'additionalInfo': {}
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    f'Trx VA {customerNo} already Paid and duplicate X-EXTERNAL-ID & paymentRequestId (Inconsistent Request)!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=404,
                    status_code=404,
                    reference='',
                    transaction_id=payment_trx_obj.id,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(404, 'Inconsistent Request', 'Inconsistent Request', custom_response=response)
            
            if is_duplicate_x_external_id:
                virtual_account_data_response.get('paymentFlagReason').update({
                    'english': 'Cannot use the same X-EXTERNAL-ID',
                    'indonesia': 'Tidak bisa menggunakan X-EXTERNAL-ID yang sama'
                })
                response = {
                    'responseCode': '4092500',
                    'responseMessage': 'Conflict',
                    'virtualAccountData': virtual_account_data_response,
                    'additionalInfo': {}
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    f'Trx VA {customerNo} already Paid and duplicate X-EXTERNAL-ID (Conflict)!',
                    '',
                    response,
                    payload,
                    new_headers,
                    response_code=409,
                    status_code=409,
                    reference='',
                    transaction_id=payment_trx_obj.id,
                    api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                    method_id=method_obj.id if method_obj else False,
                    model_id=model_obj.id if model_obj else False
                )
                return invalid_response_api(409, 'Conflict', 'Conflict', custom_response=response)
            
            response = {
                'responseCode': '4042414',
                'responseMessage': 'Paid Bill',
                'virtualAccountData': virtual_account_data_response,
                'additionalInfo': {}
            }
            _log.sudo().create_api_log(
                name,
                url,
                f'Trx VA {customerNo} already Paid!',
                '',
                response,
                payload,
                new_headers,
                response_code=404,
                status_code=404,
                reference='',
                transaction_id=payment_trx_obj.id,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(404, 'Paid Bill', 'Paid Bill', custom_response=response)
        
        vals = {'reference_number': referenceNo}
        detail_info = f'partnerServiceId: {partnerServiceId}\n'
        detail_info += f'customerNo: {customerNo}\n'
        detail_info += f'virtualAccountNo: {virtualAccountNo}\n'
        if virtualAccountName:
            detail_info += f'virtualAccountName: {str(virtualAccountName)}\n'
        detail_info += f'paymentRequestId: {paymentRequestId}\n'
        if channelCode:
            detail_info += f'channelCode: {str(channelCode)}\n'
        if hashedSourceAccountNo:
            detail_info += f'hashedSourceAccountNo: {str(hashedSourceAccountNo)}\n'
        if sourceBankCode:
            detail_info += f'sourceBankCode: {str(sourceBankCode)}\n'
        detail_info += f'paidAmount: {str(paidAmount)}\n'
        if referenceNo:
            detail_info += f'referenceNo: {str(referenceNo)}\n'
        if flagAdvise:
            detail_info += f'flagAdvise: {str(flagAdvise)}\n'
        if subCompany:
            detail_info += f'subCompany: {str(subCompany)}\n'
        if billDetails:
            detail_info += f'billDetails: {str(billDetails)}\n'
        if additionalInfo:
            detail_info += f'additionalInfo: {str(additionalInfo)}\n'
        vals['detail_info'] = detail_info

        # * check to make sure is already full paid or not
        is_paid = False
        if float(paidAmount.get('value')) == float(payment_trx_obj.amount):
            is_paid = True
        else:
            # * Invalid Amount
            response = {
                'responseCode': '4042513',
                'responseMessage': 'Invalid Amount',
                'virtualAccountData': virtual_account_data_response,
                'additionalInfo': {}
            }
            _log.sudo().create_api_log(
                name,
                url,
                f'Trx VA {customerNo} has invalid Amount (different paid amount and total amount that must be paid)!',
                '',
                response,
                payload,
                new_headers,
                response_code=404,
                status_code=404,
                reference='',
                transaction_id=payment_trx_obj.id,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(404, 'Invalid Amount', 'Invalid Amount', custom_response=response)

        response = {
            'responseCode': '2002500',
            'responseMessage': 'Successful',
            'virtualAccountData': virtual_account_data_response,
            'additionalInfo': {}
        }
        if is_inconsistent_req:
            virtual_account_data_response.update({
                'paymentFlagStatus': '00',
                'paymentFlagReason': {
                    'english': 'Success',
                    'indonesia': 'Sukses'
                }
            })
            response.update({
                'responseCode': '4042518',
                'responseMessage': 'Inconsistent Request'
            })
        elif is_duplicate_x_external_id:
            virtual_account_data_response.get('paymentFlagReason').update({
                'indonesia': 'Tidak bisa menggunakan X-EXTERNAL-ID yang sama',
                'english': 'Cannot use the same X-EXTERNAL-ID'
            })
            response.update({
                'responseMessage': 'Conflict'
            })
        else:
            if is_paid:
                transaction_date = (parser.parse(trxDateTime) - relativedelta(hours=7)).replace(tzinfo=None)
                vals.update({
                    'reason': 'Success',
                    'transaction_status': '1',
                    'transaction_date': transaction_date,
                    'state': 'done'
                })

            # * update va obj
            payment_trx_obj.suspend_security().write(vals)

            # * get trx obj
            trx_obj = request.env['tw.account.payment'].sudo().search([
                ('name','=',payment_trx_obj.reference)
            ], limit=1)
            if trx_obj:
                if is_paid and payment_trx_obj.state == 'done':
                    trx_obj.action_auto_post_api_payment()

                virtual_account_data_response.update({
                    'paymentFlagStatus': '00',
                    'paymentFlagReason': {
                        'english': 'Success',
                        'indonesia': 'Sukses'
                    }
                })
                if virtual_account_data_response.get('billDetails'):
                    virtual_account_data_response['billDetails'][0].update({
                        'status': '00',
                        'reason': {
                            'english': 'Success',
                            'indonesia': 'Sukses'
                        }
                    })

        if is_inconsistent_req:
            _log.sudo().create_api_log(
                name,
                url,
                'Failed Notification Update API Payment Trx VA BCA because duplicate X-EXTERNAL-ID & paymentRequestId (Inconsistent Request)!',
                '',
                response,
                payload,
                new_headers,
                response_code=404,
                status_code=404,
                reference='',
                transaction_id=payment_trx_obj.id,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(404, 'Inconsistent Request', 'Inconsistent Request', custom_response=response)
        elif is_duplicate_x_external_id:
            _log.sudo().create_api_log(
                name,
                url,
                'Failed Notification Update API Payment Trx VA BCA because duplicate X-EXTERNAL-ID (Conflict)!',
                '',
                response,
                payload,
                new_headers,
                response_code=409,
                status_code=409,
                reference='',
                transaction_id=payment_trx_obj.id,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return invalid_response_api(409, 'Conflict', 'Conflict', custom_response=response)
        else:
            _log.sudo().create_api_log(
                name,
                url,
                'Success Notification Update API Payment Trx VA BCA',
                '',
                response,
                payload,
                new_headers,
                response_code=200,
                status_code=200,
                reference='',
                transaction_id=payment_trx_obj.id,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )
            return valid_response_api(200, response)