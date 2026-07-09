# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from datetime import datetime
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockLocationApproval(models.Model):
    _inherit = "stock.location"

    is_approval = fields.Boolean(string='Need Approval', default=False, help='This fields used for domain / attributes')
    
    # 9: relation fields
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
            
    # 12: override methods
    
    # 13: action methods
