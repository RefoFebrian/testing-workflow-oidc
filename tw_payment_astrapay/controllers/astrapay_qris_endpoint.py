# 1: imports of python lib
import json
import requests
import hashlib
import hmac
import base64
import io
import qrcode
import random
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
    @http.route('/api/ext/snap/v1.0/access-token/b2b', methods=['POST'], type='json', auth='public', csrf=False, json_rpc=False)
    def _qr_dynamic_token_astrapay(self, **kwargs):
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
        name = 'AstraPay Qris Token'
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
            }, expired_time=900)

            response = {
                'responseCode': '2007300',
                'responseMessage': 'Successful',
                'accessToken': token_obj.get('token').decode('utf-8') if not isinstance(token_obj.get('token'), str) else token_obj.get('token'),
                'tokenType': 'bearer',
                'expiresIn': 900
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
        
    @http.route('/api/ext/snap/v1.0/qr/qr-mpm-notify', methods=['POST'], type='json', auth='public', csrf=False, json_rpc=False)
    @verify_token
    def _qr_dynamic_mpm_notify_astrapay(self, **kwargs):
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

        name = 'AstraPay Qris Notification'
        url = request.httprequest.url
        
        request_type = 'post'
        method_obj = request.env['tw.selection'].sudo().get_selection('ApiMethod', value=request_type)
        model_obj = request.env['ir.model'].sudo().search([('model','=','payment.transaction')], limit=1)
        today = datetime.now().date()
        
        payload = request.httprequest.json
        minified_request_body = json.dumps(payload, separators=(',', ':')) # Minify the JSON string
        
        partner_model = request.env['res.partner']
        client_obj = request.env['res.users'].sudo().browse(request.session.uid)
        if not client_obj:
            response = {
                'responseCode': '4017300',
                'responseMessage': 'Unauthorized client'
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
            return invalid_response_api(401, 'Unauthorized client', 'Unauthorized client', custom_response=response)
        
        api_config_obj = request.env['tw.api.configuration'].sudo()._get_config_bank_by_name(client_obj.partner_id.code, is_api_payment=True, additional_domain=[('partner_id','=',client_obj.partner_id.id)])
        qris_setting_api_payment_obj = request.env['tw.setting.api.payment'].sudo().search([
            ('payment_usage','=','qris'),
            ('provider_id','=',client_obj.partner_id.sudo().id)
        ], limit=1)
        if qris_setting_api_payment_obj:
            if channel_id != qris_setting_api_payment_obj.channel_id:
                response = {
                    'responseCode': '4015200',
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
            
            x_partner_id_notify = qris_setting_api_payment_obj.x_partner_id_notify or '000885000002089'
            if x_partner_id != x_partner_id_notify:
                response = {
                    'responseCode': '4015200',
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
        
        relative_url = request.httprequest.path
        sha256_hash = hashlib.sha256(minified_request_body.encode('utf-8')).hexdigest()
        body = sha256_hash.lower() # HexEncode the SHA-256 hash
        try:
            # verify client signature
            relative_url = relative_url.split('/api/ext/snap')[1]
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
                raise Warning('Invalid Signature QRIS Notify AstraPay!')
        except Exception as err:
            logging.error(err)
            response = {
                'responseCode': '4015200',
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
            filter_value = '%'+'"X-EXTERNAL-ID": "{x_external_id}"'.format(x_external_id=x_external_id)+'%'
            filter_log_name = 'AstraPay'
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
        originalReferenceNo = data.get('originalReferenceNo')
        latestTransactionStatus = data.get('latestTransactionStatus')
        transactionStatusDesc = data.get('transactionStatusDesc').split()[0].lower()
        if transactionStatusDesc == 'success':
            transactionStatusDesc = 'Successfully'
        state = STATE_MAPPING.get(transactionStatusDesc) or STATE_MAPPING.get(transactionStatusDesc.lower())
        transaction_status = STATE_CODE_MAPPING.get(latestTransactionStatus)
        vals = {
            'state': state,
            'transaction_status': transaction_status,
            'payer_name': data.get('destinationAccountName'),
            'payer_phone_number': data.get('customerNumber'),
            'amount': data.get('value'),
            'currency_code': data.get('currency'),
            'batch_number': data.get('sessionID'),
            'terminal_id': data.get('externalStoreID'),
            'issuer_reference_number': data.get('issuerRrn'),
            'issuer_name': data.get('issuerName'),
        }

        # * adjust state
        if vals.get('state') == 'declined':
            vals['state'] = 'cancel'
        elif vals.get('state') == 'invalid':
            vals['state'] = 'error'
        elif vals.get('state') == 'unpaid':
            vals['state'] = 'pending'
        elif vals.get('state') == 'paid':
            vals['state'] = 'done'
        elif not vals.get('state'):
            vals['state'] = 'error'

        if not vals.get('amount') and data.get('amount'):
            vals['amount'] = data.get('amount').get('value')
        if not vals.get('currency_code') and data.get('amount'):
            vals['currency_code'] = data.get('amount').get('currency')
        if data.get('additionalInfo'):
            if data.get('additionalInfo').get('transactionDate'):
                vals['transaction_date'] = parser.parse(data.get('additionalInfo').get('transactionDate'))
            if not vals.get('issuer_reference_number') and data.get('additionalInfo').get('issuerReferenceNumber'):
                vals['issuer_reference_number'] = data.get('additionalInfo').get('issuerReferenceNumber')
            if not vals.get('issuer_name') and data.get('additionalInfo').get('issuerName'):
                vals['issuer_name'] = data.get('additionalInfo').get('issuerName')
            if data.get('additionalInfo').get('acquirerName'):
                vals['acquirer_name'] = data.get('additionalInfo').get('acquirerName')

            add_info = 'tip: {tip}\ndeviceId: {deviceId}\nchannel: {channel}\ngracePeriod: {gracePeriod}\nterminalId: {terminalId}\nuserName: {userName}\nmerchantPan: {merchantPan}\ncustomerPan: {customerPan}\nissuerName: {issuerName}\ntransactionId: {transactionId}'.format(
                tip=data.get('additionalInfo').get('tip', '0.00'),
                deviceId=data.get('additionalInfo').get('deviceId', ''),
                channel=data.get('additionalInfo').get('channel', ''),
                gracePeriod=str(data.get('additionalInfo').get('gracePeriod')) if data.get('additionalInfo').get('gracePeriod') else '0',
                terminalId=data.get('additionalInfo').get('terminalId', ''),
                userName=data.get('additionalInfo').get('userName', ''),
                merchantPan=data.get('additionalInfo').get('merchantPan', ''),
                customerPan=data.get('additionalInfo').get('customerPan', ''),
                issuerName=data.get('additionalInfo').get('issuerName', ''),
                transactionId=data.get('additionalInfo').get('transactionId', '')
            )
            vals['additional_info'] = add_info
        
        # TODO: sementara, untuk testing callback saja di server tes. hapus nanti
        conf_params_obj = request.env['ir.config_parameter'].sudo().get_param('tw_payment_astrapay.dummy_data_callback')
        if conf_params_obj:
            conf_params_obj = eval(conf_params_obj)
            originalReferenceNo = conf_params_obj.get('original_reference_no')
            vals['amount'] = conf_params_obj.get('amount')
        payment_trx_model = request.env['payment.transaction']
        payment_trx_obj = payment_trx_model.suspend_security().search([('reference_number','=',originalReferenceNo)], limit=1)
        if not payment_trx_obj:
            if is_duplicate_x_external_id:
                response = {
                    'responseCode': '4095200',
                    'responseMessage': 'Conflict'
                }
                _log.sudo().create_api_log(
                    name,
                    url,
                    f'Trx API Payment QRIS AstraPay {originalReferenceNo} not found and duplicate X-EXTERNAL-ID!',
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
                'responseMessage': 'Invalid Bill/QRIS data [Not Found]'
            }
            _log.sudo().create_api_log(
                name,
                url,
                f'Trx API Payment QRIS AstraPay {originalReferenceNo} not found!',
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
            return invalid_response_api(404, 'Invalid Bill/QRIS data [Not Found]', 'Invalid Bill/QRIS data [Not Found]', custom_response=response)

        detail_info = payment_trx_obj.detail_info + '\n' if payment_trx_obj.detail_info else '\n'
        detail_info += f"originalPartnerReferenceNo: {data.get('originalPartnerReferenceNo')}\n"
        detail_info += f"accountType: {data.get('accountType')}\n"
        detail_info += f"reffId: {data.get('reffId')}\n"
        detail_info += f"bankCode: {data.get('bankCode')}\n"
        detail_info += f"destinationNumber: {data.get('destinationNumber')}\n"
        detail_info += f"destinationAccountName: {data.get('destinationAccountName')}"
        vals['detail_info'] = detail_info
                            
        try:
            if payment_trx_obj:
                payment_trx_obj.suspend_security().write(vals)
            else:
                vals['transaction_keys'] =  originalReferenceNo
                payment_trx_obj = payment_trx_model.suspend_security().create(vals)
        except Exception as err:
            logging.error(f'\nerr:\t {err}')
            detail_err = f'Failed QR MPM Notify with detail error:\n{err}'
            _log.sudo().create_api_log(
                name,
                url,
                detail_err,
                '',
                {},
                payload,
                new_headers,
                response_code=400,
                status_code=400,
                reference='',
                transaction_id=payment_trx_obj.id,
                api_type_id=api_config_obj.api_type_id.id if api_config_obj and api_config_obj.api_type_id else False,
                method_id=method_obj.id if method_obj else False,
                model_id=model_obj.id if model_obj else False
            )

        response = {
            'responseCode': '2005200',
            'responseMessage': 'Successful',
            'additionalInfo': {
                'tip': data.get('additionalInfo').get('tip', '0.00')
            }
        }

        if is_duplicate_x_external_id:
            response.update({
                'responseCode': '4095200',
                'responseMessage': 'Conflict',
            })
            _log.sudo().create_api_log(
                name,
                url,
                'Duplicate X-EXTERNAL-ID',
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
        
        if response.get('responseCode') == '2005200' and payment_trx_obj.state == 'done':
            transaction_obj = request.env['tw.account.payment'].sudo().search([
                ('name','=',payment_trx_obj.reference)
            ], limit=1)
            if transaction_obj and transaction_obj.state != 'paid':
                transaction_obj.action_auto_post_api_payment()

        _log.sudo().create_api_log(
            name,
            url,
            'Success Notification Update API Payment QRIS AstraPay',
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