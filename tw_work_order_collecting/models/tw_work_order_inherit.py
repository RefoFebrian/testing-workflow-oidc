# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrder(models.Model):
    _inherit = "tw.work.order"
    # 7: defaults methods

    # 8: fields
    claim_state = fields.Selection([
        ('draft', 'Draft'),
        ('claimed', 'Claimed')
    ], string='WO Collected', default='draft')

    # 9: relation fields
    collecting_work_order_id = fields.Many2one(
        'tw.work.order.collecting', string='Collecting Work Order ID',
    )

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods