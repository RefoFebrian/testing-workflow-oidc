from odoo import models, fields, api
from odoo.exceptions import UserError as Warning


class BudgetProposalLine(models.Model):
    _name = "tw.budget.proposal.line"
    _description = "Detail Budget Proposal"

    proposal_category_code = fields.Char('Category')
    proposal_category_name = fields.Char('Category Name')
    initial_budget_amount = fields.Float('Initial Budget Amount')
    reserved_budget_amount = fields.Float('Reserved Budget Amount')
    realization_budget_amount = fields.Float('Realization Budget Amount')
    available_budget_amount = fields.Float('Available Budget Amount')

    budget_proposal_id = fields.Many2one('tw.budget.proposal', string='Budget Proposal')
    budget_payment_ids = fields.One2many('tw.budget.payment.proposal.line', 'budget_proposal_line_id', string='Budget Payment Proposal')

    def name_get(self):
        if self._context is None:
            self._context = {}
        res = []
        for record in self:
            name = "[%s] %s" % (record.budget_proposal_id.reference, record.proposal_category_code)
            res.append((record.id, name))
        return res

