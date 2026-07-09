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


class InheritTwBankTransfer(models.Model):
    _inherit = "tw.bank.transfer"
    

    # 9: relation fields
    reconcile_id = fields.Many2one('tw.bank.reconcile',string="Bank Reconcile")
    
    
    # 13: action methods
    def action_reconcile_create(self, line_id):
        reconcile_ids = [line.move_line_id.id for line in self.reconcile_ids]
        reconcile_ids += [line_id]
        r_id = self.env['tw.bank.reconcile'].create({
            'type': 'cash',
            'line_ids': map(lambda x: (4, x, False), reconcile_ids),
        })
        self.write({'reconcile_id':r_id})
        return r_id