# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TWAccountMove(models.Model):
    _inherit = "account.move.line"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    discount_id = fields.Many2one('tw.account.discount', string='Discount')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    # @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id')
    # def _compute_totals(self):
    #     super()._compute_totals()

    # 12: override methods
    # @api.model_create_multi
    # def create(self, vals_list):
    #     return super().create(vals_list)
    
    # def write(self, vals):
    #     return super().write(vals)


    # 13: action methods

    # 14: private methods
