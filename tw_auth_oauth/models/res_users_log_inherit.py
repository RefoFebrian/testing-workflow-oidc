# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date
import requests

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError as Warning, AccessDenied, AccessError, ValidationError
from odoo import SUPERUSER_ID
# 5: local imports

# 6: Import of unknown third party lib

import logging

_logger = logging.getLogger(__name__)

class ResUsersLog(models.Model):
    _inherit = "res.users.log"

    type = fields.Selection([
        ('normal', 'Normal'),
        ('oauth', 'OAuth'),
    ], string='Type', default='normal')