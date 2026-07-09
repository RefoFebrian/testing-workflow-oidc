# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, timedelta, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwStockLotInherit(models.Model):
    _inherit = "stock.lot"
    _description = "TW Stock Lot"
   
    # 8: fields
    inv_progressive_tax_id = fields.Many2one('account.move', string='Invoice Pajak Progressive')