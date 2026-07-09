# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError, ValidationError

# Dynamic inheritance to preserve the chain
try:
    from odoo.addons.auth_oauth.controllers.main import OAuthLogin as Home
except ImportError:
    try:
        from odoo.addons.auth_signup.controllers.main import AuthSignupHome as Home
    except ImportError:
        from odoo.addons.web.controllers.home import Home

class OAuthLoginCaptcha(Home):
    @http.route()
    def web_login(self, redirect=None, **kw):
        # 1. Handle POST Captcha Verification
        error = None
        if request.httprequest.method == 'POST':
            pub_key = request.env['ir.config_parameter'].sudo().get_param('recaptcha_public_key')
            priv_key = request.env['ir.config_parameter'].sudo().get_param('recaptcha_private_key')
            recaptcha_version = request.env['ir.config_parameter'].sudo().get_param('web_login_captcha.recaptcha_version')
            
            if pub_key and priv_key and recaptcha_version != 'off':
                try:
                    if not request.env['ir.http']._verify_request_recaptcha_token('login'):
                        error = _("Suspicious activity detected by Google reCaptcha.")
                except (ValidationError, UserError) as e:
                    error = e.args[0]

                if error:
                    # Captcha failed. We must prevent login.
                    # Strategy: Remove password from params to force request.session.authenticate() to fail 
                    # in the super() call. This ensures a proper error response is generated with all context.
                    if 'password' in request.params:
                        del request.params['password']
                    # We will inject the 'error' message into the response after super() returns.

        # 2. Call Super (handles both GET and standard POST login)
        response = super().web_login(redirect=redirect, **kw)

        # 3. Inject Context on ANY QWeb Response (GET or failed POST re-render)
        if response.is_qweb:
            pub_key = request.env['ir.config_parameter'].sudo().get_param('recaptcha_public_key')
            priv_key = request.env['ir.config_parameter'].sudo().get_param('recaptcha_private_key')
            version = request.env['ir.config_parameter'].sudo().get_param('web_login_captcha.recaptcha_version')
            response.qcontext['recaptcha_enabled'] = bool(pub_key and priv_key and version != 'off')
            response.qcontext['recaptcha_version'] = version or 'v3_invisible'
            response.qcontext['recaptcha_site_key'] = pub_key
            
            # If we had a captcha error, override the generic "Wrong login/password" error
            if error:
                response.qcontext['error'] = error
        
        return response
