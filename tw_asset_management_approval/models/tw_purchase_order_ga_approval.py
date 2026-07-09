from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning


class InheritPurchaseOrderAsset(models.Model):
    _name = "purchase.order.asset"
    _inherit = ["purchase.order.asset", "tw.approval.mixin"]
    
    def approval_domain(self):
        return [('model_id', '=', self._name)]

    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('purchase',),
    ], string="Status")

    approval_ids = fields.One2many(
        comodel_name='tw.approval.line',
        inverse_name='transaction_id',
        string="Approval List",
        domain=approval_domain,
        copy=False
    )
        
    def action_request_approval(self,code='other'):
        if self.state not in ('draft'):
            raise UserError(f'Gagal RFA! Silakan refresh halaman PO Asset ini, karena state sudah {self._get_state_value()}')
        self.ensure_one()
        
        return super(InheritPurchaseOrderAsset,self).action_request_approval(code='purchase')