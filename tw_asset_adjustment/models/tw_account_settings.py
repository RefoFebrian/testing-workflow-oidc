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


class TwAssetAdjustmentAccountSetting(models.Model):
    _inherit = "tw.account.setting"
    _description = 'Account Setting'

    journal_asset_adjustment_id = fields.Many2one('account.journal', string='Journal Asset Adjustment',help='Journal Asset Adjustment')