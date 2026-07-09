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

class InheritTwAssetLending(models.Model):
    _name = "tw.asset.lending"
    _inherit = ['tw.asset.lending','tw.approval.mixin']


    state = fields.Selection(selection_add=[
        ('draft'),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
    ], string="Status")


    approval_ids = fields.One2many('tw.approval.line', 'transaction_id', string="Table Approval", domain=[('model_id', '=', _name)])

    def action_request_approval(self):
        self.ensure_one()
        # Nilai Value mengikuti TEDS 1.0
        return super().action_request_approval(value=2)
    
    def action_print_asset_lending(self):
        self.ensure_one()
        return self.env.ref('tw_asset_lending_return_approval.action_report_asset_lending_return_print').report_action(self)