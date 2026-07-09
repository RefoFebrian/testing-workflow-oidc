# -*- coding: utf-8 -*-
import base64
import hashlib
from datetime import datetime
from odoo import models, fields

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
from pytz import timezone

class Users(models.Model):
    _inherit = "res.users"

    client_id = fields.Char(string='Client ID')
    client_secret = fields.Char(string='Client Secret')
    credential_public_file = fields.Binary(string='Creds Public File', help='Used as public key file to crypt or decrypt RSA alike')
    credential_public_filename = fields.Char(string='Creds Public Filename')
    credential_private_file = fields.Binary(string='Creds Private File', help='Used as private key file to crypt or decrypt RSA alike')
    credential_private_filename = fields.Char(string='Creds Private Filename')

    def action_generate_user_api_credentials(self):
        if not self.client_id and not self.client_secret:
            self.client_id = hashlib.sha224(f'{self.partner_id.name}|{datetime.now().isoformat()}'.encode()).hexdigest()
            self.client_secret = hashlib.sha224(f'{self.login}|{datetime.now().isoformat()}'.encode()).hexdigest()
        else:
            self.client_id = False
            self.client_secret = False

    def action_generate_key_pair(self):
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        timestamp = datetime.now(timezone('Asia/Jakarta')).strftime('%Y%m%d%H%M%S')

        self.credential_public_file = self._generate_public_key(key)
        self.credential_private_file = self._generate_private_key(key)
        self.credential_public_filename = f'{self.login}_{timestamp}_public.pem'
        self.credential_private_filename = f'{self.login}_{timestamp}_private.pem'

    def _generate_public_key(self, key):
        return base64.encodebytes(key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        ))
    
    def _generate_private_key(self, key):
        return base64.encodebytes(key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
        ))
