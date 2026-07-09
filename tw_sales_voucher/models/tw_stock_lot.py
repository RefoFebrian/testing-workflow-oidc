# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

class TwStockLot(models.Model):
    _inherit = "stock.lot"

    voucher_ids = fields.Many2many('tw.sales.voucher', 'tw_stock_lot_voucher_rel', 'lot_id', 'voucher_id', 'Vouchers')
    voucher_total = fields.Float('Voucher Total', compute='_compute_voucher_total')

    @api.depends('voucher_ids','voucher_ids.amount')
    def _compute_voucher_total(self):
        for lot in self:
            total_voucher = 0
            for voucher in lot.voucher_ids:
                total_voucher += voucher.amount
            lot.voucher_total = total_voucher
    
    