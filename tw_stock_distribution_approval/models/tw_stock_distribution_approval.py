from odoo import models, fields
from odoo.exceptions import UserError as Warning
from datetime import datetime

class StockDistribution(models.Model):
    _name = "tw.stock.distribution"
    _inherit = ["tw.stock.distribution", "tw.approval.mixin"]
    
    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('open',),
        ('reject','Rejected'),
    ])

    def _get_state_value(self):
        # Mengambil value yang sesuai dengan key di state
        selection = self._fields.get('state') and self._fields['state'].selection
        return dict(selection).get(self.state, self.state) if selection else self.state

    def action_request_approval(self):
        if self.state not in ('draft'):
            raise UserError(f'Silakan refresh halaman ini, karena state sudah {self._get_state_value()}')
        self.ensure_one()
        self.is_approved_qty_zero()
        super().action_request_approval()

    def action_confirm_qty(self):
        total_approved_qty = sum(line.approved_qty for line in self.stock_distribution_ids)
        if total_approved_qty > 0:
            super().action_confirm_qty()
        else:
            self.reject_request()