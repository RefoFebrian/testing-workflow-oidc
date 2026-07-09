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


class TwDisbursementCancelInherit(models.Model):
    _inherit = "tw.disbursement"

    # 7: defaults methods

    # Audit Trail
    cancel_uid = fields.Many2one('res.users',string="Cancelled by")
    cancel_date = fields.Datetime('Cancelled on')
    
    # 12: override methods
    def action_cancel_disbursement(self):
        self.write({
            'state':'cancel',
            'cancel_uid': self.env.uid,
            'cancel_date': datetime.now()
        })
        return True