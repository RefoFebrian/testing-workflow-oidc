# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.tools import SQL

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)

class TWDealerSPKCancelReason(models.TransientModel):
    _name = "tw.dealer.spk.cancel.reason"
    _description = "Reason Cancel SPK"
   
    reason = fields.Text(string='Reason', required=True)
    spk_id = fields.Many2one(comodel_name='tw.dealer.spk', string='SPK',
                             required=True, readonly=True, default=lambda self: self.env.context.get('active_id'))
        
    def action_cancel(self):
        self.spk_id.action_cancel(self.reason)
    