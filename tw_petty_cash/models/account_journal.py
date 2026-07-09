from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    type = fields.Selection(
        selection_add=[
            ('petty_cash', 'Petty Cash')
        ],
        ondelete={'petty_cash': 'set general'}
    )
