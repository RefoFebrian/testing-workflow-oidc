# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class AccountMoveLineInherit(models.Model):
    _inherit = "account.move.line"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    period_id = fields.Many2one(related='move_id.period_id', string='Period', store=True)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods