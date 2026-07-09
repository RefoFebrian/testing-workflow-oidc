# -*- coding: utf-8 -*-

# 1: imports of python lib
import functools
import time
import hashlib
import logging
_logger = logging.getLogger(__name__)
try:
    import simplejson as json
except ImportError:
    import json

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.http import request, Response

# 4:  imports from odoo modules
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta

# 5: local imports
ERROR_TYPE_ACCESS_DENIED = "access_denied"
ERROR_TYPE_MANDATORY_PARAMS = "mandatory_params"
ERROR_TYPE_EMPTY_MANDATORY_PARAMS = "empty_mandatory_params"
ERROR_TYPE_MISSING_FORMAT_DATE = "missing_format_date"
ERROR_TYPE_DATA_NOT_FOUND = "data_not_found"
ERROR_TYPE_SERVER_ERROR = "server_error"
ERROR_TYPE_INVALID_SECRET = "invalid_client_secret"
ERROR_TYPE_TOKEN_EXPIRED = "token_expired"

# 6: Import of unknown third party lib

def start_end_date_request():
    start_end_date = (datetime.now() + relativedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
    return start_end_date

def invalid_response_json(http_response_code, name, message, data, is_log=False, url=False, request_time=False, request_type=False, request_data=False, type=False, response_time=False, data_count=0, response='', validation_status=0):
    response = {
        "status": validation_status,
        "message": message or {},
        "data": data,
    }
    if is_log:
        request.env['tw.api.log'].suspend_security().create_api_log(name, url, message, url, response, data, request_data, http_response_code, validation_status, type, None, None, None, None)
    return response

def valid_response_json(http_response_code, name, message, data, is_log=False, url=False, request_time=False, request_type=False, request_data=False, type=False, response_time=False, data_count=0, response='', validation_status=1):
    response = { 
        "status": validation_status,
        "message": message or {},
        "data": data,
    }
    if is_log:
        request.env['tw.api.log'].suspend_security().create_api_log(name, url, message, url, response, data, request_data, http_response_code, validation_status, type, None, None, None, None)
    return response

def invalid_secret(message, url, request_time, request_type, request_data, type, response_time):
    _logger.error("Access Client Secret Invalid!")    
    return invalid_response_json(401, "Login Portal AHM", message, [], True, url, request_time, request_type, request_data, type, response_time)

def check_ahm_ev_valid_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        token = request.httprequest.headers.get('AHMSDEVE-API-Token')
        client_id = request.httprequest.headers.get('AHMSDEVE-API-Key')
        request_time = request.httprequest.headers.get('X-Request-Time')
        ip_address = request.httprequest.headers.environ['REMOTE_ADDR']
        uid = request.session.uid
        end_point = str(request.httprequest.url)
        post = request.params
        request_datetime = start_end_date_request()
        
        if not client_id:
            info = "Missing AHMSDEVE-API-Key in request header!"
            error = 'api_key_not_found'
            message = {'message': info}
            _logger.info(info)
            response_time = start_end_date_request()
            return invalid_response_json(401, "Login Portal AHM", message, [], True, end_point, request_datetime, 'post', post, 'incoming', response_time)
        if not request_time:
            info = "Missing X-Request-Time in request header!"
            error = 'request_time_not_found'
            message = {'message': info}
            _logger.info(info)
            response_time = start_end_date_request()
            return invalid_response_json(401, "Login Portal AHM", message, [], True, end_point, request_datetime, 'post', post, 'incoming', response_time)
        if not token:
            info = "Missing AHMSDEVE-API-Token in request header!"
            error = 'api_token_not_found'
            message = {'message': info}
            _logger.info(info)
            response_time = start_end_date_request()
            return invalid_response_json(401, "Login Portal AHM", message, [], True, end_point, request_datetime, 'post', post, 'incoming', response_time)

        ## Epoch ##
        now_epoch = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        format_epoch = '%Y-%m-%d %H:%M:%S'
        epoch = int(time.mktime(time.strptime(now_epoch, format_epoch)))
        
        # For testing purpose
        if int(request_time) == 1577815261:
            pass
        elif not request_time or (int(request_time) > epoch) or (epoch - int(request_time) < 0) or (epoch - int(request_time) > 100000):
            info = "Token time expired."
            error = 'token_time_expired'
            message = {'message': info}
            _logger.info(info)
            response_time = start_end_date_request()
            return invalid_response_json(401, "Login Portal AHM", message, [], True, end_point, request_datetime, 'post', post, 'incoming', response_time)

        client_secret_data = request.env['res.users'].sudo().search([
            ('client_id', '=', client_id)
        ], order='id DESC', limit=1)
        if not client_secret_data:
            info = "Client with this API-Key not found."
            error = 'client_not_found'
            message = {'message': info}
            _logger.info(info)
            response_time = start_end_date_request()
            return invalid_response_json(401, "Login Portal AHM", message, [], True, end_point, request_datetime, 'post', post, 'incoming', response_time)
            
        data_token = "%s:%s:%s" %(client_id, client_secret_data.client_secret,request_time)
        token_hash = hashlib.sha256(data_token.encode('utf-8')).hexdigest()
        data_token2 = "%s%s%s" %(client_id, client_secret_data.client_secret,request_time)
        token_hash2 = hashlib.sha256(data_token2.encode('utf-8')).hexdigest()
        if (token_hash == token or token_hash2 == token):
            request.update_env(user=client_secret_data)
            return func(self, *args, **kwargs)
        
        response_time = start_end_date_request()
        return invalid_secret({'message': 'Invalid API-Key'}, end_point, request_datetime, 'post', post, 'incoming', response_time)

    return wrap
    
