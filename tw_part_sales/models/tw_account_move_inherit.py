# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools import float_compare, float_is_zero

# 5: local imports

# 6: Import of unknown third party lib

class AccountMoveInherit(models.Model):
    _inherit = "account.move"

    def _invoice_paid_hook(self):
        res = super(AccountMoveInherit,self)._invoice_paid_hook()
        todo = set()
        for invoice in self.filtered(lambda move: move.is_invoice()):
            for line in invoice.invoice_line_ids:
                for part_sales_line in line.part_sales_line_ids:
                    todo.add((part_sales_line.order_id, invoice.name))
        
        for (order, name) in todo:
            order.message_post(body=_("Invoice %s paid", name))
            order.action_done()
        return res