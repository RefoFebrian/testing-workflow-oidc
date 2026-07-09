# Part of Flectra. See LICENSE file for full copyright and licensing details.
import logging
import functools
import odoo
import json
from dateutil.relativedelta import relativedelta
from odoo import http
from odoo.http import request
from odoo import fields
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

def invalid_token(info):
    return invalid_response(400, "Bad Authentication "+info, info)

def check_valid_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token = request.httprequest.headers.get('Authorization')
        ip_address = request.httprequest.headers.environ['REMOTE_ADDR']
        
        if not access_token:
            info = "Missing access token in request header!"
            return invalid_response(400, "Bad Authentication",info)

        access_token = access_token[7:]  # Remove "Bearer " prefix
        
        # Search using res.users.apikeys (Odoo 18)
        api_key = request.env['res.users.apikeys'].sudo().search(
            [('key', '=', access_token)], limit=1)

        if not api_key:
            info = "Access Token Invalid!"
            return invalid_token(info)
        
        # Check if key is still valid (not expired or revoked)
        if not api_key.user_id:
            info = "Access Token Invalid - No user associated!"
            return invalid_token(info)

        request.session.uid = api_key.user_id.id
        request.uid = api_key.user_id.id
        return func(self, *args, **kwargs)

    return wrap


def valid_response(code, data, message='Success'):
    response = {
        'status': 1,
        'message': message,
        'code': code,
        'data': data
    }
    return response

def invalid_response(code, data, info, message=None):
    if not message:
        message = 'Failed'
    if 'opt' in str(info) or 'syntax' in str(info):
        info = 'Error !, Please contact administrator if you think this is a mistake.'
    response = {
        'status': 0,
        'message': message,
        'code': code,
        'data': data
    }
    return response


class ControllerREST(http.Controller):
    @http.route(['/api/popeye/auth/get_tokens'], methods=['POST'], type='json', auth='none', csrf=False)
    def api_auth_gettokens(self, **post):
        post = json.loads(request.httprequest.get_data(as_text=True))
        client_id = post.get('client_id')
        client_secret = post.get('client_secret')

        # Validation
        if not client_id or not client_secret:
            info = "Empty value of 'client_id' or 'client_secret'!"
            return invalid_response(400, "Bad Authentication", info)

        try:
            # Search for user with matching credentials
            user = request.env['res.users'].sudo().search([
                ('client_id', '=', client_id), 
                ('client_secret', '=', client_secret)
            ], limit=1)
            
            if not user:
                info = "Invalid Client Id or Client Secret!"
                return invalid_response(400, "Bad Authentication", info)
            
            uid = user.id

        except Exception as e:
            info = f"Authentication error: {str(e)}"
            _logger.error(f"Auth error: {info}")
            return invalid_response(400, "Bad Authentication", info)

        if not uid:
            info = "Odoo User authentication failed!"
            return invalid_response(400, "Bad Authentication", info)

        # Generate API Key using Odoo 18's res.users.apikeys
        try:
            # Use the custom _get_access_token method from res.users.apikeys
            api_key = request.env['res.users.apikeys'].sudo()._get_access_token(
                user_id=uid, 
                create=True
            )
            
            if api_key:
                # Successfully generated or retrieved token
                # Set expiration to 365 days from now
                expired_on = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d %H:%M:%S')
            else:
                raise Exception("Failed to generate API key")

        except Exception as e:
            _logger.error(f"Error generating API key: {str(e)}")
            info = f"Failed to generate API token: {str(e)}"
            return invalid_response(500, "Server Error", info)

        # Successful response
        return {
            "Status": 1, 
            "Message": "Successfull",
            "code": "SCS",
            "Data": {
                'token': str(api_key),
                "grant_type": "client_credentials",
                "expired_on": expired_on,
            } 
        }
