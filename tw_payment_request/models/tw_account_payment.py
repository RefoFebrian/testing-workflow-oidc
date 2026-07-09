# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class AccountPaymentInherit(models.Model):
    _inherit = "tw.account.payment"

    # 12: override methods

    # 13: action methods
    def action_validate(self):
        result = super().action_validate()
        for payment in self:
            payment._update_payment_request_payment_ids()
        return result

    # 14: private methods
    def _update_payment_request_payment_ids(self):
        if not self.move_id:
            return

        for line in self.line_ids:
            if not line.move_line_id:
                continue

            payment_request = self.env['tw.payment.request'].suspend_security().search([
                ('move_id', '=', line.move_line_id.move_id.id),
            ], limit=1)
            if not payment_request:
                continue

            payment_request.suspend_security().write({
                'account_payment_ids': [(4, self.id)]
            })
            payable_lines = payment_request.move_id.line_ids.filtered(
                lambda l: l.account_id.account_type == 'liability_payable'
            )
            if payable_lines and all(line.full_reconcile_id for line in payable_lines):
                payment_request.suspend_security().write({'is_paid': True})
