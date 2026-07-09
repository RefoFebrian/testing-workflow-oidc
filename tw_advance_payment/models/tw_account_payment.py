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
            payment._update_advance_payment_payment_ids()
        return result

    # 14: private methods
    def _update_advance_payment_payment_ids(self):
        if not self.move_id:
            return

        for line in self.line_ids:
            if not line.move_line_id:
                continue

            advance_payment = self.env['tw.advance.payment'].suspend_security().search([
                ('move_id', '=', line.move_line_id.move_id.id),
            ], limit=1)
            if advance_payment:
                advance_payment.suspend_security().write({
                    'payment_ids': [(4, self.id)]
                })
