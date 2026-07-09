# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

class TwAccountSettingInherit(models.Model):
    _inherit = "tw.account.setting"

    # 8: fields

    # 9: relation fields
    journal_dso_direct_gift_md_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal Direct Gift MD',
        help="This journal setting will be used as the account in the direct gift subsidy program")
    journal_direct_gift_finco_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal Direct Gift Finco',
        help="This journal setting will be used as the account in the direct gift subsidy program")