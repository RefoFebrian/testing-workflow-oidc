# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date
import requests

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import SUPERUSER_ID
from odoo import models, fields, api, _, Command
from odoo.tools import str2bool

# 4:  imports from odoo modules
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError as Warning, AccessDenied, AccessError, ValidationError
# 5: local imports

# 6: Import of unknown third party lib

import logging

_logger = logging.getLogger(__name__)

class ResUsersAuth(models.Model):
    _inherit = "res.users"
    _description = "User"

    # 11: compute/depends & on change methods
            
    # 12: override methods

    # 13: action methods

    def verify_token_auth(self,provider, access_token):
        check_user = False
        email_user = False
        provide = self.env['auth.oauth.provider'].sudo().search([('client_id','=',provider)])

        # validation provider
        validation = self._auth_oauth_validate(provider=provide.id, access_token=access_token)
        if not validation.get('user_id'):
            # Workaround: facebook does not send 'user_id' in Open Graph Api
            if validation.get('id'):
                validation['user_id'] = validation['id']
            else:
                raise AccessDenied()
        
        email = validation['mail'] if 'mail' in validation else validation['email'] if 'email' in validation else False
        if email:
            check_user = self.sudo().search([('oauth_uid','=',email)],limit=1)
            email_user = check_user.oauth_uid
        return check_user if email == email_user else False        
        
    
    @api.model
    def auth_oauth(self,provider, params, context=None):
        access_token = params.get('access_token')
        
        validation = self._auth_oauth_validate(provider, access_token)
        
        # required check
        scope = validation.get('@odata.context',None) or validation.get('scope',None)
        
        if scope:
            # * Azure Check
            if 'graph' in scope:
                provider_obj = self.env['auth.oauth.provider'].suspend_security().search([('id','=',int(provider))])
                if provider_obj.notify_mfa == True:
                    url = provider_obj.url_mfa
                    mfa_status = requests.get(url,headers={'Authorization': 'Bearer {}'.format(access_token)}).json()
                    value = mfa_status.get('value',None)
                    self._context.update({'mfa_status': value})
                    if not value:
                        raise Warning('Enable MFA for Azure and Google accounts to ensure heightened security !')
                if not validation.get('user_id') and not validation.get('id'):
                    raise AccessDenied()
        
            # * Google Check
            if 'google' in scope:
                if not validation.get('email'):
                    raise AccessDenied()
        # retrieve and sign in user
        login = self._auth_oauth_signin(provider, validation, params, context=context)
        if not login:
            raise AccessDenied()
        if 'google' in scope and not login.mfa_enabled:
            raise Warning('Enable MFA for Azure / Google / SATU accounts to ensure heightened security !')

        # return user credentials
        return (self.env.cr.dbname, login.login, access_token,scope)

    def action_remove_password(self):
        if not self.oauth_uid:
            raise Warning("User is not set to Oauth / SSO Tunas, please set Oauth / SSO Tunas first")
        
        self.env.cr.execute("SELECT id FROM res_users WHERE id = %s AND password IS NOT NULL;", (self.id))
        result = self.env.cr.fetchone()
        if result:
            # when user has no password return true
            return True
        # Bypass when onchange because self is NewId with Origin ID Self it self object
        id_user = self.id.origin if hasattr(self.id, 'origin') else self.id
        self.env.cr.execute(
            'UPDATE res_users SET password=%s WHERE id=%s',
            (None, id_user)
        )

    # 11: Private Method
    def _check_schema_reset_password(self):
        schema_reset_password = self.env['ir.config_parameter'].sudo().get_param('tw_auth_oauth.schema_reset_password',False)
        schema_reset_password = str2bool(schema_reset_password)
        if schema_reset_password:
            return True 
        return False
        
        

    def _auth_oauth_rpc(self,endpoint, access_token, context=None):
        if self.env['ir.config_parameter'].sudo().get_param('auth_oauth.authorization_header'):
            response = requests.get(endpoint, headers={'Authorization': 'Bearer %s' % access_token}, timeout=10)
        else:
            response = requests.get(endpoint, params={'access_token': access_token}, timeout=10)
        
        if 'graph.microsoft.com' in endpoint:
            check_token = requests.get(
                endpoint, headers={'Authorization': 'Bearer {}'.format(access_token)}
            )
            return check_token.json()

        
        if response.ok: # nb: could be a successful failure
            return response.json()

        auth_challenge = parse_auth(response.headers.get("WWW-Authenticate"))
        if auth_challenge and auth_challenge.type == 'bearer' and 'error' in auth_challenge:
            return dict(auth_challenge)

        return {'error': 'invalid_request'} 
    
    @api.model
    def _auth_oauth_signin(self, provider, validation, params, context=None):
        """ retrieve and sign in the user corresponding to provider and validated access token
            :param provider: oauth provider id (int)
            :param validation: result of validation of access token (dict)
            :param params: oauth parameters (dict)
            :return: user login (str)
            :raise: odoo.exceptions.AccessDenied if signin failed

            This method can be overridden to add alternative signin methods.
        """         
        email =  validation.get('email',None) or validation.get('mail',None) or validation.get('userPrincipalName',None)
        oauth_user = self.search([("oauth_uid", "=", email), ('oauth_provider_id', '=', provider)])
        if not oauth_user:
            raise AccessDenied()
        assert len(oauth_user) == 1
        self.env.user = oauth_user
        oauth_user.sudo().write({'oauth_access_token': params.get('access_token')}) 
        return oauth_user
    



        