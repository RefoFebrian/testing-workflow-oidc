from odoo import models, fields, api
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

class StockDistributionInherit(models.Model):
    _inherit = "tw.stock.distribution"

    is_rpa = fields.Boolean(string='RPA',default=False)
    is_add_from_hotline = fields.Boolean(string="Dari POS Hotline?", default=False, help="Terceklis jika distribusi Additional berasal dari POS Hotline DMS")