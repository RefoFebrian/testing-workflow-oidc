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


class NetOffApproval(models.Model):
    _name = "tw.net.off"
    _inherit = ["tw.net.off","tw.approval.mixin"]

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
        # Mengajukan permintaan approval
        return super().action_request_approval(max(self.total_debit,self.total_credit))
        