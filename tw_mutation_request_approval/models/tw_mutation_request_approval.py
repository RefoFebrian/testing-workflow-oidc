from datetime import datetime
from odoo import models,fields
from odoo.exceptions import UserError


class ApprovalMutationRequest(models.Model):
    _name = "tw.mutation.request"
    _inherit = ["tw.mutation.request","tw.approval.mixin"]

    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('confirm',),
        ('open',),
        ('done',),
        ('reject','Rejected'),
    ])
    
    def action_rfa(self):
        self._check_valid_request()
        # Permintaan persetujuan berdasarkan nilai total
        return super().action_request_approval(value=self.amount_total)

    def action_approval(self):
        approve = super().action_approval()
        self.action_confirm_order()
        return approve


        