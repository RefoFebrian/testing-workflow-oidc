from odoo import models, fields

class TWAccountMoveLine(models.Model):
    _inherit = "account.move.line"

    consolidated_qty = fields.Float('Consolidated Qty')
