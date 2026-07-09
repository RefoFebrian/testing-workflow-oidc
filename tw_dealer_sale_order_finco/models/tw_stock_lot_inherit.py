from odoo import api, fields, models, _
from odoo.exceptions import UserError as Warning
from lxml import etree
from datetime import datetime


class DealerSaleOrderFincoLot(models.Model):
    _inherit = "stock.lot"

    # 8: fields
    tenor = fields.Integer(string="Tenor")
    installment = fields.Integer(string="Cicilan")

    # 9: relation fields
    finco_id = fields.Many2one('res.partner', 'Finance Company', domain=[('category_id.name', '=', 'Finance Company')])