# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.osv import expression
from odoo.exceptions import UserError as Warning
from odoo.tools import format_datetime, format_date, format_list, groupby, SQL
from odoo.tools.float_utils import float_compare, float_is_zero
from odoo.tools.misc import formatLang

# 5: local imports

# 6: Import of unknown third party lib

class InheritTwAssetAdjustment(models.Model):
    _name = "tw.asset.adjustment"
    _inherit = ['tw.asset.adjustment','tw.approval.mixin']


    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('post',),
    ], string="Status")


    def action_request_approval(self):
        self.ensure_one()
        # Validasi kapitalisasi lines sebelum request approval
        self._validate_capitalization_lines()
        # ? mengikuti TEDS 1.0
        return super().action_request_approval(value=5)