# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class Country(models.Model):
    _inherit = "res.country"
    _description = "Res Country Inherit"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = vals['name'].upper()
        return super(Country,self).create(vals_list)

    
    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(Country, self).write(vals)
    
    # 13: action methods
    
    # 14: private methods
