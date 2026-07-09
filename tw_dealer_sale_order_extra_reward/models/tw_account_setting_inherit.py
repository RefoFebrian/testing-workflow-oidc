# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

class TwAccountSettingInherit(models.Model):
    _inherit = "tw.account.setting"

    journal_dso_extra_reward_id = fields.Many2one('account.journal', 'Journal Extra Reward', help='Select a Journal for Extra Reward')
    