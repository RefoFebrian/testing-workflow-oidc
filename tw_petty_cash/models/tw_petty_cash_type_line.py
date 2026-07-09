from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TwPettyCashTypeLine(models.Model):
    _name = "tw.petty.cash.type.line"
    _description = "Petty Cash Type Line"

    name = fields.Char(string="Name", required=True)
    petty_cash_type_id = fields.Many2one('tw.petty.cash.type', string="Petty Cash Type", ondelete='cascade')
    account_id = fields.Many2one('account.account', string="Account", required=True)
