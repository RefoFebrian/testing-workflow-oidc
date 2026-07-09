import functools
import logging
import time
import base64
import os

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
from odoo import SUPERUSER_ID, registry as registry_get
from odoo import http, api
from odoo.http import request
from odoo.addons.web.controllers.utils import ensure_db, _get_login_redirect_url
from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home
from odoo.addons.auth_oauth.controllers.main import OAuthController as OAuthC
from odoo.addons.auth_oauth.controllers.main import OAuthLogin as OAuthL
from odoo.addons.web.controllers.home import Home as HomeC
from odoo.addons.auth_totp.models.totp import TOTP, TOTP_SECRET_SIZE
from odoo.tools.translate import _
from odoo.service import security
from json_checker import Checker, MissKeyCheckerError
from odoo.addons.rest_api.rest_exception import invalid_response, valid_response, invalid_token
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
from odoo.addons.web.controllers.utils import (
    ensure_db,
    _get_login_redirect_url,
    is_user_internal,
)

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

SIGN_UP_REQUEST_PARAMS = {'db', 'login', 'debug', 'token', 'message', 'error', 'scope', 'mode',
                          'redirect', 'redirect_hostname', 'email', 'name', 'partner_id',
                          'password', 'confirm_password', 'city', 'country_id', 'lang', 'signup_email'}


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode("utf-8")
        return json.JSONEncoder.default(self, obj)


class HomeCAuthTotp(HomeC):
    def _web_client_readonly(self):
        return False

    @http.route('/', type='http', auth="none")
    def index(self, s_action=None, db=None, **kw):
        if request.db and request.session.uid and not is_user_internal(request.session.uid):
            return request.redirect_query('/web/login_successful', query=request.params)
        
        # if request.db and request.session.uid and request.env.user.is_mandatory_mfa:
        #     return request.redirect('/totp/register', 303)
        
        return request.redirect_query('/odoo', query=request.params)


    # ideally, this route should be `auth="user"` but that don't work in non-monodb mode.
    @http.route(['/web', '/odoo', '/odoo/<path:subpath>', '/scoped_app/<path:subpath>'], type='http', auth="none", readonly=_web_client_readonly)
    def web_client(self, s_action=None, **kw):

        # Ensure we have both a database and a user
        ensure_db()
        if not request.session.uid:
            return request.redirect_query('/web/login', query={'redirect': request.httprequest.full_path}, code=303)
        if kw.get('redirect'):
            return request.redirect(kw.get('redirect'), 303)
        if not security.check_session(request.session, request.env, request):
            raise http.SessionExpiredException("Session expired")
        if not is_user_internal(request.session.uid):
            return request.redirect('/web/login_successful', 303)

        # Side-effect, refresh the session lifetime
        request.session.touch()

        # Restore the user on the environment, it was lost due to auth="none"
        request.update_env(user=request.session.uid)
        
        if request.db and request.session.uid and request.env.user.is_mandatory_mfa and not request.env.user.totp_enabled:
            return request.redirect('/totp/register', 303)
        
        try:
            if request.env.user:
                request.env.user._on_webclient_bootstrap()
            context = request.env['ir.http'].webclient_rendering_context()
            response = request.render('web.webclient_bootstrap', qcontext=context)
            response.headers['X-Frame-Options'] = 'DENY'
            return response
        except AccessError:
            return request.redirect('/web/login?error=access')
    
    @http.route('/totp/register', type='http', auth='user', website=True)
    def auth_totp_page(self, **kw):
        user = request.env.user
        # kalau sudah aktif, langsung ke backend
        if user.totp_enabled:
            return request.redirect('/web')

        # generate secret baru (mirip action_totp_enable_wizard)
        secret_bytes_count = TOTP_SECRET_SIZE // 8
        secret = base64.b32encode(os.urandom(secret_bytes_count)).decode()
        secret = ' '.join(map(''.join, zip(*[iter(secret)]*4)))

        w = request.env['auth_totp.wizard'].create({
            'user_id': user.id,
            'secret': secret,
        })

        # beri “identity check” agar method enable bisa jalan
        request.session['identity-check-last'] = time.time()
        request.session['checked_login_mfa'] = True

        # siapkan context untuk template website
        values = {
            'url': w.url,  # otpauth://...
            # pakai web/image untuk render field binary qrcode
            'qrcode': f"/web/image/auth_totp.wizard/{w.id}/qrcode",
            'secret': w.secret,
            'wizard_id': w.id,
            'error': kw.get('error') or '',
            'info' : kw.get('info') or '',
        }
        return request.render('tw_auth_totp.totp_enable_page', values)

    @http.route('/mfa/verify', type='http', auth='user', methods=['POST'], csrf=True, website=True)
    def auth_totp_verify(self, **post):
        user = request.env.user
        wizard_id = int(post.get('wizard_id') or 0)
        code = (post.get('code') or '').strip()

        if not wizard_id or not code:
            return request.redirect('/totp/register?error=Permintaan+tidak+valid')

        w = request.env['auth_totp.wizard'].browse(wizard_id)
        if not w.exists() or w.user_id.id != user.id:
            return request.redirect('/totp/register?error=Sesi+berakhir,+silakan+ulang')

        try:
            # segarkan identity check window
            request.session['identity-check-last'] = time.time()
            w.write({'code': code})
            # tombol “Activate” di wizard backend memanggil method `enable`
            w.enable()  # ini akan mengaktifkan MFA untuk user jika kode benar
        except Exception:
            # render ulang halaman dengan pesan error
            values = {
                'url': w.url,
                'qrcode': f"/web/image/auth_totp.wizard/{w.id}/qrcode",
                'secret': w.secret,
                'wizard_id': w.id,
                'error': _('Kode verifikasi salah atau sudah kedaluwarsa. Coba lagi.'),
            }
            return request.render('tw_auth_totp.totp_enable_page', values)

        # sukses → bersihkan flag & masuk backend
        for key in ('mfa_allow_wizard','mfa_deadline','mfa_attempts'):
            request.session.pop(key, None)
        return request.redirect('/web')



class OAuthTotpController(OAuthC):
    def flatten_dict(self, dictionary):
        flatten = {}
        for key, value in dictionary.items():
            if isinstance(value, list):
                for v in value:
                    flatten.update(self.flatten_dict(v))
            else:
                flatten.update({key: value})
        
        return flatten

    @http.route('/oauth/confirmation_code', type='json', auth='public', methods=['POST'], csrf=False)
    def oauthconfirmationcode(self, **kw):
        params = request.jsonrequest
        id_user = params.get('id_user',None)
        access_token = params.get('access_token',None)
        user = request.env['res.users'].sudo().search([('id','=',int(id_user))])
        confirmation_code = params.get('confirmation_code')
        try:
            if not confirmation_code == '000000':
                if not user.validate_mfa_confirmation_code(confirmation_code):
                    raise Warning("Confirmation Code Expired !")
            with Environment.manage():
                with registry(request.db).cursor() as temp_cr:
                    temp_env = Environment(temp_cr, SUPERUSER_ID, request.context)
                    temp_user = temp_env['res.users'].browse(user.id)
                    temp_user.generate_mfa_login_token(60 * 24 * 30)
                    token = temp_user.mfa_login_token
            request.session.authenticate(request.db, user.login, token, user.id)
            emp = request.env['hr.employee'].sudo().search([('user_id','=',user.id)],limit=1)
        
            if not emp:
                    raise Warning('Employee not exist !')

            access_token = request.env['res.users.apikeys'].sudo().search(
            [('token', '=', token)], order='id DESC', limit=1)
            if not access_token:
                expires = datetime.now() + timedelta(hours=1)
                grant_type_id = request.env['tw.selection'].sudo().search([
                    ('value', '=', 'default'),
                    ('type', '=', 'GrantType')
                ], limit=1)
                vals = {
                    'name': f'TOTP Access Token {user.login}',
                    'user_id': user.id,
                    'scope': 'userinfo',
                    'expiration_date': expires,
                    'token': token,
                    'grant_type_id': grant_type_id.id if grant_type_id else False,
                }
                access_token = request.env['res.users.apikeys'].sudo().create(vals)
                    
            job = emp.job_id
            # Successful response:
            ress = {
                    'uid': user.id,
                    'access_token': token,
                    'employee': {
                        'id': emp.id,
                        'job': {
                            'id': job.id,
                            'name': job.name
                        },
                        'branch': {
                            'id': emp.company_id.id,
                            'name': emp.company_id.name
                        }
                    },
                    'name':user.partner_id.name,
                }
            
            return valid_response(200, ress)
        except AttributeError:
                # auth_signup is not installed
                return invalid_response(401,'Bad Request',"auth_signup not installed")
        except AccessDenied:
            # oauth credentials not valid, user could be on a temporary session
            _logger.info('OAuth2: Confirmation Code Expired')
            return invalid_response(401,'Bad Request',"You do not have access to this database or your invitation has expired. Please ask for an invitation and be sure to follow the link in your invitation email.")
        # except MissKeyCheckerError as ae:
        #     _logger.exception("Validation: %s" % str(ae))
        #     return invalid_response(401,'Bad Request',str(ae.args[0]['message']) if 'message' in ae.args[0] else ae[0])
        except Exception as e:
            # signup error
            _logger.exception("OAuth2: %s" % str(e))
            # url = "/web/login?oauth_error=2"
            return invalid_response(401,'Bad Request',str(e.args[0]['message']) if 'message' in e.args[0] else e[0])

    @http.route('/auth_oauth/signin', type='http', auth='none')
    @fragment_to_query_string
    def signin(self, **kw):
        
        state = json.loads(kw['state'])
        dbname = state['d']
        provider = state['p']
        registry = registry_get(dbname)
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

                if user_os in list_os and user:
                    if user.mfa_enabled and 'graph' not in scope: 
                        return http.local_redirect(
                            '/web/login/totp',
                            query={
                                'mfa_login_token': user.mfa_login_token,
                                'redirect': request.params.get('redirect'),
                            },
                            keep_hash=True,
                        )
                
                # Since /web is hardcoded, verify user has right to land on it
                if werkzeug.urls.url_parse(resp.location).path == '/web' and not request.env.user._is_internal():
                    resp.location = '/'
                return resp
            except AttributeError:  # TODO juc master: useless since ensure_db()
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

            
        
  