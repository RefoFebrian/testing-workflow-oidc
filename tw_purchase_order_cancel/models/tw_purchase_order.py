# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date 

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwPurchaseOrderCancelInherit(models.Model):
    _inherit = "purchase.order"

    # 7: defaults methods

    # Audit Trail
    cancel_uid = fields.Many2one('res.users',string="Cancel by")
    cancel_date = fields.Datetime('Cancel on')
    
    # 12: override methods
    def button_cancel(self):
        cancel = super(TwPurchaseOrderCancelInherit, self).button_cancel()
        self.write({
            'state': 'cancel',
            'cancel_uid': self.env.uid,
            'cancel_date': datetime.now()
        })
        return cancel

    def _get_additional_cancel_account_moves(self):
        """Hook for feature modules to expose extra moves tied to this PO."""
        self.ensure_one()
        return self.env['account.move']

    def _get_additional_cancel_blocking_moves(self):
        """Hook for feature modules to expose extra moves that must block PO cancellation."""
        self.ensure_one()
        return self.env['account.move']
