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
    is_only_use_pricelist = fields.Boolean('Only use pricelist?',help="If checked, the Product Category will be used for pricing.",default=True)

    # 9: relation fields
   
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
  
    @api.onchange('is_only_use_pricelist')
    def onchange_is_only_use_pricelist(self):
        def get_all_child_categories(category):
            children = self.search([('parent_id', '=', category.id)])
            all_children = children
            for child in children:
                all_children |= get_all_child_categories(child)
            return all_children

        all_childs = get_all_child_categories(self)
        for child in all_childs:
            child.is_only_use_pricelist = self.is_only_use_pricelist

    
    @api.onchange('parent_id')
    def onchange_parent_id(self):
        self.is_only_use_pricelist = True
        if self.parent_id:
            self.is_only_use_pricelist = self.parent_id.is_only_use_pricelist

    # 12: override methods

    # 13: action methods

    # 14: private methods
