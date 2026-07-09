# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwMasterExpenseSource(models.Model):
    _name = "tw.master.expense.source"
    _description = "Master Expense Source"
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    
    expense_source_id = fields.Many2one('tw.selection', string='Expense Source', domain=[('type', '=', 'ExpenseSource')])
    account_id = fields.Many2one('account.account', string='Account')
    is_nc = fields.Boolean(string='Is Payment Request', compute='_compute_is_nc')

    @api.depends('expense_source_id')
    def _compute_is_nc(self):
        for rec in self:
            rec.is_nc = rec.expense_source_id.value == 'NC'

    @api.constrains('expense_source_id', 'account_id')
    def _check_account_id_required_for_nc(self):
        for rec in self:
            if rec.expense_source_id.value == 'NC' and not rec.account_id:
                raise Warning(_("Account is required when Expense Source is Payment Request (NC)."))
    