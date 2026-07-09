from odoo import models, fields
from odoo.exceptions import UserError as Warning
from datetime import datetime

class TWCashCountApproval(models.Model):
    _name = "tw.cash.count"
    _inherit = ['tw.cash.count', 'tw.approval.mixin']
    
    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('posted',),
        ('reject','Rejected'),
    ])

    def action_request_approval(self):
        self.ensure_one()

        super().action_request_approval(value=5)
