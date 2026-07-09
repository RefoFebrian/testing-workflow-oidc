# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
from datetime import datetime

# 2: import of known third party lib
from lxml import etree

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)

class TwAccountMove(models.Model):
    _inherit = "account.move"


    def write(self, vals):
        write = super(TwAccountMove, self).write(vals)
        for move in self:
            if move.ref and 'GRC/' in move.ref and move.payment_state in ('paid', 'in_payment'):
                check_grc = self.env['tw.good.receive.collecting'].suspend_security().search([
                    '|', ('move_id', '=', move.id), ('invoice_id', '=', move.id)
                ], limit=1)
                if check_grc and check_grc.state not in ('done', 'cancel'):
                    check_grc.action_done()
        return write