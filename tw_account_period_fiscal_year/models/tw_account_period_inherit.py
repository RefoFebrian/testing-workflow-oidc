# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class TwAccountPeriodInherit(models.Model):
    _inherit = "tw.account.period"

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now()

    # 8: fields

    # 9: relation fields
    fiscalyear_id = fields.Many2one('account.fiscal.year', 'Fiscal Year', ondelete='cascade')
    company_id = fields.Many2one('res.company', related='fiscalyear_id.company_id', string="Branch", store=True)

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('name_company_unique', 'unique(name, company_id)', 'The name of the period must be unique per company!')
    ]

    # 11: compute/depends & on change methods
    @api.constrains('fiscalyear_id', 'date_from', 'date_to')
    def _check_year_limit(self):
        warning = 'Error!\nThe period is invalid. Either some periods are overlapping or the period\'s dates are not matching the scope of the fiscal year.'
        for data in self:
            if data.special:
                continue

            if (data.fiscalyear_id.date_to < data.date_to) or \
                (data.fiscalyear_id.date_to < data.date_from) or \
                    (data.fiscalyear_id.date_from > data.date_from) or \
                        (data.fiscalyear_id.date_from > data.date_to):
                raise ValidationError(_(warning))
            
            pid_objs = self.search([
                ('date_to','>=',data.date_from),
                ('date_from','<=',data.date_to),
                ('special','=',False),
                ('id','!=',data.id)
            ])
            if pid_objs:
                for pid_obj in pid_objs:
                    if pid_obj.fiscalyear_id.company_id.id == data.fiscalyear_id.company_id.id:
                        raise ValidationError(_(warning))

    # 12: override methods
    def write(self, vals):
        if 'company_id' in vals:
            move_line_obj = self.env['account.move.line'].search([('period_id','=',self.id)])
            if move_line_obj:
                raise ValidationError(_('This journal already contains items for this period, therefore you cannot modify its company field.'))
        
        return super(TwAccountPeriodInherit, self).write(vals)
    
    # 13: action methods
    def action_draft_period(self):
        action_draft = super(TwAccountPeriodInherit, self).action_draft_period()
        if self.fiscalyear_id:
            if self.fiscalyear_id.state == 'done':
                raise ValidationError(_('You can not re-open a period which belongs to closed fiscal year'))
        # TODO: is create account_journal_period models?
        # cr.execute('update account_journal_period set state=%s where period_id in %s', (mode, tuple(ids),))
    
        return action_draft

    # 14: private methods