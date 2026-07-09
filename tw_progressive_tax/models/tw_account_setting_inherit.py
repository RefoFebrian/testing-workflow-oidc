# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, timedelta, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwAccountSettingInherit(models.Model):
    _inherit = "tw.account.setting"
    _description = "TW Account Setting"
   
    # 8: fields
    journal_birojasa_progressive_id = fields.Many2one('account.journal',string="Journal Pajak Progressive",domain="[('type','!=','view')]",help="Journal ini dibutuhkan saat proses Tagihan Biro Jasa, jika Unitnya memiliki pajak progressive.")