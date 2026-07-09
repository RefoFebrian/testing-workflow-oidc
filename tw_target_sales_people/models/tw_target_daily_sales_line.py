# 1: imports of python lib

# 2: import of known third party lib
import calendar

# 3:  imports of odoo
from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwTargetDailySalesLine(models.Model):
    _name = "tw.target.daily.sales.line"
    _description = "Target Daily Sales Line"

    # 7: defaults methods
    def _get_series(self):
        self._cr.execute("""
            SELECT name->>'en_US' as name FROM product_template
            WHERE division = 'Unit'
            AND sale_ok = True
            GROUP BY name
        """)
        return [(item['name'], item['name']) for item in self._cr.dictfetchall()]

    # 8: fields
    month = fields.Selection(
        [(str(x), str(calendar.month_name[x])) for x in range(1, 13)],
        string='Month',
        default=str(datetime.now().month)
    )
    series = fields.Selection(_get_series, string='Series')

    target = fields.Integer(string='Target', default=0)
    actual = fields.Integer(string='Actual', default=0)

    # 9: relation fields
    target_daily_sales_id = fields.Many2one(comodel_name='tw.target.daily.sales', string='Target Daily Sales')

    # 10: constraints & sql constraints
    @api.constrains('target_daily_sales_id', 'series', 'month')
    def _check_existance(self):
        for rec in self:
            count = self.env['tw.target.daily.sales.line'].search_count([
                ('target_daily_sales_id', '=', rec.target_daily_sales_id.id),
                ('series', '=', rec.series),
                ('month', '=', rec.month),
                ('id', '!=', rec.id),
            ])
            if count > 1:
                raise ValidationError('Series dan Bulan sudah ada untuk Target Daily Sales ini!')

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods