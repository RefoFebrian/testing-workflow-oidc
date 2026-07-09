# -*- coding: utf-8 -*-

from odoo import models, fields

class TwStockPickingDGI(models.Model):
    _inherit = "stock.picking"

    is_dgi = fields.Boolean(related="purchase_id.is_dgi", string="Is DGI", store=True)
    md_reference_po = fields.Char(related="purchase_id.md_reference_po", string="MD Reference PO", store=True)
    md_reference_sl = fields.Char(related="purchase_id.md_reference_sl", string="MD Reference SL", store=True)
