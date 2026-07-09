# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, Command,fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritMrpBomLine(models.Model):
    _inherit = "mrp.bom.line"


    # 7: defaults methods

    # 8: fields
    

    # 9: relation fields
    product_header_id = fields.Many2one(
        related="bom_id.product_id",
        store=True,
        index=True,
        string="Product Variant"
    )

    categ_id = fields.Many2one(related="product_id.categ_id",string="Product Category")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
