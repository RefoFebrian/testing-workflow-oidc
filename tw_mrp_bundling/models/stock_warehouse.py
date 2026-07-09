# -*- coding: utf-8 -*-
from odoo import models, fields

class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    bundling_location_id = fields.Many2one(
        'stock.location', string='Bundling Location',
        domain="[('usage', '=', 'internal'), ('company_id', '=', company_id)]",
        help="Location where materials are automatically moved when starting a bundling production."
    )
