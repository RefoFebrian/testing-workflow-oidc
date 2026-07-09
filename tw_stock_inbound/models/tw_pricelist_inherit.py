from odoo import models, fields, api, _

class ExpeditionPricelist(models.Model):
    _inherit = "product.pricelist"
    
    type = fields.Selection(selection_add=[('expedition', 'Expedition')])


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    
    type = fields.Selection(
        string='Type',
        related='pricelist_version_id.pricelist_id.type',
        store=True,
        readonly=True
    )