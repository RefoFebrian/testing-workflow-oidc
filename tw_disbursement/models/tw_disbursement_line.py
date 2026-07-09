# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import re

# 2: import of known third party lib
from datetime import date, timedelta, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib

class TwDisbursementLine(models.Model):
    _name = "tw.disbursement.line"
    _description = "Disbursement EDC Line"
    
    # 7: defaults methods

    # 8: fields
    name = fields.Char(string="Name")
    ref = fields.Char(string="Reference")
    debit = fields.Float(string="Amount", digits='Account')

    # 9: relation fields
    disbursement_id = fields.Many2one('tw.disbursement',string="Disbursement",ondelete='cascade')
    move_line_id = fields.Many2one('account.move.line',string="Move Line")
    account_id = fields.Many2one('account.account',string="Account")
    partner_id = fields.Many2one('res.partner',string="Partner")

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('unique_name_move_line_id', 'unique(disbursement_id,move_line_id)', 'move line must be unique!')
    ]

    # 11: compute/depends & on change methods
    @api.onchange('move_line_id')
    def onchange_move_line(self):
        if self.move_line_id :
            self.partner_id = self.move_line_id.partner_id.id
            self.account_id = self.move_line_id.account_id.id            
            self.debit = self.move_line_id.debit
            self.ref = self.move_line_id.ref

    # 12: override methods  

    # 13: action methods

    # 14: private methods
    
