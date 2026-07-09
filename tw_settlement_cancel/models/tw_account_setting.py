# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwAccountSetting(models.Model):
    _inherit = "tw.account.setting"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    journal_settlement_cancel_id = fields.Many2one(
        'account.journal',
        string='Journal Settlement Cancel',
        help='Journal used for Settlement cancellation entries'
    )
