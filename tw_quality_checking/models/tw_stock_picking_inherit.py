# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class QcStockPicking(models.Model):
    _inherit = "stock.picking"
    _description = "Stock Picking"

    quality_checking_id = fields.Many2one('tw.quality.checking', string='Quality Checking')