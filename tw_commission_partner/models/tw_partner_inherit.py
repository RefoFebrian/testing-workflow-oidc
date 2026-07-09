# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritTwPartnerCommission(models.Model):
    _inherit = "res.partner"

    # 7: defaults methods

    # 8: fields
    
    # 9: relation fields
    tax_mediator_id = fields.Many2one('account.tax', string='Tax Mediator')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods