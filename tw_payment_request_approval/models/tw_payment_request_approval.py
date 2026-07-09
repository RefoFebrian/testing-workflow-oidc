# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class InheritAccountPaymentRequestApproval(models.Model):
    _name = "tw.payment.request"
    _inherit = ["tw.payment.request","tw.approval.mixin"]

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_request_approval(self,value=False,code='other', **kwargs):
        self._update_amount_based_on_total_amount()
        self._validate_amount()
        amount = self._get_approval_amount()
        return super().action_request_approval(amount, code)
    
    def _get_approval_code(self):
        code = super()._get_approval_code()
        if self.type == 'other_receivable':
            code = 'other'
        return code
    
    def _get_approval_amount(self):
        total = 0.0
        for line in self.line_dr_ids :
            total += line.amount
        return total