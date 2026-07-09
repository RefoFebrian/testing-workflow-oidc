# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    # 7: defaults methods
    def _get_period(self):
        period_obj = self.env['tw.account.period']._get_current_periods()
        return period_obj.id

    # 8: fields

    # 9: relation fields
    period_id = fields.Many2one('tw.account.period', 'Period')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['period_id'] = vals['period_id'] if 'period_id' in vals else self.with_company(vals.get('company_id',False))._get_period()
            
        return super(AccountMoveInherit, self).create(vals_list)

    # 13: action methods
    def action_post(self):
        result = super(AccountMoveInherit, self).action_post()
        for move in self:
            if not move.period_id:
                period_obj = move.with_company(move.company_id.id).period_id._get_current_periods(date=move.date)
                if period_obj:
                    if period_obj.state == 'done':
                        raise ValidationError(_('Failed to Post Move, Period already closed !'))
                    move.period_id = period_obj.id
                
        return result

    # 14: private methods