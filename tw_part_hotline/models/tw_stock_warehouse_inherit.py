# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class StockWarehouseInherit(models.Model):
    _inherit = "stock.warehouse"

    # 7: defaults methods

    # 8: fields
    in_hotline_type_id = fields.Many2one('stock.picking.type', 'Type Picking In Hotline')
    

    