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

class InheritStockPickingTypeQRCode(models.Model):
    _inherit = "stock.picking.type"
    
    # 7: defaults methods

    # 8: fields
    is_need_qr_code = fields.Boolean(string="Need QR Code", default=False)

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods

