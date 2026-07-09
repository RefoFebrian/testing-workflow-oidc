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


class CollectingApproval(models.Model):
    _name = "tw.collecting"
    _inherit = ["tw.collecting","tw.approval.mixin"]

    # 8: fields
    state = fields.Selection(
        selection_add=[
            ('waiting_for_approval','Waiting For Approval'),
            ('approved','Approved'),
            ('confirm',)
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

    def action_request_approval(self):
        self._validate_amount()
        # Mengajukan permintaan approval
        return super().action_request_approval(self.amount)
        