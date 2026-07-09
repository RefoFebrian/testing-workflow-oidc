# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class InheritAccountPaymentProposal(models.Model):
    _inherit = "tw.account.payment"

    # 8: fields
    proposal_domain = fields.Binary(compute='_compute_proposal_domain', store=False, readonly=True, default=lambda self: [('id', '=', 0)])
    proposal_limit_amount = fields.Float(string='Limit Proposal', digits='Product Price', help='Limit yang bisa dibayarkan melalui Payment Request (Yang dibayarkan langsung ke vendor)')
    proposal_total_amount = fields.Float(string='Total Proposal', digits='Product Price', help='Total amount dari proposal')
    proposal_state = fields.Selection([
        ('-','-'),
        ('under','UNDER BUDGET'),
        ('on','ON BUDGET'),
        ('over','OVER BUDGET'),
        ('reject','REJECTED'),
        ('close','CLOSED')
    ], string='Status Proposal', compute='_compute_proposal_state')

    # 9: relation fields
    proposal_id = fields.Many2one('tw.proposal', string='Proposal')

    MIN_LIMIT = 10000000 # COO

     
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('proposal_id.state', 'proposal_limit_amount', 'amount_total', 'proposal_total_amount')
    def _compute_proposal_state(self):
        for rec in self:
            if rec.proposal_id:
                if rec.proposal_id.state == 'reject' and rec.state in ['draft', 'waiting_for_approval', 'approved']:
                    rec.proposal_state = 'reject'
                elif rec.proposal_id.state == 'close' and rec.state in ['draft', 'waiting_for_approval', 'approved']:
                    rec.proposal_state = 'close'
                elif rec.proposal_limit_amount:
                    # Priority: compare current payment amount against remaining limit
                    if rec.amount_total < rec.proposal_limit_amount:
                        rec.proposal_state = 'under'
                    elif rec.amount_total == rec.proposal_limit_amount:
                        rec.proposal_state = 'on'
                    elif rec.amount_total > rec.proposal_limit_amount:
                        rec.proposal_state = 'over'
                    else:
                        rec.proposal_state = '-'
                else:
                    rec.proposal_state = '-'
            else:
                rec.proposal_state = '-'
            
    @api.depends('company_id', 'division')
    def _compute_proposal_domain(self):
        for rec in self:
            domain = [('id', '=', 0)]
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
                    proposal_ids = [p[0] for p in proposal_ress]
                    domain = [('id', 'in', proposal_ids)]
            rec.proposal_domain = domain
    # 12: override methods

    # 13: action methods
    def action_update_proposal_limit(self):
        pay_to = self._get_proposal_pay_to()
        total, paid, reserved = self.proposal_id.get_proposal_amounts_by_pay_to(pay_to)
        self.proposal_total_amount = total
        self.proposal_limit_amount = total - (paid + reserved)
    
    def action_validate(self):
        result = super().action_validate()
        # Setelah Account Payment confirm & reconcile, update PR/AVP terkait
        for payment in self:
            payment._update_related_payment_ids()
        return result

    # 14: private methods
    def _check_proposal_amount(self):
        if not self.proposal_id:
            return
            
        amount = self.amount_total
        pay_to = self._get_proposal_pay_to()
        
        total, paid, reserved = self.proposal_id.get_proposal_amounts_by_pay_to(pay_to)
        
        amount_limit = total - (paid + reserved)

        if amount > amount_limit:
            raise Warning('Total amount (%s) tidak boleh melebihi limit proposal (%s) untuk category %s.' % (amount, amount_limit, pay_to.upper()))

    def _check_proposal_state(self):
        if self.proposal_id.state == 'reject':
            raise Warning('Status %s REJECTED' % (self.proposal_id.name))
        elif self.proposal_id.state == 'close':
            raise Warning('Status %s CLOSED' % (self.proposal_id.name))
        
        
    def _get_proposal_limit(self):
        if self.proposal_id:
            pay_to = self._get_proposal_pay_to()
            total, paid, reserved = self.proposal_id.get_proposal_amounts_by_pay_to(pay_to)
            return total - (paid + reserved)
        return 0

    def _get_proposal_pay_to(self):
        """
        Determine if the payment is for Vendor (Advance Payment) or PIC (Direct Account Payment).
        """
        # Advance Payment handles vendor lines
        if hasattr(self, 'type') and self.type == 'advance_payment':
            return 'pic'
        # Default for direct account payment linked to proposal is PIC
        return 'vendor'

    def _update_related_payment_ids(self):
        """
        cari PR/AVP dari payment lines,
        ambil amount dari line.amount.
        Update proposal amount_paid.
        """
        if not self.move_id:
            return

        proposals = self.env['tw.proposal']

        for line in self.line_ids:
            if not line.move_line_id:
                continue

            move = line.move_line_id.move_id
            paid_amount = line.amount

            # === Payment Request ===
            pr = self._update_request_payment(move.id,'tw.payment.request')
            if pr:
                if hasattr(pr, '_update_proposal_amount_paid'):
                    pr._update_proposal_amount_paid(paid_amount)
                proposals |= pr.proposal_id
                continue

            # === Advance Payment ===
            avp = self._update_request_payment(move.id,'tw.advance.payment')
            if avp:
                if hasattr(avp, '_update_proposal_amount_paid'):
                    avp._update_proposal_amount_paid(paid_amount)
                proposals |= avp.proposal_id

        # Update proposal state done
        for proposal in proposals:
            proposal.suspend_security()._compute_state_done()

    def _update_request_payment(self,move_id,model):
        pr = self.env[model].suspend_security().search([
                ('move_id', '=', move_id),
                ('proposal_id', '!=', False),
            ], limit=1)
        return pr
