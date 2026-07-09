# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class TwPurchaseReturnApproval(models.Model):
    _name = "tw.purchase.return"
    _inherit = ["tw.purchase.return", "tw.approval.mixin"]

    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('approved', 'Approved'),
        ('sale',),
        ('cancel')
    ], string="Status")

    def action_request_approval(self):
        self.ensure_one()
        return super().action_request_approval(code='purchase')
    
    def validate_order(self):
        self._validate_order()
        return super().validate_order()