#!/usr/bin/python#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
import functools
import werkzeug.wrappers
try:
    import simplejson as json
except ImportError:
    import json
import logging
_logger = logging.getLogger(__name__)
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta
# 2: import of known third party lib
try:
    from packaging import version as parse_version
except ImportError:
    from odoo.tools import parse_version as parse_version

# 3:  imports of odoo
import odoo
from odoo import models, fields, api, _
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request
from odoo.http import Response
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError

# Import from local main.py controller
from odoo.addons.tw_popeye.controllers.main import check_valid_token, valid_response, invalid_response

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.INFO)

class ControllerREST(http.Controller):
    @http.route('/api/popeye/v1/payment_status', methods=['POST'], type='json', auth='none', csrf=False, json_rpc=False)
    @check_valid_token
    def post_payment_status(self, **post):
        teds_api_log = request.env['teds.api.log']
        url = '/api/popeye/v1/payment_status'
        name = 'Get Popeye Status'
        request_time = datetime.now()

        post = json.loads(request.httprequest.get_data(as_text=True))
        if 'transactions' not in post:
            return invalid_response(200, 'Bad Request', 'Parameter "transactions" tidak boleh kosong!')

        data = post.get('transactions')
        response = []
        for transaction in data:
            try:
                transaction_no = transaction.get('transaction_no', None)
                transaction_status = transaction.get('transaction_status', None)
                message = transaction.get('message', '')
                if not transaction_no or not transaction_status:
                    response.append({'transaction_no': transaction.get('transaction_no'),'status': 0,'message': 'Parameter "transaction_no" dan "transaction_status" tidak boleh kosong!'})
                    continue
                if transaction_status not in ['verifying','on_approval','queuing','paid','reject']:
                    response.append({'transaction_no': transaction.get('transaction_no'),'status': 0,'message': 'Status yg didapat dari popeye tidak sesuai (%s)' %transaction_status})
                    continue
                
                # Check if transaction type is correct
                transaction_type = transaction_no[0:2]
                if transaction_type == 'PV':
                    transaction_obj = request.env['tw.account.payment'].sudo().search([('name','=',transaction_no)],limit=1)
                elif transaction_type == 'BT':
                    transaction_obj = request.env['tw.bank.transfer'].sudo().search([('name','=',transaction_no)],limit=1)
                else:
                    response.append({'transaction_no': transaction.get('transaction_no'),'status': 0,'message': 'Tipe transaksi (%s) tidak dikenali' %transaction_type})
                    continue

                if not transaction_obj:
                    response.append({'transaction_no':transaction_no,'status': 0,'message': 'Voucher %s not found!'%transaction_no})
                    continue
                
                if transaction_obj.state not in ('wfp','approved'):
                    response.append({'transaction_no':transaction_no,'status': 0,'message': 'Status voucher %s sudah bukan Waiting for Payment. Status Voucher sudah %s!'%(transaction_no,transaction_obj.state)})
                    continue
                elif transaction_obj.state == 'approved':
                    response.append({'transaction_no':transaction_no,'status': 1,'message': 'Status voucher %s sudah Paid!'%(transaction_no)})
                    continue
                
                if transaction_obj.status_api_payment == transaction_status:
                    response.append({'transaction_no':transaction_no,'status': 1,'message': 'Status voucher %s sudah %s.!'%(transaction_no,transaction_status)})
                    continue
                try:
                    transaction_obj._update_status_from_popeye(transaction_status,message)
                    response.append({'transaction_no':transaction_no,'status': 1,'message': 'Success'})
                    continue
                except Exception as e:
                    request._cr.rollback()
                    response.append({'transaction_no':transaction_no,'status': 0,'message': str(e)})
            except Exception as e:
                    request._cr.rollback()
                    response_time = datetime.now()
                    teds_api_log.sudo().create_log_api(name,e,False,url,request_time,response_time,'teds_api_popeye','teds.api.popeye')
                    return valid_response(200,response)
        
        response_time = datetime.now()
        teds_api_log.sudo().create_log_api(name,response,True,url,request_time,response_time,'teds_api_popeye','teds.api.popeye')
        
        return valid_response(200, response)