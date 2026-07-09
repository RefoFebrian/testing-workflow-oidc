# 1: imports of python lib

# 2: import of known third party lib
from datetime import date

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwCancellation(models.Model):
    _name = "tw.cancellation.handler"
    _description = "Tw Cancellation Handler"

    # 7: defaults methods

    # 8: fields
    model = fields.Char(required=True) 
    module = fields.Char(required=True)

    

