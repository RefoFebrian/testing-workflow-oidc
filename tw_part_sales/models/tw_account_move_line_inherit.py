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

    part_sales_line_ids = fields.Many2many(
        'tw.part.sales.line',
        'tw_part_sales_line_invoice_rel',
        'invoice_line_id', 'order_line_id',
        string='Part Sales Lines', readonly=True, copy=False)