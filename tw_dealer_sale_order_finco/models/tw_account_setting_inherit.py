# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

class TwAccountSettingInherit(models.Model):
    _inherit = "tw.account.setting"


    journal_dso_incentive_finco_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal Incentive Finco',
        help="This journal will be used to record transactions for finance company incentives.")