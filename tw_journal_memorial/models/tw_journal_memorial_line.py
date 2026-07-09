# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# 4: imports from odoo modules
from odoo.tools import float_compare

# 5: local imports

# 6: Import of unknown third party lib

class TwJournalMemorialLine(models.Model):
    """Journal Memorial Line"""
    _name = "tw.journal.memorial.line"
    _description = "Journal Memorial Line"
    _order = "id"

    # 7: defaults methods
    # 8: fields
    type = fields.Selection(selection=[("debit", "Debit"), ("credit", "Credit")], string="Type", required=True,default="debit")
    amount = fields.Float(string="Amount", required=True, digits='Account', default=0.0)
    name = fields.Char(string="Label", required=True)

    # 9: relation fields
    journal_memorial_id = fields.Many2one("tw.journal.memorial", string="Journal Memorial", required=True, ondelete="cascade", index=True, copy=False)
    account_id = fields.Many2one("account.account", string="Account", required=True)
    partner_id = fields.Many2one("res.partner", string="Partner", domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    company_id = fields.Many2one("res.company", string="Branch", required=True)
    company_currency_id = fields.Many2one("res.currency", related="company_id.currency_id", string="Company Currency", readonly=True, store=True)
    asset_id = fields.Many2one("account.asset.asset", string="Asset", domain="[('state', '!=', 'close'), ('company_id', '=', company_id)]")

    # 10: constraints & sql constraints
    _sql_constraints = [
        (
            "unique_account_partner_branch",
            "UNIQUE(journal_memorial_id, account_id, partner_id, company_id)",
            "Account, partner and branch combination must be unique per journal memorial!"
        ),
        (
            "check_amount",
            "CHECK(amount > 0)",
            "The amount must be strictly positive."
        ),
    ]

    # 11: compute/depends & on change methods
    @api.onchange("account_id")
    def _onchange_account_id(self):
        if self.account_id:
            self.name = self.name or self.account_id.name or ""
    
    @api.onchange("type")
    def _onchange_type(self):
        if self.type == 'debit':
            diff = self.journal_memorial_id.total_credit - self.journal_memorial_id.total_debit
            self.amount = diff if diff > 0 else 0
        elif self.type == 'credit':
            diff = self.journal_memorial_id.total_debit - self.journal_memorial_id.total_credit
            self.amount = diff if diff > 0 else 0
            

    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods
    @api.constrains("amount")
    def _check_amount(self):
        for line in self:
            if line.amount <= 0.0:
                raise ValidationError(_("The amount must be strictly positive."))

    def _prepare_move_line_vals(self):
        self.ensure_one()
        debit = self.amount if self.type == 'debit' else 0.0
        credit = self.amount if self.type == 'credit' else 0.0
        
        currency = self.company_currency_id or self.company_id.currency_id
        if currency:
            debit = currency.round(debit)
            credit = currency.round(credit)
        
        return {
            'name': self.journal_memorial_id.description,
            'ref': self.journal_memorial_id.name,
            'account_id': self.account_id.id,
            'division': self.journal_memorial_id.division,
            'debit': debit,
            'credit': credit,
            'partner_id': self.partner_id.id or False,
        }
