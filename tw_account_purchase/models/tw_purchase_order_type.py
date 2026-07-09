# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
import calendar

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritTwPurchaseOrderType(models.Model):
	_inherit = "tw.purchase.order.type"
	_description = "Inherit Purchase Order Type"
	
    # 7: defaults methods

    # 8: fields
	
    # 9: relation fields
	payment_term_id = fields.Many2one('account.payment.term', 'Payment Terms', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
	
    # 10: constraints & sql constraints
	
    # 11: compute/depends & on change methods

    # 12: override methods
    
                 