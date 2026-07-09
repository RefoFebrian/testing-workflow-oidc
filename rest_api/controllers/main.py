# Part of Flectra. See LICENSE file for full copyright and licensing details.

import functools
import hashlib
import os
import ast
import odoo
from odoo import http, fields
from odoo.http import request, Response
from odoo.exceptions import MissingError, AccessDenied
from odoo.tools.config import config
from datetime import date
from requests.structures import CaseInsensitiveDict
from ..rest_exception import *

_logger = logging.getLogger(__name__)

# Read OAuth2 constants and setup token store:
db_name = odoo.tools.config.get('db_name')
if not db_name:
    _logger.warning("Warning: To proper setup OAuth - it's necessary to "
                    "set the parameter 'db_name' in flectra config file!")

def _get_bulan():
    return str(date.today().month)

def _create_log(request, message, status_code):
    content = request.httprequest
    
    if str(status_code).startswith('2'):
        name = 'Success ,%s' % status_code
        _logger.info(message)
    elif str(status_code).startswith('3'):
        name = 'Redirect ,%s' % status_code
        _logger.warning(message)
    elif str(status_code).startswith('4'):
        name = 'Client Error ,%s' % status_code
        _logger.error(message)
    elif str(status_code).startswith('5'):
        name = 'Server Error ,%s' % status_code
        _logger.error(message)

    request.env['tw.api.log'].sudo().create({
        'name': name,
        'end_point': content.remote_addr,
        'method': content.method,
        'origin': content.url,
        'header': content.headers,
        'request': request.params,
        'status': status_code,
        # 'api_type': 'finco',
    })

def _give_response(request, status, message, data=None):
    # _create_log(request, message, status)
    content_type = request.httprequest.content_type.split(';')[0]
    
    if status == 200:
        response = { 'status':200, 'description':'Success', 'data':data }
        if content_type in ('message/http', 'multipart/form-data'):
            return valid_response(status, response)
        return response

    elif status == 400:
        Response.status = '400'
        response = { 'status':400, 'description':'Bad Request', 'message':message }
        if content_type in ('message/http', 'multipart/form-data'):
            return invalid_response(400, 'bad_request', response)
        return response

    elif status == 401:
        Response.status = '401'
        response = { 'status':401, 'description':'Unauthorized', 'message':message }
        if content_type in ('message/http', 'multipart/form-data'):
            return invalid_response(401, 'unauthorized', response)
        return response

    elif status == 404:
        Response.status = '404'
        response = { 'status':404, 'description':'Not Found', 'message':message }
        if content_type in ('message/http', 'multipart/form-data'):
            return invalid_response(404, 'not_found', response)
        return response

    elif status == 500:
        Response.status = '500'
        response = { 'status':500, 'description':'Internal Server Error', 'message':message }
        if content_type in ('message/http', 'multipart/form-data'):
            return invalid_response(500, 'internal_server_error', response)
        return response

def eval_json_to_data(modelname, json_data, create=True):
    Model = request.env[modelname]
    model_fiels = Model._fields
    field_name = [name for name, field in Model._fields.items()]
    values = {}
    for field in json_data:
        if field not in field_name:
            continue
        if field not in field_name:
            continue
        val = json_data[field]
        if not isinstance(val, list):
            values[field] = val
        else:
            values[field] = []
            if not create and isinstance(model_fiels[field], fields.Many2many):
                values[field].append((5,))
            for res in val:
                recored = {}
                for f in res:
                    recored[f] = res[f]
                if isinstance(model_fiels[field], fields.Many2many):
                    values[field].append((4, recored['id']))

                elif isinstance(model_fiels[field], odoo.fields.One2many):
                    if create:
                        values[field].append((0, 0, recored))
                    else:
                        if 'id' in recored:
                            id = recored['id']
                            del recored['id']
                            values[field].append((1, id, recored)) if len(recored) else values[field].append((2, id))
                        else:
                            values[field].append((0, 0, recored))
    return values


def object_read(model_name, params, status_code):
    domain = []
    fields = []
    offset = 0
    limit = None
    order = None
    if 'filters' in params:
        domain += ast.literal_eval(params['filters'])
    if 'field' in params:
        fields += ast.literal_eval(params['field'])
    if 'offset' in params:
        offset = int(params['offset'])
    if 'limit' in params:
        limit = int(params['limit'])
    if 'order' in params:
        order = params['order']

    data = request.env[model_name].search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)
    if data:
        return valid_response(status=status_code, data={
            'count': len(data),
            'results': data
        })
    else:
        return object_not_found_all(model_name)


