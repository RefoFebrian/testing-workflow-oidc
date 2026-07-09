# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

class SaleProcurementGroup(models.Model):
    _inherit = "procurement.group"

    sale_order_id = fields.Many2one('tw.sale.order', 'Sales Order')