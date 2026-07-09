# -*- coding: utf-8 -*-

from odoo import models
from odoo.exceptions import UserError as Warning


class TwSaleOrderLineInherit(models.Model):
    _inherit = "tw.sale.order.line"
    
    def _validate_order_line(self):
        """
        Extend validation to check qty against approved_qty from SD (Stock Distribution).
        """
        # Call base validation first
        super()._validate_order_line()
        
        # Check qty not exceeding approved qty from SD (Stock Distribution)
        for line in self:
            if line.order_id and line.order_id.stock_distribution_id and line.product_id:
                sd_line = self.env['tw.stock.distribution.line'].sudo().search([
                    ('stock_distribution_id', '=', line.order_id.stock_distribution_id.id),
                    ('product_id', '=', line.product_id.id)
                ], limit=1)
                if sd_line and line.product_uom_qty > sd_line.approved_qty:
                    raise Warning(f'Quantity must not exceed approved qty from Stock Distribution (Qty Approved: {sd_line.approved_qty})')
