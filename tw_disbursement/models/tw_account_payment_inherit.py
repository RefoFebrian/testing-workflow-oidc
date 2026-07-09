# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TWAccountPaymentInherit(models.Model):
    _inherit = "tw.account.payment"
    
    # 7: defaults methods

    # 8: fields
    percentage = fields.Float(string="Bank Charge (%)", digits='Account')
    amount_edc = fields.Float(string='EDC Total Amount', digits='Account', compute='_compute_amount', store=True)
    approval_code = fields.Char(string="Approval Code")
    journal_type = fields.Char(string="Journal Type", compute='_compute_journal_type', store=True)

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('percentage','amount')
    def _compute_amount(self):
        for rec in self:
            rec.amount_edc = 0.0
            if rec.journal_id.type == 'edc':
                rec.amount_edc = rec.amount *100/(100-rec.percentage)

    @api.depends('journal_id')
    def _compute_journal_type(self):
        for rec in self:
            rec.journal_type = rec.journal_id.type

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _get_available_journal_type(self):
        return ['bank', 'cash', 'credit','edc']