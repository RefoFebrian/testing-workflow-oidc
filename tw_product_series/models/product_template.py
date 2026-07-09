from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    series_id = fields.Many2one(
        'product.series',
        string='Product Series',
        index=True,
        help="Select a product series for this product"
    )
