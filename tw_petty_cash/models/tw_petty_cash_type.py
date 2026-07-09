from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError as Warning


class TwPettyCashType(models.Model):
    _name = "tw.petty.cash.type"
    _description = "Petty Cash Type"
    _order = "name asc"

    name = fields.Text(string="Description", required=True)
    active = fields.Boolean(
        string='Active',
        default=True)
    petty_cash_type_lines = fields.One2many(
        'tw.petty.cash.type.line',
        'petty_cash_type_id',
        string="Petty Cash Type Line",
        copy=True
    )