def object_read_one(model_name, rec_id, params, status_code):
    fields = []
    if 'field' in params:
        fields += ast.literal_eval(params['field'])
    try:
        rec_id = int(rec_id)
    except Exception as e:
        rec_id = False

    if not rec_id:
        return invalid_object_id()
    data = request.env[model_name].search_read(domain=[('id', '=', rec_id)], fields=fields)
    if data:
        return valid_response(status=status_code, data=data)
    else:
        return object_not_found(rec_id, model_name)


def object_create_one(model_name, data, status_code):
    try:
        res = request.env[model_name].create(data)
    except Exception as e:
        return no_object_created(e)
    if res:
        return valid_response(status_code, {'id': res.id})


def object_update_one(model_name, rec_id, data, status_code):
    try:
        rec_id = int(rec_id)
    except Exception as e:
        rec_id = None

    if not rec_id:
        return invalid_object_id()

    try:
        res = request.env[model_name].search([('id', '=', rec_id)])
        if res:
            res.write(data)
        else:
            return object_not_found(rec_id, model_name)
    except Exception as e:
        return no_object_updated(e)
    if res:
        return valid_response(status_code, {'desc': 'Record Updated successfully!', 'update': True})


def object_delete_one(model_name, rec_id, status_code):
    try:
        rec_id = int(rec_id)
    except Exception as e:
        rec_id = None

    if not rec_id:
        return invalid_object_id()

    try:
        res = request.env[model_name].search([('id', '=', rec_id)])
        if res:
            res.unlink()
        else:
            return object_not_found(rec_id, model_name)
    except Exception as e:
        return no_object_deleted(e)
    if res:
        return valid_response(status_code, {'desc': 'Record Successfully Deleted!', 'delete': True})

def validate_payload(payload, mandatory_fields):
        """
            Validate that all mandatory fields exist in the payload
            
            :param payload: dict - The incoming request payload
            :param mandatory_fields: list - List of mandatory field names
            :return: tuple - (is_valid, error_message)
        """
        # Example usage:
        # is_valid, error = self._validate_payload(payload, ['field1', 'field2', 'field3'])
        # if not is_valid:
        #     return invalid_response(400, 'Validation Error', error)

        if not isinstance(payload, dict):
            return False, "Invalid payload format. Expected a dictionary."
        
        missing_fields = [field for field in mandatory_fields if field not in payload]
        
        if missing_fields:
            error_msg = f"Missing mandatory fields: {', '.join(missing_fields)}"
            return False, error_msg
        
        return True, ""

def check_valid_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        version = str(kwargs.get('version'))

        access_token = request.httprequest.headers.get('access_token')
        method = request.httprequest.method
        if not access_token:
            info = "Missing access token in request header!"
            error = 'access_token_not_found'
            return invalid_response(400, error, info,version)

        access_token_data = request.env['res.users.apikeys'].sudo().search(
            [('token', '=', access_token)], order='id DESC', limit=1)

        if access_token_data._get_access_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_token(version)

        request.session.uid = access_token_data.user_id.id
        request.update_env(user=access_token_data.user_id.id)
        return func(self, *args, **kwargs)

    return wrap

