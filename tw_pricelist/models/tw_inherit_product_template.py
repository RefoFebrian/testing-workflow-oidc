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
    _inherit = "product.template"

    # 7: defaults methods

    # 8: fields
    is_unit = fields.Boolean(compute='_compute_is_unit', string='Is Unit', help="Indicates if this product is a unit product, which is used for unit transactions.")

    # 9: relation fields
    service_category_id = fields.Many2one(comodel_name='tw.selection', string='Service Category' , domain=[('type','=','PricelistServiceCategory')])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('division')
    def _compute_is_unit(self):
        for record in self:
            record.is_unit = False
            if record.division == 'Unit':            
                record.is_unit = True

    # 12: override methods

    # 13: action methods

    # 14: private methods
