# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib



class TwBankTransferReconcileLine(models.Model): 
    _name = "tw.bank.transfer.reconcile.line"
    _description = 'Bank Transfer Reconciliation Line'

    
    # 7: defaults methods


    # 8: fields
    name = fields.Char(string="Name",readonly=True,store=True)
    ref_original = fields.Char(related='move_line_id.ref', string='Ref')
    date_original = fields.Date(related='move_line_id.date', string='Date')
    amount_original = fields.Float(string='Original Amount', store=True, digits='Account', compute='_compute_balance')

    # 9: relation fields
    bank_transfer_id = fields.Many2one('tw.bank.transfer',string="Bank Transfer", required=True)
    move_line_id = fields.Many2one('account.move.line', string='Journal Item', required=True)   

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('move_line_id')
    def _compute_balance(self):
        for data in self:
            move_line = data.move_line_id or False

            if not move_line:
                data.amount_original = 0.0
                data.name = ""
            else :
                data.amount_original = move_line.debit - move_line.credit
                data.name = move_line.name

    @api.onchange('move_line_id')
    def onchange_move_line_id(self):

        self.name = False
        self.ref_original = False
        self.date_original = False
        self.amount_original = False

        if self.move_line_id :
                self.name = self.move_line_id.name
                self.ref_original = self.move_line_id.ref
                self.date_original = self.move_line_id.date
                self.amount_original = self.move_line_id.debit - self.move_line_id.credit

    # 12: override methods

    # 13: action methods

    # 14: private methods

    
             
