# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TwMrpApproval(models.Model):
    _name = "mrp.production"
    _inherit = ["mrp.production",'tw.approval.mixin']

    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('confirmed',),
        ('progress',),
        ('done',),
        ('reject','Rejected'),
    ])

    def action_request_approval(self):
        self.ensure_one()
        self.validate_bundling_production()
        self.validate_bundling_stock()
        return super().action_request_approval(code='other', value=5)

    def action_approval(self):
        return super().action_approval()
    
    

