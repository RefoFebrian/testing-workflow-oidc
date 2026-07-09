# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools import float_compare, float_is_zero

# 5: local imports

# 6: Import of unknown third party lib


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    work_order_line_ids = fields.Many2many(
        'tw.work.order.line',
        'tw_work_order_line_invoice_rel',
        'invoice_line_id', 'order_line_id',
        string='Work Order Lines', readonly=True, copy=False)

    
