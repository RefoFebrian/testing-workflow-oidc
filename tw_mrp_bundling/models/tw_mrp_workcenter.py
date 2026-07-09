# -*- coding: utf-8 -*-

# 1: imports of python lib
# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, exceptions

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class MrpWorkcenter(models.Model):
    _inherit = "mrp.workcenter"

    # 7: defaults methods

    # 8: fields
    bundling_account_id = fields.Many2one('account.account', 'Account Bundling',help="Account Bundling for stock journal")
    partner_id = fields.Many2one('res.partner', string='Supplier')

    # 9: relation fields