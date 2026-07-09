import functools
import logging

try:
    import simplejson as json
except ImportError:
    import json

import werkzeug.urls
import werkzeug.utils
from werkzeug.exceptions import BadRequest as AccessDenied
import httpagentparser

import odoo
from odoo.api import Environment
from odoo import SUPERUSER_ID
from odoo.modules.registry import Registry
from odoo import http, api
from odoo.http import request
from odoo.addons.web.controllers.utils import ensure_db, _get_login_redirect_url
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home
from odoo.addons.auth_oauth.controllers.main import OAuthController as OAuthC
from odoo.addons.auth_oauth.controllers.main import OAuthLogin as OAuthL
from odoo.tools.translate import _
from json_checker import Checker, MissKeyCheckerError
from odoo.addons.rest_api.rest_exception import invalid_response, valid_response, invalid_token
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

#----------------------------------------------------------
# helpers
#----------------------------------------------------------
def fragment_to_query_string(func):
    @functools.wraps(func)
    def wrapper(self, *a, **kw):
        if not kw:
            return """<html><head><script>
                var l = window.location;
                var q = l.hash.substring(1);
                var r = l.pathname + l.search;
                if(q.length !== 0) {
                    var s = l.search ? (l.search === '?' ? '' : '&') : '?';
                    r = l.pathname + l.search + s + q;
                }
                if (r == l.pathname) {
                    r = '/';
                }
                window.location = r;
            </script></head><body></body></html>"""
        return func(self, *a, **kw)
    return wrapper  


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode("utf-8")
        return json.JSONEncoder.default(self, obj)


class OAuthController(OAuthC):
    def flatten_dict(self, dictionary):
        flatten = {}
        for key, value in dictionary.items():
            if isinstance(value, list):
                for v in value:
                    flatten.update(self.flatten_dict(v))
            else:
                flatten.update({key: value})
        
        return flatten

    @http.route('/auth_oauth/signin', type='http', auth='none')
    @fragment_to_query_string
    def signin(self, **kw):
        
        state = json.loads(kw['state'])
        dbname = state['d']
        provider = state['p']
        registry = Registry(dbname)
        with registry.cursor() as cr:
            try:
                credentials = request.env['res.users'].with_user(SUPERUSER_ID).auth_oauth(provider, kw)
                login = credentials[1]
                key = credentials[2]
                request._cr.commit()
                action = state.get('a')
                menu = state.get('m')
                redirect = werkzeug.urls.url_unquote_plus(state['r']) if state.get('r') else False
                url = '/odoo'
                if redirect:
                    url = redirect
                elif action:
                    url = '/odoo/action-%s' % action
                elif menu:
                    url = '/odoo?menu_id=%s' % menu

                credential = {'login': login, 'token': key, 'type': 'oauth_token'}
                auth_info = request.session.authenticate(dbname, credential)
                resp = request.redirect(_get_login_redirect_url(auth_info['uid'], url), 303)
                resp.autocorrect_location_header = False
                agent = request.httprequest.environ.get('HTTP_USER_AGENT')
                agent_details = httpagentparser.detect(agent)
                user_os = agent_details['os']['name']
                list_os = ['Macintosh','Linux','Windows']
                scope = credentials[3]
                if auth_info.get('uid'):
                    user = request.env['res.users'].sudo().search([('id','=',auth_info['uid'])],limit=1)
                    if user: 
                        request.env.user = user
                        if user._check_schema_reset_password():
                            user.action_remove_password()
                        request.env['res.users.log'].sudo().create({'type': 'oauth'})
                # Since /web is hardcoded, verify user has right to land on it
                if werkzeug.urls.url_parse(resp.location).path == '/web' and not request.env.user._is_internal():
                    resp.location = '/'
                return resp

            except AttributeError:  
                # auth_signup is not installed
                _logger.error("auth_signup not installed on database %s: oauth sign up cancelled.", dbname)
                url = "/web/login?oauth_error=1"
            except AccessDenied:
                # oauth credentials not valid, user could be on a temporary session
                _logger.info('OAuth2: access denied, redirect to main page in case a valid session exists, without setting cookies')
                url = "/web/login?oauth_error=3"
            except Exception:
                # signup error
                _logger.exception("Exception during request handling")
                url = "/web/login?oauth_error=2"

        redirect = request.redirect(url, 303)
        redirect.autocorrect_location_header = False
        return redirect

    @http.route('/oauth/signin', type='json', auth='public', methods=['POST'], csrf=False)
    def oauthsignin(self, **kw):
        expected_schema = {'access_token': str, 'device_id': str, 'device_type':str, 'p':str}        
        try:
            state = request.jsonrequest
            dbname = request.env.cr.dbname

            check_provider = request.env['auth.oauth.provider'].sudo().search([('client_id','=',state['p'])])
            provider = check_provider.id if check_provider else 1
            registry = Registry(dbname)
            context = state.get('c', {})
            with registry.cursor() as cr:
            
                env = api.Environment(cr, SUPERUSER_ID, context)
                credentials = env['res.users'].sudo().auth_oauth(provider, state)
                (dbname, login, access_token) = (credentials[0],credentials[1],credentials[2])
                cr.commit()

                if access_token :
                    user = request.env['res.users'].sudo().search([('login','=',login)],limit=1)
                    if not user:
                        raise AccessDenied()
                    emp = request.env['hr.employee'].sudo().search([('user_id','=',user.id)],limit=1)
                    if emp:
                        role = emp.apps_job_id.name if emp.apps_job_id else emp.job_id.name
                        role_id = emp.apps_job_id.id if emp.apps_job_id else emp.job_id.id

                    if not emp:
                        raise AccessDenied()
                       
                    job = emp.job_id
                    # TODO
                    resp = login_and_redirect(*(dbname, login, access_token), redirect_url='/')
                    resp = request.redirect(_get_login_redirect_url(user.id, url), 303)
                    # Since /web is hardcoded, verify user has right to land on it
                    if werkzeug.urls.url_parse(resp.location).path == '/web' and not request.env.user.has_group('base.group_user'):
                        resp.location = '/'

                    # Successful response:
                    access_token_obj = request.env['res.users.apikeys'].sudo().search(
                    [('token', '=', access_token)], order='id DESC', limit=1)
                    if not access_token_obj:
                        expires = datetime.now() + timedelta(hours=1)
                        grant_type_id = request.env['tw.selection'].sudo().search([
                            ('value', '=', 'default'),
                            ('type', '=', 'GrantType')
                        ], limit=1)
                        vals = {
                            'name': f'OAuth Access Token {user.login}',
                            'user_id': user.id,
                            'scope': 'userinfo',
                            'expiration_date': expires,
                            'token': access_token,
                            'grant_type_id': grant_type_id.id if grant_type_id else False,
                        }
                        access_token_obj = request.env['res.users.apikeys'].sudo().create(vals)

                    ress = {
                            'uid': user.id,
                            'access_token': access_token,
                            'employee': {
                                'id': emp.id,
                                'job': {
                                    'id': role_id,
                                    'name': role
                                },
                                'branch': {
                                    'id': emp.company_id.id,
                                    'name': emp.company_id.name
                                }
                            },
                            'name':user.partner_id.name,
                        }
                    
                    mfa_login_token = user.generate_mfa_login_token()
                    if mfa_login_token:
                        ress['mfa_login_token'] = user.mfa_login_token

                    return valid_response(200, ress)
        except AttributeError:
                # auth_signup is not installed
                _logger.error("auth_signup not installed on database %s: oauth sign up cancelled." % (dbname,))
                url = "/web/login?oauth_error=1"
                return invalid_response(401,'Bad Request',"auth_signup not installed")
        except AccessDenied:
            # oauth credentials not valid, user could be on a temporary session
            _logger.info('OAuth2: access denied, redirect to main page in case a valid session exists, without setting cookies')
            return invalid_response(401,'Bad Request',"You do not have access to this database or your invitation has expired. Please ask for an invitation and be sure to follow the link in your invitation email.")
        except Exception as e:
            # signup error
            _logger.exception("OAuth2: %s" % str(e))
            return invalid_response(401,'Bad Request',str(e.args[0]['message']) if 'message' in e.args[0] else e[0])
        return redirect(url)

class OAuthLogin(OAuthL):
    
    def list_providers(self):
        try:
            providers = request.env['auth.oauth.provider'].sudo().search_read([('enabled', '=', True)])
        except Exception:
            providers = []
        for provider in providers:
            return_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            return_url = return_url + '/auth_oauth/signin'
            state = self.get_state(provider)
            params = dict(
                response_type='token',
                client_id=provider['client_id'],
                redirect_uri=return_url,
                scope=provider['scope'],
                state=json.dumps(state),
                # nonce=base64.urlsafe_b64encode(os.urandom(16)),
            )
            provider['auth_link'] = "%s?%s" % (provider['auth_endpoint'], werkzeug.urls.url_encode(params))
        return providers

    def get_state(self, provider):
        redirect = request.params.get('redirect', 'web')
        return_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if not redirect.startswith(('//', 'http://', 'https://')):
            redirect = '%s%s' % (return_url, redirect)
        state = dict(
            d=request.session.db,
            p=provider['id'],
            r=werkzeug.urls.url_quote_plus(redirect),
        )
        token = request.params.get('token')
        if token:
            state['t'] = token
        return state

    @http.route()
    def web_login(self, *args, **kw):
        ensure_db()
        if request.httprequest.method == 'GET' and request.session.uid and request.params.get('redirect'):
            # Redirect if already logged in and redirect param is present
            return request.redirect(request.params.get('redirect'))
        providers = self.list_providers()

        response = super(OAuthLogin, self).web_login(*args, **kw)
        if response.is_qweb:
            error = request.params.get('oauth_error')
            if error == '1':
                error = _("Sign up is not allowed on this database.")
            elif error == '2':
                error = _("Access Denied")
            elif error == '3':
                error = _("You do not have access to this database or your invitation has expired. Please ask for an invitation and be sure to follow the link in your invitation email.")
            elif error == '4':
                error = _("Enable MFA for Azure and Google accounts to ensure heightened security")
            else:
                error = None

            response.qcontext['providers'] = providers
            if error:
                response.qcontext['error'] = error

        return response



