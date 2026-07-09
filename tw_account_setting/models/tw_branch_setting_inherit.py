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


class TwAccountBranchSetting(models.Model):
    _inherit = "tw.branch.setting"
    _description = 'Branch Setting'

    account_setting_id = fields.Many2one('tw.account.setting', string='Account Setting')
    inter_company_account_id = fields.Many2one('account.account', string='Account Intercompany')