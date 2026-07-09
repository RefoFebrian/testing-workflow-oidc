
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class QualityCheckingLine(models.Model):
    _name = "tw.quality.checking.line"
    _description = "Quality Checking Line"

    quantity = fields.Integer('Qty')
    qty_supply = fields.Integer('Qty Supply')
    weight = fields.Float('Berat (gram)')

    # # TODO : Turn on if you have already run the EV schema
    # is_ev = fields.Boolean('Is EV?')
    # lot_id = fields.Many2one('stock.lot', string="Engine Number")

    quality_checking_id = fields.Many2one('tw.quality.checking', string='Quality Checking')
    picking_id = fields.Many2one('stock.picking', string='Stock Picking')
    product_id = fields.Many2one('product.product', string='Product')