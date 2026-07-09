from odoo import models, fields, api

class TWAccountMove(models.Model):
    _inherit = "account.move"

    is_consolidated = fields.Boolean('Is Consolidated',compute='_compute_is_consolidated',store=True)

    @api.depends('invoice_line_ids.consolidated_qty')
    def _compute_is_consolidated(self):
        for record in self:
            record.is_consolidated = not record.invoice_line_ids.filtered(lambda x: x.consolidated_qty != x.quantity).exists()  