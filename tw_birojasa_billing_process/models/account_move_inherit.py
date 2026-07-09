# -*- coding: utf-8 -*-

from odoo import models


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    def _invoice_paid_hook(self):
        """
        Hook called when invoice is paid.
        Override to auto-update billing process to done when vendor bill is paid.
        """
        res = super(AccountMoveInherit, self)._invoice_paid_hook()

        # Process vendor bills (in_invoice) related to billing process
        for move in self.filtered(lambda m: m.move_type == 'in_invoice'):
            # Find related billing process
            billing_process = self.env['tw.birojasa.billing.process'].search([
                ('invoice_id', '=', move.id),
                ('state', '=', 'confirmed')
            ], limit=1)

            if billing_process:
                # Auto-update to done
                billing_process.action_done()

        return res
