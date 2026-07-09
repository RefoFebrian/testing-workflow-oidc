from odoo import models, fields
from odoo.exceptions import UserError as Warning
from datetime import datetime

class TWBankTransferApproval(models.Model):
    _name = "tw.bank.transfer"
    _inherit = ['tw.bank.transfer', 'tw.approval.mixin']
    
    state = fields.Selection(selection_add=[
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('posted',),
        ('done','Done'),
        ('reject','Rejected'),
    ])

    def action_request_approval(self):
        self.ensure_one()
        self._validate_bank_transfer()
        self._check_branch_config()
        super().action_request_approval(value=self.amount_total)