def verify_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        oauth = request.env['res.users.apikeys']
        access_token = request.httprequest.headers.get('Authorization')
        grant_type = access_token.split(' ')[0]
        headers = dict(request.httprequest.headers)
        ci_headers = CaseInsensitiveDict(headers)
        is_bank = False
        if 'Channel-Id' in ci_headers and 'X-Signature' in ci_headers and 'X-External-Id' in ci_headers and 'X-Partner-Id' in ci_headers:
            is_bank = True

        if not grant_type:
            return invalid_response(401, 'grant_type_not_found', 'Missing Grant Type in request header!')

        if not access_token.split(' ')[1]:
            if is_bank:
                if 'payment' in request.httprequest.url:
                    return invalid_token_b2b_bank(type='payment')
                elif 'qr-mpm-notify' in request.httprequest.url:
                    return invalid_token_b2b_bank(type='qr-mpm-notify')
                return invalid_token_b2b_bank()

            info = 'Missing access token in request header!'
            error = 'access_token_not_found'
            return invalid_response(400, error, info, request.httprequest.environ.get('REQUEST_METHOD'))

        access_token_data = oauth.sudo().search([
            ('grant_type_id.value', '=', grant_type.lower()),
            ('token', '=', access_token.split(' ')[1])
        ], limit=1)
        
        if not access_token_data:
            if is_bank:
                if 'payment' in request.httprequest.url:
                    return invalid_token_b2b_bank(type='payment')
                elif 'qr-mpm-notify' in request.httprequest.url:
                    return invalid_token_b2b_bank(type='qr-mpm-notify')
                return invalid_token_b2b_bank()
            
            return invalid_token(request.httprequest.environ.get('REQUEST_METHOD'))

        if access_token_data.is_expired():
            if is_bank:
                access_token_data.sudo().unlink()
                if 'payment' in request.httprequest.url:
                    return invalid_token_b2b_bank(type='payment')
                elif 'qr-mpm-notify' in request.httprequest.url:
                    return invalid_token_b2b_bank(type='qr-mpm-notify')
                return invalid_token_b2b_bank()
            
            _logger.error('JWT:: Token is expired !')
            return invalid_response(401, 'Unauthorized', 'Token is expired!',
                request.httprequest.environ.get('REQUEST_METHOD'))

        request.session.uid = access_token_data.user_id.id
        request.update_env(user=access_token_data.user_id.id)
        return func(self, *args, **kwargs)

    return wrap

def check_sensitive_value(convert_type,value):
    try:
        value = convert_type(value)
    except:
        return False
    return value

def invalid_value(message):
    return invalid_response(401, 'internal_error', message)

def invalid_token(version=None):
    return invalid_response(401, 'invalid_token', "Token is expired or invalid!", version)


def generate_token(length=40):
    random_data = os.urandom(100)
    hash_gen = hashlib.new('sha512')
    hash_gen.update(random_data)
    return hash_gen.hexdigest()[:length]

