# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions

from odoo.exceptions import UserError as Warning

from datetime import datetime, date

import logging
_logger = logging.getLogger(__name__)

class InheritProductPricelistItemApproval(models.Model):
    _name = "product.pricelist.item"
    _inherit = ["product.pricelist.item","tw.approval.mixin"]

    # 8: fields
    state = fields.Selection(
        selection_add=[
            ('waiting_for_approval','Waiting For Approval'),
            ('approved','Approved'),
            ('active',)
        ], 
        ondelete={
            'waiting_for_approval': 'set default',
            'approved': 'set default',
        }
    )

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_confirm_update_price(self):
        self.ensure_one()
        self.action_request_approval()
    
    def action_request_approval(self):
        # Mengajukan permintaan approval
        return super().action_request_approval(5)
    
    def action_approval(self):
        self.ensure_one()
        approval = super().action_approval()
        if self.state == 'approved':
            return self._action_confirm_update_price()
        return approval
        
    # 14: private methods