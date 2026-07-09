# -*- coding: utf-8 -*-

from odoo import models, fields


class tw_vehicle_document_update_data_approval(models.Model):
    _name = "tw.vehicle.document.update.data"
    _inherit = ["tw.vehicle.document.update.data","tw.approval.mixin"]
    
    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ("confirm", "Confirmed"),
        ('cancel',),
    ], string="Status")

    def action_request_approval(self):
        self.ensure_one()
        self._action_request()
        return super().action_request_approval(code='other',value=5)
    
    def action_approval(self):
        return super().action_approval()
    

