# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, timedelta

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwStockStoredStockPickingTypeInherit(models.Model):
    _inherit = "stock.picking.type"
    
    # 7: defaults methods

    # 8: fields
    
    # 9: relation fields
    temporary_location_id = fields.Many2one("stock.location", string="Temporary Location")
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods 
    
    # 12: override methods
    
    # 13: action methods

    # 14: private methods