# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# 4:  imports from odoo modules


# 5: local imports

# 6: Import of unknown third party lib

class InheritTwCheckReconcileLine(models.TransientModel):
    _name = "tw.check.reconcile.line"


    ref = fields.Char('Reference')
    date = fields.Date('Effective Date')
    partner = fields.Char('Partner')
    debit = fields.Char('Debit')
    credit = fields.Char('Credit')
    matching_number = fields.Char('Reconcile')
    
    check_reconcile_id = fields.Many2one('tw.check.reconcile', 'Check Reconcile')
    move_line_id = fields.Many2one('account.move.line', 'Move Line')
    account_id = fields.Many2one('account.account', 'Account')
    journal = fields.Many2one('account.journal', 'Journal')
    reconcile_id = fields.Many2one('account.partial.reconcile', 'Reconcile')
    