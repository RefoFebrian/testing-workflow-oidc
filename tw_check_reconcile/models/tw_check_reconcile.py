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

class InheritTwCheckReconcile(models.TransientModel):
    _name = "tw.check.reconcile"
    _description = "Tw Check Reconcile"
    _rec_name = 'move_id'

    move_id = fields.Many2one('account.move', 'Move')
    company_id = fields.Many2one("res.company", "Branch")
    matching_number = fields.Char('Matching Number')
    check_reconcile_line_ids = fields.One2many('tw.check.reconcile.line', 'check_reconcile_id', 'Check Reconcile Lines')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.move_id = False

    @api.onchange('matching_number','company_id')
    def _onchange_matching_number(self):
        self.check_reconcile_line_ids = False
        data_line_ids = []
        if self.matching_number:
            check_reconcile_ids = self.env['account.move.line'].suspend_security().search([('matching_number', '=', self.matching_number), ('company_id', '=', self.company_id.id)])
            for line in check_reconcile_ids:
                data_line_ids.append([0, 0, {
                    'check_reconcile_id': self.id,
                    'move_line_id': line.id,
                    'matching_number': line.matching_number,
                    'journal': line.journal_id.id,
                    'account_id': line.account_id.id,
                    'ref': line.ref,
                    'date': line.date,
                    'partner': line.partner_id.name,
                    'debit': line.debit,
                    'credit': line.credit,
                }])
        self.check_reconcile_line_ids = data_line_ids
            

    @api.onchange('move_id','company_id')
    def _onchange_move_id(self):
        lines = []
        self.matching_number = False
        self.check_reconcile_line_ids = False
        for line in self.move_id.line_ids:
            lines += line._all_reconciled_lines().filtered(lambda l: l.matched_debit_ids or l.matched_credit_ids)
        
        if self.matching_number and lines:
            lines = lines.filtered(lambda l: l.matching_number == self.matching_number)
        
        data_line_ids = []
        for line in lines:
            data_line_ids.append([0, 0, {
                'check_reconcile_id': self.id,
                'move_line_id': line.id,
                'matching_number': line.matching_number,
                'journal': line.journal_id.id,
                'account_id': line.account_id.id,
                'ref': line.ref,
                'date': line.date,
                'partner': line.partner_id.name,
                'debit': line.debit,
                'credit': line.credit,
            }])
        self.check_reconcile_line_ids = data_line_ids
        
    