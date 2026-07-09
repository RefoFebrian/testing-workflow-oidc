# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import datetime

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockLotQRCode(models.Model):
    _inherit = "stock.lot"
    
    # 7: defaults methods

    # 8: fields
    qr_code = fields.Char(string='QR Code', help='QR Code Unit')

    # 9: relation fields
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
  
    # 14: private methods

