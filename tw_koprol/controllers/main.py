#!/usr/bin/python
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

from odoo.addons.rest_api.rest_exception import invalid_response
from odoo.addons.rest_api.controllers.main import check_valid_token, valid_response
# 3:  imports of odoo
import odoo
from odoo import models, fields, api, _
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request
from odoo.http import Response
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
    
PREFIX = 'Bearer'

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode("utf-8")
        return json.JSONEncoder.default(self, obj)

def get_token_from_bearer(header):
    bearer, _, token = header.partition(' ')
    if bearer != PREFIX:
        return '__Invalid Token'
    return token
    
def check_valid_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token = get_token_from_bearer(request.httprequest.headers['Authorization']) if 'Authorization' in request.httprequest.headers else False
        if not access_token:
            info = "Missing access token in request header!"
            error = 'access_token_not_found'
            _logger.error(info)
            return invalid_response(401, error, info)
        
        access_token_data = request.env['res.users.apikeys'].sudo().search(
            [('token', '=', access_token)], order='id DESC', limit=1)

        if access_token_data._get_access_token(user_id=access_token_data.user_id.id) != access_token:
            if access_token_data._get_access_token_google(user_id=access_token_data.user_id.id) != access_token:
                _logger.error("Token is expired or invalid!")
                return invalid_response(401, 'invalid_token', "Token is expired or invalid!")
            else:
                request.session.uid = access_token_data.user_id.id
                request.uid = access_token_data.user_id.id
                request.company_ids = access_token_data.user_id.company_ids
                return func(self, *args, **kwargs)

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        request.company_ids = access_token_data.user_id.company_ids

        return func(self, *args, **kwargs)

    return wrap
    
def create_api_log(name,type_hit,url,request_type,request_data,response_code,response_data):
    request.env['tw.api.log'].sudo().create({
        'name': name,
        'type': type_hit,
        'url': url,
        'request_type': request_type,
        'request': request_data,
        'response_code': response_code,
        'response': response_data,
    })

def valid_response(status, message, data, total_data=None, total_page=None, page=None):
    response = {
        "status": status,
        "code": 200,
        "message": message,
        "data": data,
    }

    if total_data:
        response.update({ "total_data": total_data })

    if total_page:
        response.update({ "total_page": total_page })

    if page:
        response.update({ "page": page })

    if request.httprequest.content_type == 'application/json':
        # request._json_response = JsonRequestPatch._json_response.__get__(request)
        return response

    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        response=json.dumps(response, cls=JSONEncoder),
    )

def invalid_response(status_code, message, detail_message):
    response = {
        'status': 'failed',
        'status_code': status_code,
        'message': message,
        'detail_message': detail_message
    }

    if request.httprequest.content_type == 'application/json':
        # request._json_response = JsonRequestPatch._json_response.__get__(request)
        return response

    return werkzeug.wrappers.Response(
        status='failed',
        content_type='application/json; charset=utf-8',
        response=json.dumps(response)
    )

def check_mandatory_fields(item,mandatory_field):
    fields = []
    detail_message = ''
    if item:
        for field in mandatory_field :
            if field not in item.keys():
                fields.append(field)
        if len(fields) > 0:
            detail_message = 'Fields ini tidak ada: %s' %(fields)

    return detail_message


def check_valid_token_azure(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        try:
            token = get_token_from_bearer(request.httprequest.headers['Authorization']) if 'Authorization' in request.httprequest.headers else False
            
            config_obj = self.env['tw.api.configuration'].sudo().search([
                ('name', '=', 'Koprol Integration'),
                ('code', '=', 'koprol')
            ], limit=1)
            if not config_obj:
                raise Warning('Configuration Koprol belum di setting !')
            
        
            tenant_id = config_obj.tenant_id
            client_id = config_obj.client_id
            openid_config_url = config_obj.open_id
            issuer = config_obj.issuer
            audience = config_obj.audience

            # Get the OpenID Configuration
            openid_config_url = openid_config_url if openid_config_url else 'https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid-configuration'.format(tenant_id=tenant_id)
            openid_config = requests.get(openid_config_url).json()

            # Get the JWKS (JSON Web Key Set)
            jwks_uri = openid_config['jwks_uri']
            jwks = requests.get(jwks_uri).json()

            # Get the signing keys
            rsa_keys = {}
            for key in jwks['keys']:
                key_json = json.dumps(key)
                rsa_key = RSAAlgorithm.from_jwk(key_json)
                rsa_keys[key['kid']] = rsa_key

            # Decode and validate the token
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = rsa_keys.get(unverified_header['kid'])

            if rsa_key is None:
                raise jwt.InvalidTokenError("Unable to find appropriate key")

            decoded = jwt.decode(
                token, 
                rsa_key, 
                algorithms=['RS256'], 
                audience= audience if audience else client_id,
                issuer= issuer if issuer else 'https://login.microsoftonline.com/{tenant_id}/v2.0'.format(tenant_id=tenant_id)
            )
            if decoded:
                # create session    
                uid = decoded.get('oid',False)
                check_user = request.env['res.users'].sudo().search([('oauth_uid','=',uid)],limit=1)
                if not check_user:
                    raise jwt.InvalidTokenError("Unable to find User Koprol in TEDS 2.0 with the Token !")
                request.session.uid = check_user.id 
                request.uid = check_user.id 

        except jwt.ExpiredSignatureError:
            print('Token has expired.')
            info = "Token has expired."
            error = 'access_token_not_found'
            _logger.error(info)
            return invalid_response_token(400, error, info)
        except jwt.InvalidTokenError as e:
            print('Invalid token: {e}'.format(e=e))
            info = 'Invalid token: {e}'.format(e=e)
            error = 'access_token_invalid'
            _logger.error(info)
            return invalid_response_token(400, error, info)
            
        return func(self, *args, **kwargs)
    return wrap%(check_good_receive.state)
