# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
_logger = logging.getLogger(__name__)

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, exceptions

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class ProductTemplate(models.Model):
    _inherit = "product.category"

    # 7: defaults methods

    # 8: fields
    is_mandatory_extras = fields.Boolean('Mandatory Extras?',help="If checked, the Product Category need to have Bom Extras when confirming PO.",default=False)

    # 9: relation fields
   
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
  
    # 12: override methods

    # 13: action methods

    # 14: private methods
