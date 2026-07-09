# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwSalesProgramLineInherit(models.Model):
    _inherit = "tw.sales.program.line"

    # 7: defaults methods
    def _get_domain_product(self):
        domain = [('id','=',0)]
        filter = []
        categ_ids = self.env['product.category'].get_child_ids('Unit')
        if categ_ids:
            filter = categ_ids
        product_ids = self.env['product.template'].search([('type','!=','view'),('categ_id','in',filter)])
        if product_ids:
            domain = [('id','in',product_ids.ids)]
        return domain

    # 8: fields

    # 9: relation fields
    product_tmpl_id = fields.Many2one('product.template', string='Product', domain=_get_domain_product)

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('product_tmpl_id_unique', 'unique(sales_program_id,product_tmpl_id)', 'Tidak boleh ada produk yang sama di dalam satu master Sales Program Lines !')
    ]

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods