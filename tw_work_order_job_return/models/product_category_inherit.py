# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class ProductCategory(models.Model):
    _inherit = "product.category"

    # 7: defaults methods

    # 8: fields
    warranty = fields.Float(string='Warranty', digits='Account', store=True, default=0.0)

    # Selection

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods