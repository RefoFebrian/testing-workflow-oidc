# -*- coding: utf-8 -*-
import logging
import requests
from odoo import api, models, _
from odoo.http import request

logger = logging.getLogger(__name__)

class Http(models.AbstractModel):
    _inherit = "ir.http"

    @api.model
    def _verify_recaptcha_token(self, ip_addr, token, action=False):
        """ Override to handle v2 (scoreless) verification """
        version = self.env['ir.config_parameter'].sudo().get_param('web_login_captcha.recaptcha_version')
        
        if version == 'v2_checkbox':
            # v2 Logic: No score check, just verification
            private_key = request.env['ir.config_parameter'].sudo().get_param('recaptcha_private_key')
            if not private_key:
                return 'no_secret'
            
            try:
                r = requests.post('https://www.recaptcha.net/recaptcha/api/siteverify', {
                    'secret': private_key,
                    'response': token,
                    'remoteip': ip_addr,
                }, timeout=2)
                result = r.json()
                if result.get('success'):
                    return 'is_human'
                
                # Handle errors
                errors = result.get('error-codes', [])
                logger.warning("ReCAPTCHA v2 verification failed for ip %s. Errors: %r", ip_addr, errors)
                for error in errors:
                    if error in ['missing-input-secret', 'invalid-input-secret']:
                        return 'wrong_secret'
                    if error in ['missing-input-response', 'invalid-input-response']:
                        return 'wrong_token'
                    if error == 'timeout-or-duplicate':
                        return 'timeout'
                    if error == 'bad-request':
                        return 'bad_request'
                return 'is_bot'
                
            except requests.exceptions.Timeout:
                return 'timeout'
            except Exception:
                return 'bad_request'
                
        # Fallback to standard (v3) logic for other cases
        return super(Http, self)._verify_recaptcha_token(ip_addr, token, action)
