# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwStockLotInherit(models.Model):
    _inherit = "stock.lot"
    _description = "Stock Lot"

    freight_cost = fields.Float(
        string='Freight Cost',
        default=0.0,
        readonly=True,
        help='Freight cost from Expedition'
    )
    