# -*- coding: utf-8 -*-
from odoo import models, _


class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    def _invoice_paid_hook(self):
        """Override to mark Purchase Return as done when invoice is paid."""
        res = super(AccountMoveInherit, self)._invoice_paid_hook()
        
        # Handle Purchase Return
        purchase_return_orders = set()
        for invoice in self.filtered(lambda move: move.is_invoice()):
            for line in invoice.invoice_line_ids:
                for return_line in line.purchase_return_line_ids:
                    purchase_return_orders.add((return_line.order_id, invoice.name))
        
        if purchase_return_orders:  
            for (order, name) in purchase_return_orders:
                order.message_post(body=_("Invoice %s paid", name))
                order.action_done()
        
        return res
