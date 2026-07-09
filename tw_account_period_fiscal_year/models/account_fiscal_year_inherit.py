# 1: imports of python lib
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class AccountFiscalYearInherit(models.Model):
    _inherit = "account.fiscal.year"

    # 7: defaults methods

    # 8: fields
    code = fields.Char('Code', size=6)
    state = fields.Selection([
        ('draft','Open'),
        ('done','Closed')
    ], 'State', default='draft')

    # 9: relation fields
    period_ids = fields.One2many('tw.account.period', 'fiscalyear_id', string='Periods')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_create_period3(self):
        return self.action_create_period(3)
    
    def action_create_period(self, interval=1):
        period_obj = self.env['tw.account.period']
        if self.date_from and self.date_to:
            ds = self.date_from
            period_obj.create({
                'name':  f"Opening Period {ds.strftime('%Y')}",
                'code': ds.strftime('00/%Y'),
                'date_from': ds,
                'date_to': ds,
                'special': True,
                'fiscalyear_id': self.id
            })
            while ds.strftime('%Y-%m-%d') < self.date_to.isoformat():
                de = ds + relativedelta(months=interval, days=-1)
                if de.strftime('%Y-%m-%d') > self.date_to.isoformat():
                    de = self.date_to
                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_from': ds.strftime('%Y-%m-%d'),
                    'date_to': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': self.id
                })
                ds = ds + relativedelta(months=interval)
        
        return True
    
    # 14: private methods