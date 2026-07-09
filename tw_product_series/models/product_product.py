from odoo import models, fields, api

class ProductProduct(models.Model):
    _inherit = "product.product"

    series_id = fields.Many2one(
        'product.series',
        string='Product Series',
        related='product_tmpl_id.series_id',
        store=True,
        index=True,
        readonly=False
    )
