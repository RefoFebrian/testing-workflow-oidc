# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib


class TwSalesProgramInherit(models.Model):
    _name = "tw.sales.program"
    _inherit = ["tw.sales.program", "tw.approval.mixin"]

    # 7: defaults methods

    # 8: fields

    # Audit Trail
    confirm_uid = fields.Many2one('res.users',string='Confirmed by')
    confirm_date = fields.Datetime('Confirmed on')

    # 9: relation fields
    approval_ids = fields.One2many('tw.approval.line', 'transaction_id', string='Approval', domain=[('model_id','=',_inherit)])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_rfa(self):
        for data in self:
            if len(data.line_ids) < 1:
                raise UserError(_('Sales Program Lines must be fill.'))
        amount = self.promo_value or 0.0
        self.action_request_approval(value=amount)
        return True
    
    def action_approve(self):
        self.action_approval()
        
    def action_revise(self):
        if self.state == 'approved':
            self.write({'state': 'editable'})
        else:
            self.write({'state': 'on_revision'})
        return True

    def _get_amount_field(self):
        return "promo_value"
    
    # 14: private methods
    def get_approve_additional_vals(self):
        self.ensure_one()
        return {
            'confirm_uid': self._uid,
            'confirm_date': datetime.now(),
            'state': 'approved'
        }