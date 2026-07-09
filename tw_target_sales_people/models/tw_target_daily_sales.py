# 1: imports of python lib

# 2: import of known third party lib
import calendar

# 3:  imports of odoo
from odoo import models, fields, api, _
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwTargetDailySales(models.Model):
    _name = "tw.target.daily.sales"
    _description = "Target Daily Sales"

    # 7: defaults methods

    # 8: fields
    year = fields.Selection([
        (str(x), str(x)) for x in range(2010, datetime.now().year + 1)
    ], string='Year', default=str(datetime.now().year))

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string="Branch", default=lambda self: self.env.company.id)
    target_line_ids = fields.One2many(comodel_name='tw.target.daily.sales.line', inverse_name='target_daily_sales_id', string='Target Lines')

    # 10: constraints & sql constraints
    @api.constrains('company_id', 'year')
    def _check_existance(self):
        for rec in self:
            company_ids = self.mapped('company_id')
            search_ids = self.env['tw.target.daily.sales'].suspend_security().search([
                ('company_id', 'in', company_ids.ids),
                ('year', '=' , rec.year)
            ])
            if len(search_ids) > 1:
                raise ValidationError('Company dan Tahun sudah ada!')

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods