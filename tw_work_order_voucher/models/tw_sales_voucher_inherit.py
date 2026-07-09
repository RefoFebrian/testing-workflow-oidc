# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

class TwSalesVoucher(models.Model):
    _inherit = "tw.sales.voucher"

    used_amount = fields.Float('Used Amount', default=0.0, help='Voucher amount used in WO payment')
    residual_amount = fields.Float('Residual Amount', compute='_compute_residual_amount', store=True, help='Remaining voucher amount against the total voucher amount used when paying for WO')
    claimed_transaction_name = fields.Char('Claimed Transaction Name', help='Transaction name when claiming voucher')
    
    @api.depends('used_amount')
    def _compute_residual_amount(self):
        for record in self:
            record.residual_amount = record.amount
            if record.used_amount > 0:
                record.residual_amount = record.amount - record.used_amount
