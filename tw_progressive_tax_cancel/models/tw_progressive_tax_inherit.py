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


class TwProgressiveTaxCancel(models.Model):
    _inherit = "tw.progressive.tax"
    _description = 'Progressive Tax Cancel'

    state = fields.Selection(selection_add=[('cancel', 'Cancel')])
    cancel_uid = fields.Many2one('res.users', string="Cancelled by")
    cancel_date = fields.Datetime('Cancelled on')

    def _action_cancel(self):
        self.write({
            'state': 'cancel',
            'cancel_uid': self._uid,
            'cancel_date': datetime.now()
        })