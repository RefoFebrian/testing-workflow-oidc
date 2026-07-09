
from odoo import api, fields, models


class Job(models.Model):
    _inherit = "hr.job"
    
    sales_category = fields.Selection(selection=lambda self: self.env['tw.selection'].get_option_list('IncentiveCategory'))
