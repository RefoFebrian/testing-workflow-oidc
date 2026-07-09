# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

class TwSalesVoucher(models.Model):
    _name = "tw.sales.voucher"
    _description = "Sales Voucher"

    name = fields.Char('Name')
    amount = fields.Float('Amount')
    date = fields.Date('Date', default=date.today())
    
    voucher_id = fields.Many2one('tw.sales.program', 'Voucher ID')
    lot_id = fields.Many2one('stock.lot', 'Engine No')
    partner_id = fields.Many2one('res.partner', 'Partner')

    
    