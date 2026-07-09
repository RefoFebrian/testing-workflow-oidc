from odoo import api, fields, models, _
from odoo.exceptions import UserError as Warning
from lxml import etree
from datetime import datetime


class DealerSaleOrderBbnLot(models.Model):
    _inherit = "stock.lot"

    service_amount = fields.Float(string='Service', digits='Product Price')
    estimation_amount = fields.Float(string='Estimation Total',digits='Product Price')

    biro_jasa_id = fields.Many2one(comodel_name='res.partner', string='Biro Jasa', readonly=True,domain=[('category_id.name', '=', 'Birojasa')], tracking=True)
    customer_stnk_id = fields.Many2one(comodel_name='res.partner', string='Customer STNK', tracking=True, readonly=True)
    
    accure_bbn_move_id = fields.Many2one('account.move', string='Invoice BBN')
    accrue_bbn_move_line_ids = fields.Many2many('account.move.line', 'stock_lot_account_move_line_rel', 'lot_id', 'move_line_id', string='Entries Invoice BBN')