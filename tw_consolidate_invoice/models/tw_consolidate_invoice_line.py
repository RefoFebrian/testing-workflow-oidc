from odoo import models, fields

class TWConsolidateInvoiceLine(models.Model):
    _name = "tw.consolidate.invoice.line"
    _description = "Consolidate Invoice Line"

    qty = fields.Float(string='Qty')
    invoice_qty = fields.Float(string='Invoice Qty')
    move_qty = fields.Float(string='Move Qty')
    unit_price = fields.Float(string='Unit Price')
    untaxed_price = fields.Float(string='DPP')
    
    consolidate_id = fields.Many2one('tw.consolidate.invoice', string='Consolidate Invoice', ondelete='cascade')
    purchase_order_id = fields.Many2one('purchase.order', string='Purchase Order')
    invoice_line_id = fields.Many2one('account.move.line', string='Invoice Line')
    stock_move_id = fields.Many2one('stock.move', string='Stock Move')
    product_id = fields.Many2one('product.product', string='Product')
    lot_ids = fields.Many2many('stock.lot', string='Serial Number')
