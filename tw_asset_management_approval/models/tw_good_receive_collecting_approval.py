from odoo import models, fields
from odoo.exceptions import UserError as Warning
from datetime import datetime

class GoodReceiveCollectingApproval(models.Model):
    _name = "tw.good.receive.collecting"
    _inherit = ["tw.good.receive.collecting", "tw.approval.mixin"]
    
    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('open',),
        ('done',),
        ('cancel',),
    ])

    approval_ids = fields.One2many('tw.approval.line', 'transaction_id', string="Table Approval", domain=[('model_id', '=', _name)])
    def action_request_approval(self):
        if self.state != 'draft':
            raise UserError(f'Silakan refresh halaman ini, karena state telah {self._get_state_value()}')
        
        self.ensure_one()
        return super().action_request_approval(value=self.amount_total)