class ControllerREST(http.Controller):
    @http.route('/api/auth/get_tokens', methods=['POST'], type='http',auth='none', csrf=False)
    def api_get_tokens(self, **post):
        # Convert http data into json:
        db = db_name
        username = post['username'] if post.get('username') else None
        password = post['password'] if post.get('password') else None
        # Empty 'db' or 'username' or 'password:
        if not db or not username or not password:
            info = "Empty value of 'db' or 'username' or 'password'!"
            error = 'empty_db_or_username_or_password'
            _logger.error(info)
            return invalid_response(400, error, info)
        # Login in flectra database:
        try:
            request.session.authenticate(db, {
                'type': 'password',
                'login': username,
                'password': password
            })
            uid = request.session.uid
            user_context = request.session.context
            company_id = request.env.user.company_id.id
        except Exception as err:
            _logger.error(err.args)
            return invalid_response(400, 'Internal Server Error', err.args[0])
        
        # flectra login failed:
        if not uid:
            info = "flectra User authentication failed!"
            error = 'flectra_user_authentication_failed'
            _logger.error(info)
            return invalid_response(401, error, info)

        role = False
        role_id = False
        is_tdm = False
        user_name = False
        job_kategori = False
        company_id = False
        branch_name = False
        is_suspend = False
        area_code = False
        user_email = False
        emp = request.env['hr.employee'].sudo().search([('user_id','=',uid)],limit=1)
        if emp:
            role = emp.job_id.name
            role_id = emp.job_id.id
            # TODO: active again if branch have field is_tdm
            # is_tdm = emp.is_tdm
            user_name = emp.name
            job_kategori = emp.job_id.job_category_id.name
            company_id = emp.company_id.id
            branch_name = emp.company_id.name
            # TODO: active again if branch have field is_suspend
            # is_suspend = emp.is_suspend
            area_code = emp.area_id.name

        # Generate tokens
        access_token = request.env['res.users.apikeys']._get_access_token(user_id = uid, create = True)

        # Save all tokens in store
        _logger.info("Save OAuth2 tokens of user in store...")

        # Successful response:
        data = {
            'uid': uid,
            'user_context': user_context,
            'company_id': company_id,
            'access_token': access_token,
            'employee_id' : emp.id,
            'role_id':role_id,
            'role':role,
            'user_name':user_name,
            'job_kategori' : job_kategori,
            'company_id' : company_id,
            'branch_name' : branch_name,
            'is_tdm' : is_tdm,
            'user_email': user_email,
            'user_login': username,
            'is_suspend': is_suspend,
            'area_code': area_code
        }
        return valid_response(200,data)

    @http.route('/api/auth/tokens', methods=['POST'], type='http', auth='public', csrf=False, json_rpc=False)
    def get_jwt_tokens(self, **kwargs):
        db = db_name
        username = kwargs['username'] if kwargs.get('username') else None
        password = kwargs['password'] if kwargs.get('password') else None
        try:
            request.session.authenticate(db, {
                'type': 'password',
                'login': username,
                'password': password
            })
            uid = request.session.uid
            
        except Exception as err:
            _logger.error(err.args)
            return invalid_response(400, 'Internal Server Error', err.args[0])

        if not uid:
            info = 'Username or Password is invalid!'
            _logger.error(info)
            return invalid_response(401, 'AccessDenied', info)

        # verify body and user oauth credentials sends by client
        # generate tpken if body and user is verified
        try:
            oauth = request.env['res.users.apikeys']._generate_jwt(uid, kwargs)
        
        except MissingError as err:
            _logger.error(err.args)
            return invalid_response(401, 'MissingError', err.args[0])
        
        except AccessDenied as err:
            _logger.error(err.args)
            return invalid_response(400, err.args[0], 'User authentication is invalid!')

        return valid_response(200, {
            'access_token': oauth.get('token'),
            'expired_in': oauth.get('expires')
        })

    @http.route('/api/auth/<version>/check_auth', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def check_auth(self,version,**post):
        uid = request.session.uid
        data = {
                'uid': uid
            }
        
        return valid_response(200,data)

    # Delete access tokens from token store:
    @http.route('/api/auth/delete_tokens', methods=['POST'], type='http',
                auth='none', csrf=False)
    def api_auth_deletetokens(self, **post):
        # Try convert http data into json:
        firebase_token = False
        access_token = request.httprequest.headers.get('access_token')
        access_token_data = request.env['res.users.apikeys'].sudo().search(
            [('token', '=', access_token)], order='id DESC', limit=1)

        if not access_token_data:
            info = "No access token was provided in request!"
            error = 'no_access_token'
            _logger.info(info)
            _logger.info(request.httprequest.headers)
            _logger.info(post)
            return invalid_response(400, error, info)
        
        

        access_token_data.sudo().unlink()
        # Successful response:
        if 'firebase_token' in request.httprequest.headers:
            firebase_token = request.httprequest.headers.get('firebase_token')
            check_firebase_user=request.env['dms.firebase.user'].sudo().search([
                ('access_token','=',access_token),
                ('firebase_token','=',firebase_token),
                ('active','=',True)
                ])
            if check_firebase_user :
                for tok in check_firebase_user :
                    tok.write({'active' : False})
                    # TODO: Kembalikan ke device sebelumnya
                    # if len(check_firebase_user) == 1:
                    #     pass
                    # request.env['dms.firebase.user'].sudo().search([
                    #     ('access_token','=',access_token),
                    #     ('device_id','!=',check_firebase_user.device_id),
                    # ])
            


        return valid_response(
            200,
            {"desc": 'Token Successfully Deleted', "delete": True}
        )

    @http.route([
        '/api/<model_name>',
        '/api/<model_name>/<id>'
    ], type='http', auth="none", methods=['POST', 'GET', 'PUT', 'DELETE'],
        csrf=False)
    @check_valid_token
    def restapi_access_token(self, model_name=False, id=False, **post):
        Model = request.env['ir.model']
        Model_id = Model.sudo().search([('model', '=', model_name)], limit=1)

        if Model_id:
            if Model_id.rest_api:
                return getattr(self, '%s_data' % (
                    request.httprequest.method).lower())(
                    model_name=model_name, id=id, **post)
            else:
                return rest_api_unavailable(model_name)
        url = request.httprequest.url
        return modal_not_found(model_name,url)

    def get_data(self, model_name=False, id=False, **get):
        if id:
            return object_read_one(model_name, id, get, status_code=200)
        return object_read(model_name, get, status_code=200)

    def put_data(self, model_name=False, id=False, **put):
        return object_update_one(model_name, id, put, status_code=200)

    def post_data(self, model_name=False, **post):
        return object_create_one(model_name, post, status_code=200)

    def delete_data(self, model_name=False, id=False):
        return object_delete_one(model_name, id, status_code=200)
