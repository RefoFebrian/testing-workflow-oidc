from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning


class InheritBirojasaBillingProcess(models.Model):
    _name = "tw.birojasa.billing.process"
    _inherit = ["tw.birojasa.billing.process", "tw.approval.mixin"]

    state = fields.Selection(selection_add=[
        ('draft',),
        ('confirmed',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('done',),
        ('cancel',),
    ], string="Status")
    
    def get_state(self):
        return 'approved'

    def validate_order(self):
        self._validate_order()
        return super().validate_order()
        
    def action_request_approval(self):
        self.ensure_one()
        return super().action_request_approval(code='other', value=self.correction_amount)
    