# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class AuthOauthProvider(models.Model):
    _inherit = "auth.oauth.provider"

    url_mfa = fields.Char(string='URL MFA')
    notify_mfa = fields.Boolean(string='MFA Notifikasi?',default=False)