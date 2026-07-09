# -*- coding: utf-8 -*-

# 1: imports of python lib
# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, exceptions

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class mutationProductCategoryInherit(models.Model):
    _inherit = "product.category"

    # 7: defaults methods

    # 8: fields
    mutation_account_id = fields.Many2one('account.account', 'Account Mutation',help="Account Mutation for stock journal")

    # 9: relation fields


    def _get_accounting_sync_field_names(self):
        base_field_names = super()._get_accounting_sync_field_names()
        base_field_names += ('mutation_account_id',)
        return base_field_names