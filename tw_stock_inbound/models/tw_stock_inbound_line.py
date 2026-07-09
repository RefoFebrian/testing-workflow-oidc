from odoo import models, fields

class StockInboundLine(models.Model):
    _name = "tw.stock.inbound.line"
    _description = "Stock Inbound Line"
    
    name = fields.Char(string="Name")
    state = fields.Selection([
        ('progress', 'On Progress'),
        ('done', 'Done'),
    ], string="Status", default='progress')
    
    stock_inbound_id = fields.Many2one('tw.stock.inbound', string="Expedition", ondelete='cascade')