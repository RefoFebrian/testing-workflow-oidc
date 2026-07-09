# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
import calendar

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools import float_is_zero, OrderedSet

# 5: local imports

# 6: Import of unknown third party lib

class TwStockMove(models.Model):
    _inherit = "stock.move"
    # 7: defaults methods

    # 8: fields
	
    # 9: relation fields
	
    # 10: constraints & sql constraints
	
    # 11: compute/depends & on change methods

    # 12: override methods
