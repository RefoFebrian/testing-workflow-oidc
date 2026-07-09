from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TwPettyCashInLine(models.Model):
    _name = "tw.petty.cash.in.line"
    _description = "Petty Cash In Line"

    name = fields.Char(string="Description", required=True)
    amount = fields.Float(string="Amount")
    petty_cash_in_id = fields.Many2one('tw.petty.cash.in', string="Petty Cash In", ondelete='cascade')
    account_id = fields.Many2one('account.account', string="Account")
    allowed_account_ids = fields.Many2many(
        comodel_name='account.account',
        compute='_get_allowed_accounts',
        string='Allowed Accounts')

    @api.depends(
        'petty_cash_in_id.petty_cash_out_id'
    )
    def _get_allowed_accounts(self):
        for rec in self:
            allowed_account_ids = self.env['account.account']
            if rec.petty_cash_in_id.petty_cash_out_id:
                allowed_account_ids = rec.petty_cash_in_id.petty_cash_out_id.mapped('petty_cash_out_line_ids.account_id')
            rec.allowed_account_ids = allowed_account_ids

    @api.constrains(
        'amount'
    )
    def check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError("Amount harus lebih besar dari 0.")

    @api.constrains(
        'account_id'
    )
    def check_duplicate_account(self):
        for rec in self:
            other_id = self.search([
                ('petty_cash_in_id', '=', rec.petty_cash_in_id.id),
                ('account_id', '=', rec.account_id.id),
                ('id', '!=', rec.id),
            ], limit=1)
            if other_id:
                raise ValidationError(_(f'Account {rec.account_id.display_name} sudah ada.'))
    