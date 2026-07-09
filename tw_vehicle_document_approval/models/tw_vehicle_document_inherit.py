from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning


class InheritVehicleDocumentRequest(models.Model):
    _name = "tw.vehicle.document.request"
    _inherit = ["tw.vehicle.document.request", "tw.approval.mixin"]

    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('done',),
        ('cancel',),
    ], string="Status")
    
    def validate_order(self):
        self._validate_order()
        return super().validate_order()
        
    def action_request_approval(self):
        self.ensure_one()
        return super().action_request_approval(code='other', value=10)
    
    def _validate_state_confirm(self):
        state = super()._validate_state_confirm()
        if self.is_exception_faktur:
            return ['approved']
        return state