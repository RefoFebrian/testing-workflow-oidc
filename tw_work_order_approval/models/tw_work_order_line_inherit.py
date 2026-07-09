# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrderLine(models.Model):
    _inherit = "tw.work.order.line"

    def _check_discount(self):
        check = super()._check_discount()
        if self.discount:
            if self.discount > 0 and self.division == 'Sparepart':
                if self.state not in ['draft','waiting_for_approval','unused','cancel','rejected']:
                    self.order_id.action_request_approval()

        return check