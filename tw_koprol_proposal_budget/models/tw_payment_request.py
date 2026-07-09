from odoo import models, fields, api

class InheritTwPaymentRequest(models.Model):
    _inherit = "tw.payment.request"

    # Fields
    initial_budget_amount = fields.Float('Initial Budget Amount', digits='Product Price')
    reserved_budget_amount = fields.Float('Reserved Budget Amount', digits='Product Price')
    realization_budget_amount = fields.Float('Realization Budget Amount', digits='Product Price')
    available_budget_amount = fields.Float('Available Budget Amount', digits='Product Price')
    
    # Relation Fields
    budget_proposal_line_id = fields.Many2one('tw.budget.proposal.line', string='Budget Proposal Line')

    @api.depends('company_id', 'division')
    def _compute_proposal_domain(self):
        for rec in self:
            is_koprol = self._context.get('is_koprol', False)
            if is_koprol:
                domain = [('id', '=', 0),('budget_proposal_line_id', '=', 0)]
                proposal_ids = []
                if rec.company_id and rec.division:
                    proposal_model_id = self.env['ir.model'].sudo().search([('model', '=', 'tw.proposal')]).id
                    get_proposal_query = """
                        SELECT DISTINCT
                            prop.id
                        FROM tw_proposal prop
                        JOIN tw_approval_line al ON al.transaction_id = prop.id AND al.model_id = %s
                        WHERE prop.company_id = %s
                        AND prop.division = %s
                        AND (
                            prop.state = 'approved' 
                            OR (prop.state = 'waiting_for_approval' AND prop.amount_approved >= %s AND prop.is_deviation = True)
                        )
                    """
                    self._cr.execute(get_proposal_query, (
                        proposal_model_id, 
                        rec.company_id.id, 
                        rec.division, 
                        self.MIN_LIMIT
                    ))
                    proposal_ress = self._cr.fetchall()
                    if proposal_ress:
                        budget_obj = self.env['tw.budget.proposal.line'].suspend_security().search([
                            ('budget_proposal_id.company_id','=', rec.company_id.id),
                            ('budget_proposal_id.division','=', rec.division.upper())
                        ])
                        ids_budget = budget_obj.ids if budget_obj else [0]
                        proposal_ids = [p[0] for p in proposal_ress]
                        domain = [('id', 'in', proposal_ids),('budget_proposal_line_id', 'in', ids_bugdet)]
                rec.proposal_domain = domain
            else:
                return super()._compute_proposal_domain()
            