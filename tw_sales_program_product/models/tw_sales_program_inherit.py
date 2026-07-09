# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwSalesProgramInherit(models.Model):
    _inherit = "tw.sales.program"

    # 7: defaults methods
    def _get_domain_product(self):
        domain = [('id','=',0)]
        product_ids = self.env['product.product'].search([('type','!=','view'),('product_tmpl_id.categ_id','child_of','Direct Gift')])
        if product_ids:
            domain = [('id','in',product_ids.ids)]
        return domain

    # 8: fields

    # 9: relation fields
    product_id = fields.Many2one('product.product', string='Product', domain=_get_domain_product)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods