# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

class TwAccountSettingInherit(models.Model):
    _inherit = "tw.account.setting"

    account_activity_id = fields.Many2one('account.account', string='Account Activity Plan', help='Account HL Untuk Activity Plan')

    