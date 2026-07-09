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

class TwCashCountValidation(models.Model):
    _name = "tw.cash.count.validation"
    _description = "Cash Count Validation"

    # 7: defaults methods

    # 8: fields
    name = fields.Char('Name')
    type = fields.Selection([
        ('cash','Cash'),
        ('petty_cash','Petty Cash'),
        ('reimburse_petty_cash','Reimburse Petty Cash')])
    note = fields.Char('Note')

    # 9: relation fields

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods
