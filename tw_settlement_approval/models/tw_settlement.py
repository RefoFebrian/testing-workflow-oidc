from odoo import models, fields
from odoo.exceptions import UserError as Warning
from datetime import datetime

class TWSettlementApproval(models.Model):
    _name = "tw.settlement"
    _inherit = ['tw.settlement', 'tw.approval.mixin']
    
    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('done',),
        ('reject','Rejected'),
    ])

    def action_request_approval(self):
        self.ensure_one()
        self._check_branch_config()
        self.check_amount_total()
        super().action_request_approval(value=self.amount_total)
