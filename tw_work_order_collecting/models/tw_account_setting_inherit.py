# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwAccountSetting(models.Model):
    _inherit = "tw.account.setting"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    journal_wo_collecting_claim_id = fields.Many2one(
        'account.journal', 'Journal Collecting Piutang Claim',
        help="Field ini digunakan untuk setting account journal. "
             "pada transaksi Collecting piutang claim"
    )

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods