# -*- coding: utf-8 -*-

# 1: imports of python lib
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrderCollecting(models.Model):
    _inherit = "tw.work.order.collecting"

    # 7: defaults methods

    # 8: fields
    state = fields.Selection(selection_add=[
        ('cancel','Cancelled')
        ])

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # Work Order Collecting Cancel
    def _action_cancel(self):
        self.write({
            'state': 'cancel',
            'amount': 0
        })
        for line in self.collecting_line_ids :
            line.write({
                'collecting_work_order_id': False
            })
        for work_order in self.work_order_ids :
            work_order.write({
                'collecting_work_order_id': False
            })