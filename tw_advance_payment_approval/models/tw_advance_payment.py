from odoo import models, fields
from odoo.exceptions import UserError as Warning
from datetime import datetime

class TwAdvancePaymentApproval(models.Model):
    _name = "tw.advance.payment"
    _inherit = ["tw.advance.payment","tw.approval.mixin"]
    
    def action_request_approval(self,value=False,code='other', **kwargs):
        self.ensure_one()
        self._create_line_avp()
        if self.amount <= 0:
            raise Warning('The amount cannot be less than or equal to 0')
        
        if hasattr(self, '_check_proposal_state'):
            self._check_proposal_state()
        if hasattr(self, '_check_proposal_amount'):
            self._check_proposal_amount()

        return super().action_request_approval(self.amount,'payment')
    
    def action_reject_or_cancel(self):
        if hasattr(self, '_unset_amount_reserved'):
            self._unset_amount_reserved()
        return super().action_reject_or_cancel()
