# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.tools import SQL
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwAccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    is_require_bank_account = fields.Boolean('Require Bank Account')
    is_require_account_number = fields.Boolean('Require Account Number')

    @api.onchange('is_require_bank_account', 'is_require_account_number')
    def _onchange_is_require(self):
        if self.is_require_bank_account:
            self.is_require_account_number = False
        if self.is_require_account_number:
            self.is_require_bank_account = False