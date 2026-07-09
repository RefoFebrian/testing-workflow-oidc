# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

class TwSalesVoucher(models.Model):
    _inherit = "tw.sales.voucher"

    sale_order_id = fields.Many2one('tw.dealer.sale.order', 'Sale Order ID')
    
    
    