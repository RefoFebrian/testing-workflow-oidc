# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class MasterIncentive(models.Model):
    _name = "tw.master.incentive"
    _inherit = ["tw.master.incentive", "tw.approval.mixin"]

    # 7: defaults methods
    
    # 8: fields
    amount_total = fields.Float(default=1.0, string='Total Amount', help="A dummy field to trigger approval matrix")
    state = fields.Selection(selection_add=[
        ('draft', 'Draft'),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved', 'Approved'),
        ('active',),
        ('expired',),
    ], string='Status')
    
    # 9: relation fields
    approval_ids = fields.One2many(
        comodel_name='tw.approval.line',
        inverse_name='transaction_id',
        string='Approval',
        domain=[('model_id', '=', _inherit)]
    )

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods

    # 13: action methods
    def action_confirm(self):
        self.action_active()

    def action_request_approval(self):
        self.ensure_one()
        return super().action_request_approval(code='other')
    
    # 14: private methods
