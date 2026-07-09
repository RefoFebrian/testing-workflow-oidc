# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp

# 4: imports from odoo modules
from odoo.tools import float_compare

# 5: local imports

# 6: Import of unknown third party lib

class TwNetOffLine(models.Model):
    """Net Off Line"""
    _name = "tw.net.off.line"
    _description = "Net Off Line"

    # 7: defaults methods
    # 8: fields
    type = fields.Selection(selection=[("debit", "Debit"), ("credit", "Credit")], string="Type", required=True,default="debit")
    debit = fields.Float(string="Debit", required=True, digits='Account', default=0.0)
    credit = fields.Float(string="Credit", required=True, digits='Account', default=0.0)
    name = fields.Char(string="Label", required=True, default="/")
    matching_number = fields.Char(string="Reconcile")

    # 9: relation fields
    net_off_id = fields.Many2one('tw.net.off', string="Net Off", required=True, ondelete="cascade", index=True, copy=False)
    move_line_id = fields.Many2one('account.move.line', string='Journal Items')
    account_id = fields.Many2one('account.account', string="Account", required=True)
    company_id = fields.Many2one('res.company', related="net_off_id.company_id", string="Branch", store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string="Partner", domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    

    # 10: constraints & sql constraints
    _sql_constraints = [
        (
            "unique_net_off_move_line",
            "UNIQUE(net_off_id, move_line_id)",
            "Journal Items must be unique per net off!"
        ),
    ]

    # 11: compute/depends & on change methods
    @api.onchange("move_line_id")
    def _onchange_move_line_id(self):
        if self.move_line_id:
            self.account_id = self.move_line_id.account_id
            self.partner_id = self.move_line_id.partner_id
            self.company_id = self.move_line_id.company_id
            self.name = self.move_line_id.name
            self.debit = self.move_line_id.debit
            self.credit = self.move_line_id.credit
            self.matching_number = self.move_line_id.matching_number

    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods
    @api.constrains("debit","credit")
    def _check_amount(self):
        for line in self:
            if line.debit < 0.0:
                raise ValidationError(_("The debit must be strictly positive."))
            if line.credit < 0.0:
                raise ValidationError(_("The credit must be strictly positive."))