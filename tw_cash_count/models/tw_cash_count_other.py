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

class TwCashCountOther(models.Model):
    _name = "tw.cash.count.other"
    _description = "Cash Count Other"

    # 7: defaults methods
    
    # 8: fields
    name = fields.Char('Description')
    amount = fields.Float('Amount')
    note = fields.Char('Keterangan')

    # 9: relation fields
    cash_count_id = fields.Many2one('tw.cash.count','Cash Count')

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods

    # 12: Override Methods

    # 13: Action Methods

    # 14: Private Methods