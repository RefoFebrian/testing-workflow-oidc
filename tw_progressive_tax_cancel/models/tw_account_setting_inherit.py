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


class TwProgressiveTaxCancelAccountSetting(models.Model):
    _inherit = "tw.account.setting"
    _description = 'Account Setting'

    journal_progressive_tax_cancel_id = fields.Many2one('account.journal', string='Journal Pembatalan Pajak Progressive', help='Journal pembatalan pajak progressive')