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


class TwAccountSetting(models.Model):
    _inherit = "tw.account.setting"
    _description = 'Account Setting'

    # 7: defaults methods

    # 8: fields
    journal_customer_bbn_id = fields.Many2one('account.journal',string="Journal BBN Jual",domain="[('type','!=','view')]",help="Journal ini dibutuhkan saat proses pengurusan STNK & BPKB Unit Off The Road ke On The Road , hasilnya akan menjadi Customer Invoice dengan nama Customer 'Biro Jasa' yang dipilih")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
