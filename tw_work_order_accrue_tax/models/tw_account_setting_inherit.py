# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools import float_compare, float_is_zero

# 5: local imports

# 6: Import of unknown third party lib

class AccountSettingInherit(models.Model):
    _inherit = "tw.account.setting"

    journal_wo_accrue_tax_id = fields.Many2one('account.journal','Journal Accrue Tax', 
        help="Field ini digunakan untuk setting account journal. "
            "pada transaksi Accrue Tax")