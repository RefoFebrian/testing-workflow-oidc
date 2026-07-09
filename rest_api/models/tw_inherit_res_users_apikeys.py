# -*- coding: utf-8 -*-
import hashlib
import jwt
import logging

from datetime import datetime, timedelta
from jwt.exceptions import ExpiredSignatureError

from odoo import models, fields
from odoo.exceptions import MissingError, AccessDenied
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, SQL

_logger = logging.getLogger(__name__)

try:
    from oauthlib import common as oauthlib_common
except ImportError:
    _logger.warning(
        'OAuth library not found. If you plan to use it, '
        'please install the oauth library from '
        'https://pypi.python.org/pypi/oauthlib')
    

class UsersAPIKeys(models.Model):
    _inherit = "res.users.apikeys"

    token = fields.Char('Access Token', required=True)
    grant_type_id = fields.Many2one('tw.selection', string='Grant Type', domain=[('type', '=', 'GrantType')])

    def init(self):
        super().init()
        table = SQL.identifier(self._table)
        self.env.cr.execute(SQL("""
            ALTER TABLE %(table)s
            ADD COLUMN IF NOT EXISTS token VARCHAR,
            ADD COLUMN IF NOT EXISTS grant_type_id INTEGER REFERENCES tw_selection(id) ON DELETE CASCADE
        """, table=table))

    def _get_access_token(self, user_id=None, create=False):
        if not user_id:
            user_id = self.env.user.id

        access_token = self.search([('user_id', '=', user_id),
                                    ('grant_type_id.value', '=', 'default')],
                                    order='id DESC', limit=1)
        if access_token:
            access_token = access_token[0]
            # if access_token.is_expired():
            #     access_token = None
        if not access_token and create:
            now = datetime.now()
            expires = now + timedelta(seconds=int(self.env.ref('rest_api.oauth2_access_token_expires_in').sudo().value))
            grant_type_id = self.env['tw.selection'].search([('value', '=', 'default'), ('type', '=', 'GrantType')])
            vals = {
                'name': f'Access REST API {self.env.user.login}',
                'user_id': user_id,
                'scope': 'userinfo',
                'create_date': now,
                'expiration_date': expires,
                'token': oauthlib_common.generate_token(),
                'grant_type_id': grant_type_id.id
            }
            access_token = self.sudo().create(vals)
            # we have to commit now, because /oauth2/tokeninfo could
            # be called before we finish current transaction.
            self._cr.commit()

        if not access_token:
            return None
        return access_token.token


    def _get_access_token_google(self, user_id=None, create=False):
        access_token = self.search([('user_id', '=', user_id),
                                    ('grant_type_id.value', '=', 'default')],
                                    order='id DESC', limit=1)
        if access_token:
            access_token = access_token[0]
            # if access_token.is_expired():
            #     access_token = None
        if not access_token and create:
            expires = datetime.now() + timedelta(seconds=int(self.env.ref('rest_api.oauth2_access_token_expires_in').sudo().value))
            vals = {
                'user_id': user_id,
                'scope': 'userinfo',
                'expires': expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'token': oauthlib_common.generate_token(),
                'grant_type': 'default'
            }
            access_token = self.create(vals)
            # we have to commit now, because /oauth2/tokeninfo could
            # be called before we finish current transaction.
            self._cr.commit()

        if not access_token:
            return None
        return access_token.token   



    def is_valid(self, scopes=None):
        """
        Checks if the access token is valid.

        :param scopes: An iterable containing the scopes to check or None
        """
        self.ensure_one()
        return not self.is_expired() and self._allow_scopes(scopes)

    def is_expired(self):
        self.ensure_one()
        return datetime.now() > fields.Datetime.from_string(self.expiration_date)

    def _allow_scopes(self, scopes):
        self.ensure_one()
        if not scopes:
            return True

        provided_scopes = set(self.scope.split())
        resource_scopes = set(scopes)

        return resource_scopes.issubset(provided_scopes)

    # TODO: SPJ - Seharusnya bisa 1 saja dengan yang di file Oauth Provider
    def _generate_jwt(self, user_id, payload, expired_time=1200, is_force_create=False):
        oauth = self.search([('user_id', '=', user_id),
                             ('grant_type_id.value', '=', payload.get('grant_type'))],
                             limit=1)
        is_create = False
        if not oauth:
            is_create = True
        
        if not oauth:
            user = self.env['res.users'].sudo().browse(user_id)
        else:
            user = oauth.user_id
        if user.client_id != payload.get('client_id'):
            raise MissingError('client_id is not recognized!')
        
        if user.client_secret != payload.get('client_secret'):
            raise MissingError('client_secret is not recognized!')

        payload.update({
            'exp': timedelta(seconds=expired_time).seconds,
            'username': user.login,
            'password': user.password
        })
        expires = datetime.now() + timedelta(seconds=expired_time)
        salt = hashlib.sha512(f'KuncH3nH0nd4K1t4P@ssw0rd{expires.isoformat()}'.encode('utf-8')).hexdigest()
        vals = {
            'name': 'generate_jwt',
            'token': jwt.encode(payload, salt, algorithm='HS256'),
            'expiration_date': expires,
            'scope': 'read write'
        }
        if is_force_create or is_create:
            grant_type_obj = self.env['tw.selection'].sudo().search([
                ('value','=','bearer'),
                ('type','=','GrantType')
            ], limit=1)
            vals.update({
                'user_id': user.id,
                'grant_type_id': grant_type_obj.id
            })
            access_token_obj = oauth.sudo().create(vals)
            del vals['user_id']
            del vals['grant_type_id']
        else:
            oauth = oauth.sudo().write(vals)
        del vals['name']
        del vals['expiration_date']
        vals.update({'expires': timedelta(seconds=expired_time).seconds})

        return vals

    # TODO: SPJ - Seharusnya bisa 1 saja dengan yang di file Oauth Provider
    def _refresh_jwt(self):
        """
        TODO: should implement refresh token, therefore client could
            retrieve token if the current request is less than refresh expired time
        """

        refresh = False
        try:
            expires = datetime.now() + timedelta(seconds=1200)
            salt = hashlib.sha512('KuncH3nH0nd4K1t4P@ssw0rd%s' % expires.isoformat()).hexdigest()
            refresh = jwt.decode(self.token, salt, algorithm=['HS256'])
        
        except ExpiredSignatureError as err:
            _logger.warning(err.args[0])
            refresh = self._generate_jwt(self.user_id.id, {
                'grant_type': self.grant_type,
                'client_id': self.client_id,
                'client_secret': self.client_secret,
            })

        if self.client_id == refresh.get('client_id') and self.client_secret == refresh.get('client_secret'):
            expires = datetime.now() + timedelta(seconds=1200)
            refresh = self.sudo().write({
                'expires': expires.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
            })
        
        return refresh
