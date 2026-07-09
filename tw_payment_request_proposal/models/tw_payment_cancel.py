# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
from odoo.fields import Command

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwPaymentCancelProposal(models.Model):
    _inherit = "tw.payment.cancel"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods

    def action_confirm(self):
        res = super().action_confirm()
        payment = self.account_payment_id
        if payment.proposal_id:
            # 1. Reverse the payment amounts in proposal lines
            for line in payment.line_dr_ids.filtered('proposal_line_id'):
                proposal_line = line.proposal_line_id.sudo()
                proposal_line.write({
                    'amount_paid': proposal_line.amount_paid - line.amount,
                    'amount_reserved': proposal_line.amount_reserved + line.amount
                })
                
                # 2. Remove the payment record from proposal line payments
                if hasattr(proposal_line, 'payment_ids'):
                    payment_rec = proposal_line.payment_ids.filtered(
                        lambda p: p.name == payment.name
                    )
                    if payment_rec:
                        payment_rec.unlink()
            
            # 3. Remove the main payment record
            payment_records = self.env['tw.proposal.payment'].search([
                ('proposal_id', '=', payment.proposal_id.id),
                ('payment_model_id', '=', payment.id)
            ])
            payment_records.unlink()
            
            # 4. Log the cancellation
            _logger.info(f"Payment {payment.name} for proposal {payment.proposal_id.name} has been cancelled")
            
        return res
    

    # 14: private methods 
    