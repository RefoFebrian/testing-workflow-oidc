# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwInheritBranchSetting(models.Model):
    _inherit = "tw.branch.setting"

    # 7: defaults methods

    # 8: fields
    plafon_petty_cash_sr = fields.Float('Plafon Petty Cash SR')
    plafon_petty_cash_ws = fields.Float('Plafon Petty Cash WS')
    plafon_petty_cash_atl_btl = fields.Float('Plafon Petty Cash ATL/BTL')

    