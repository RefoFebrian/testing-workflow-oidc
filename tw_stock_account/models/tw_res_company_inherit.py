# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritCompany(models.Model):
    _inherit = "res.company"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        company_obj = super().create(vals_list)
        # Sync cost method template to new companies
        cats = self.env['product.category'].search([('cost_method_template', '!=', False)])
        if cats:
            cats._sync_accounting_data(companies=company_obj)

        return company_obj

    # 13: action methods

    # 14: private methods
