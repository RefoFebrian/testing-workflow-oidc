#-*- coding: utf-8 -*-

# 1: imports of python lib
import base64
import json
try:
    import simplejson as json
except ImportError:
    import json

from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib
from odoo.addons.rest_api.controllers.main import *
from odoo.addons.tw_b2b_api.controllers.main import check_ahm_ev_valid_token,invalid_response_json,valid_response_json,start_end_date_request

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request
from odoo.http import Response
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

# 5: local imports

# 6: Import of unknown third party lib
import logging
_logger = logging.getLogger(__name__)

class ControllerREST(http.Controller):
    def _validate_api_request(self, data, mandatory_fields, end_point, request_and_response_datetime):
        """Validate API request data"""
        # Handle both single list and tuple of lists
        if isinstance(mandatory_fields, tuple):
            # For main request fields
            main_fields = mandatory_fields[0]
            fields = [field for field in main_fields if field not in data.keys()]
            if fields:
                message = f"Mandatory request in body {str(fields)}!"
                _logger.error(message)
                return invalid_response_json(
                    401, 'API POST ACC EV', message, [], True, end_point, 
                    request_and_response_datetime, 'post', data, 
                    'incoming', request_and_response_datetime
                )
        elif isinstance(mandatory_fields, list):
            # For acc item fields
            fields = [field for field in mandatory_fields if field not in data.keys()]
            if fields:
                message = f"Mandatory request in body {str(fields)}!"
                _logger.error(message)
                return invalid_response_json(
                    401, 'API POST ACC EV', message, [], True, end_point, 
                    request_and_response_datetime, 'post', data, 
                    'incoming', request_and_response_datetime
                )
        return None

    def _process_api(self, acc_type, mandatory_fields, end_point, request_and_response_datetime, data):
        """Process API request"""
        res = []
        validation_error = self._validate_api_request(data, mandatory_fields, end_point, request_and_response_datetime)
        if validation_error:
            return validation_error

        mdCode = data.get('mdCode').upper()
        if mdCode not in ['H2Z', 'G5Z']:
            message = f"MD code must be 'H2Z' or 'G5Z' not '{mdCode}'!"
            _logger.error(message)
            return invalid_response_json(
                401, 'API POST ACC EV', message, [], True, end_point, 
                request_and_response_datetime, 'post', data, 
                'incoming', request_and_response_datetime
            )

        company_obj = request.env['res.company'].sudo().search([('atpm_code', '=', mdCode)], limit=1)
        if not company_obj:
            message = f"Main Dealer with ATPM Code '{mdCode}' is not found!"
            _logger.error(message)
            return invalid_response_json(
                401, 'API POST ACC EV', message, [], True, end_point, 
                request_and_response_datetime, 'post', data, 
                'incoming', request_and_response_datetime
            )

        b2b_api_ev_vals = {
            'company_id': company_obj.id,
            'ship_list_number': str(data.get('slNo')) if data.get('slNo') else False,
            'ship_list_date': data.get('slDate'),
            'md_code': mdCode,
            'voucher_acc': str(data.get('voucherAccNo')) if data.get('voucherAccNo') else False,
            'packing_number': str(data.get('packingNo')) if data.get('packingNo') else False,
            'hit_api_date': datetime.now(),
            'jenis_acc': acc_type
        }

        b2b_api_ev_obj = request.env['tw.b2b.api.ev'].sudo().search([('ship_list_number', '=', data.get('slNo'))], limit=1)
        if b2b_api_ev_obj:
            b2b_api_ev_vals['state'] = 'duplicate'
        b2b_api_ev_obj = request.env['tw.b2b.api.ev'].sudo().create(b2b_api_ev_vals)

        for rec in data.get('acc', []):
            acc_mandatory_fields = mandatory_fields[1] if isinstance(mandatory_fields, tuple) else mandatory_fields
            validation_error = self._validate_api_request(rec, acc_mandatory_fields, end_point, request_and_response_datetime)
            if validation_error:
                return validation_error

            accType = rec.get('accType')
            if accType == 'B':
                accType = 'EVBT'
            elif accType == 'C':
                accType = 'EVCH'

            b2b_api_ev_line_vals = {
                'b2b_api_ev_id': b2b_api_ev_obj.id,
                'serial_number': rec.get('serialNo'),
                'type_acc': accType,
                'part_code': rec.get('partNo'),
                'part_desc': rec.get('partDesc'),
                'box_number': rec.get('boxNo'),
                'carton_number': rec.get('cartonNo')
            }

            b2b_api_ev_line_obj = request.env['tw.b2b.api.ev.line'].sudo().search([
                ('serial_number', '=', rec.get('serialNo'))
            ], limit=1)
            if not b2b_api_ev_line_obj:
                b2b_api_ev_line_obj = request.env['tw.b2b.api.ev.line'].sudo().create(b2b_api_ev_line_vals)

            res.append({
                'serialNo': rec.get('serialNo'),
                'accepted': 'Y'
            })

        response = {
            'result': 'full_accept',
            'acc': res
        }
        return valid_response_json(
            200, 'API POST ACC EV', 'full_accept', response, True, end_point,
            request_and_response_datetime, 'post', data,
            'incoming', request_and_response_datetime
        )

    @http.route('/mdms/AHMSDEVE/v1.0/accoem/add', methods=['POST'], type='json', auth='none', csrf=False)
    @check_ahm_ev_valid_token
    def tw_b2b_api_ev_acc_oem(self, **post):
        """Handle OEM API request"""
        try:
            post = json.loads(request.httprequest.get_data(as_text=True))
            end_point = str(request.httprequest.url)
            request_and_response_datetime = start_end_date_request()
            mandatory_fields = (
                ['slNo', 'slDate', 'mdCode', 'acc'],
                ['accType', 'partNo', 'partDesc', 'serialNo']
            )
            return self._process_api('OEM', mandatory_fields, end_point, request_and_response_datetime, post)
        except Exception as e:
            message = f'Error Exception - {str(e)}'
            _logger.error(message)
            return invalid_response_json(
                401, 'API POST ACC EV', message, [], True, end_point,
                request_and_response_datetime, 'post', post,
                'incoming', request_and_response_datetime
            )

    @http.route('/mdms/AHMSDEVE/v1.0/accrem/add', methods=['POST'], type='json', auth='none', csrf=False)
    @check_ahm_ev_valid_token
    def tw_b2b_api_ev_acc_rem(self, **post):
        """Handle REM API request"""
        try:
            post = json.loads(request.httprequest.get_data(as_text=True))
            end_point = str(request.httprequest.url)
            request_and_response_datetime = start_end_date_request()
            mandatory_fields = (
                ['slNo', 'slDate', 'mdCode', 'acc'],
                ['packingNo', 'cartonNo', 'accType', 'partNo', 'serialNo']
            )
            return self._process_api('REM', mandatory_fields, end_point, request_and_response_datetime, post)
        except Exception as e:
            message = f'Error Exception - {str(e)}'
            _logger.error(message)
            return invalid_response_json(
                401, 'API POST ACC EV', message, [], True, end_point,
                request_and_response_datetime, 'post', post,
                'incoming', request_and_response_datetime
            )


