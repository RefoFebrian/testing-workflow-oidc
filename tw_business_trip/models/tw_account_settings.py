# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwBusiness_tripAccountSetting(models.Model):
    _inherit = "tw.account.setting"
    _description = 'Account Setting'

    account_payment_request_saku_id = fields.Many2one('account.account','Account Payment Request Uang Saku',help="Account Payment Request Uang Saku") 
    account_payment_request_akomondasi_id = fields.Many2one('account.account','Account Payment Request Uang Akomondasi',help="Account Payment Request Uang Akomondasi") 