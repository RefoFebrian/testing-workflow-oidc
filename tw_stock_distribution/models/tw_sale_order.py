from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning


class TwSaleOrder(models.Model):
    _inherit = "tw.sale.order"
    
    origin = fields.Char(copy=False)
    stock_distribution_id = fields.Many2one('tw.stock.distribution', 'Stock Distribution', copy=False)
    
    def action_done(self):
        action_done = super().action_done()
        if self.stock_distribution_id:
            self.stock_distribution_id.suspend_security().action_done()
        return action_done