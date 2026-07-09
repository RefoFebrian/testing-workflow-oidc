# Part of Odoo. See LICENSE file for full copyright and licensing details.
# 1: imports of python lib
import logging

_logger = logging.getLogger(__name__)

# 2: import of known third party lib

# 3: imports of odoo
from odoo import api, fields, models, _

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # 7: defaults methods

    # 8: fields
    is_only_use_pricelist = fields.Boolean(
        'Is only use pricelist?', 
        config_parameter='tw_pricelist.is_only_use_pricelist'
    )

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.onchange('is_only_use_pricelist')
    def _onchange_group_sale_pricelist(self):
        if self.is_only_use_pricelist:
            if 'group_product_pricelist' in self.read()[0]:
                self.group_product_pricelist = True

    def set_values(self):
        """Override to update all product.category based on is_only_use_pricelist setting."""
        res = super().set_values()
        _logger.info("=== set_values called, is_only_use_pricelist: %s ===", self.is_only_use_pricelist)
        
        # Update all product.category to match the setting value
        product_categories = self.env['product.category'].search([])
        _logger.info("=== Updating %s product categories to is_only_use_pricelist=%s ===", 
                     len(product_categories), self.is_only_use_pricelist)
        product_categories.write({'is_only_use_pricelist': self.is_only_use_pricelist})
        
        return res
        
    # 13: action methods

    # 14: private methods