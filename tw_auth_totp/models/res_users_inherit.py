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

class InheritResUsersAuthTotp(models.Model):
    _inherit = "res.users"

    is_mandatory_mfa = fields.Boolean(string='Mandatory MFA?',default=False,help='Mandatory MFA for this user')