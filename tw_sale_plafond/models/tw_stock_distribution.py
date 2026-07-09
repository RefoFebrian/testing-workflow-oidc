from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning


class InheritStockDistribution(models.Model):
    _inherit = "tw.stock.distribution"
    _description = 'Stock Distribution'

    def action_create_sale_order(self):
        so_obj = super().action_create_sale_order()
        so_obj.action_set_plafond_avaibility()
        return so_obj