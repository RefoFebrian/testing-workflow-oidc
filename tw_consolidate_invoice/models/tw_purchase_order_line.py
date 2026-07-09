from odoo import models, fields

class TWPurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    consolidated_qty = fields.Float('Consolidated Qty')
