# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.tools import SQL
from odoo.exceptions import UserError as Warning

# 5: local imports
from odoo.addons.tw_base.models.amount_to_text import convert

# 6: Import of unknown third party lib


class InheritTWAccountMove(models.Model):
    _inherit = "account.move"
    
    # 7: defaults methods

    # 8: fields
    process_offtr_id = fields.Many2one('tw.process.off.the.road', string='Process Off The Road')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _invoice_paid_hook(self):
        res = super(InheritTWAccountMove,self)._invoice_paid_hook()
        todo = set()
        for invoice in self.filtered(lambda move: move.is_invoice()):
            if invoice.process_offtr_id:
                todo.add((invoice.process_offtr_id, invoice.name))

        for (order, name) in todo:
            order.message_post(body=_("Invoice %s paid", name))
            order.action_done()
        return res
