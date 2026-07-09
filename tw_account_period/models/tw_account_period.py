# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from datetime import datetime, timedelta
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class TwAccountPeriod(models.Model):
    _name = "tw.account.period"
    _order = "date_from, special desc"
    _description = 'Master Account Period'

    # 7: defaults methods

    # 8: fields
    name = fields.Char('Period Name')
    code = fields.Char('Code', size=12)
    special = fields.Boolean('Opening/Closing Period', help='These periods can overlap.')
    date_from = fields.Date('Start of Period')
    date_to = fields.Date('End of Period')
    state = fields.Selection([
        ('draft','Open'),
        ('done','Closed')
    ], 'Status', default='draft', help='When monthly periods are created. The status is \'Draft\'. At the end of monthly period it is in \'Done\' status.')

    # 9: relation fields
    company_id = fields.Many2one('res.company', string="Branch")

    # 10: constraints & sql constraints
    @api.constrains('date_from', 'date_to')
    def _check_duration(self):
        for data in self:
            if data.date_from and data.date_to:
                if data.date_from > data.date_to:
                    raise ValidationError(_('Error!\nThe duration of the Period(s) is/are invalid.'))

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_account_period_tree(self):
        domain = []
        list_view_id = self.env.ref('tw_account_period.tw_account_period_list_view').id
        form_view_id = self.env.ref('tw_account_period.tw_account_period_form_view').id
        search_view_id = self.env.ref('tw_account_period.tw_account_period_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Periods',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.account.period',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {
                'search_default_fieldname': 1,
                'search_default_state_draft': 1,
                'readonly_by_pass': 1
            },
        }
    
    
    def action_close_period(self):
        account_move_objs = self.env['account.move'].search([
            ('period_id','=',self.id),
            ('state','=','draft')
        ])
        if account_move_objs:
            raise ValidationError(_('In order to close a period, you must first post related journal entries.'))
        # TODO: is create account_journal_period models?
        # cr.execute('update account_journal_period set state=%s where period_id=%s', (mode, id))
        self.write({'state': 'done'})
    
    def action_draft_period(self):
        self.write({'state': 'draft'})

    # 14: private methods

    def _get_current_periods(self, date=None):
        # TODO : Test ulang
        now = datetime.now() - timedelta(hours=7)
        if date:
            now = date
        args = [('date_from','<=',now), ('date_to','>=',now)]
        if self._context.get('company_id', False):
            company_id = self._context['company_id']
            company_obj = self.env['res.company'].browse(company_id)
        else:
            company_obj = self.env.company
        
        args.append(('company_id','parent_of',company_obj.id))
        period_objs = self.search(args + [('special','=',False)])
        if not period_objs:
            period_objs = self.search(args)
        if not period_objs:
            warning = f'There is no period defined for this date: {now.date()}.\nPlease go to Configuration/Periods in {company_obj.code}.'
            raise ValidationError(_(warning))
        return period_objs[0]