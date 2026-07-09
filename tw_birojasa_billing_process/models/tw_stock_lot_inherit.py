from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockLotBilling(models.Model):
    _inherit = "stock.lot"

    birojasa_billing_date = fields.Date(string='Tagihan Birojasa Date', tracking=True)
    birojasa_billing_id = fields.Many2one('tw.birojasa.billing.process', string="Tagihan Birojasa", tracking=True)
    progressive_tax_invoice_id = fields.Many2one(comodel_name='account.move',string='Progressive Tax Invoice', tracking=True)