# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError,UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwAdvancePaymentProposal(models.Model):
    _name = "tw.advance.payment.proposal"
    _description = "Advance Payment - Proposal"
    
    # 7: defaults methods

    # 8: fields
    amount_proposal = fields.Float(string='Amount Proposal', digits='Product Price')
    amount_total = fields.Float(string='Amount', digits='Product Price')

    # 9: relation fields
    advance_payment_id = fields.Many2one('tw.advance.payment', string="ID Payment", ondelete='cascade')
    proposal_line_id = fields.Many2one('tw.proposal.line', string='Item Proposal', ondelete='restrict')

    # 10: constraints & sql constraints
    _sql_constraints = [('proposal_line_id_uniq', 'unique(advance_payment_id, proposal_line_id)', "Item proposal tidak boleh duplikat.")]

    @api.constrains('amount_total')
    def _check_amount(self):
        for record in self:
            if record.amount_total <= 0:
                raise ValidationError("Amount %s tidak boleh 0." % (record.proposal_line_id.description))
    
    # 11: compute/depends & on change methods
    @api.onchange('proposal_line_id')
    def _onchange_proposal_line(self):
        self.amount_total = 0
        self.amount_proposal = 0
        if self.proposal_line_id:
            self.amount_total = self.proposal_line_id.amount_total - (self.proposal_line_id.amount_reserved + self.proposal_line_id.amount_paid)
            self.amount_proposal = self.proposal_line_id.amount_total
            if self.amount_total < 0:
                self.amount_total = 0
    
    @api.onchange('amount_total')
    def _onchange_amount_total(self):       
        if self.amount_total > self.amount_proposal:
            raise Warning("Amount %s tidak boleh melebihi amount proposal." % (self.proposal_line_id.description))
