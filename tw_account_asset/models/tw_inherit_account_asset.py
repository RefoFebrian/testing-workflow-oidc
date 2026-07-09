# -*- coding: utf-8 -*-
# # 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class TwAccountAsset(models.Model):
    _inherit = "account.asset.asset"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    company_id = fields.Many2one("res.company", string="Branch", domain="[('parent_id', '!=', False)]")
    product_id = fields.Many2one("product.product", string="Product")

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('company_id'):
                branch = self.env['res.company'].browse(vals['company_id'])
                vals['name'] = self.env['ir.sequence'].get_sequence_code('REGAS', str(branch.code))
        return super().create(vals_list)

    # 13: action methods

    # 14: private methods