# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockMoveNRFS(models.Model):
    _inherit = "stock.move"
    
    # 7: defaults methods

    # 8: fields
    has_nrfs = fields.Selection(related='picking_id.has_nrfs', string='Has NRFS')
    
    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    
    # 12: override methods

    # 13: action methods

    # 14: private methods
    
