from odoo import models, fields, api

class BudgetPaymentProposal(models.Model):
    _name = "tw.budget.payment.proposal.line"
    _description = "Payment Budget Proposal"

    state = fields.Selection(related='payment_request_id.state', store=True)
    
    payment_request_id = fields.Many2one('tw.account.payment', string='Payment Request', ondelete='cascade', domain='[("type", "=", "payment_request")]')
    budget_proposal_line_id = fields.Many2one('tw.budget.proposal.line', string='Budget Proposal Line')