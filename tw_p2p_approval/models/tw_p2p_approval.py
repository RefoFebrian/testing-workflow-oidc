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

class InheritTwP2pPurchaseOrder(models.Model):
    _name = "tw.p2p.purchase.order"
    _inherit = ["tw.p2p.purchase.order","tw.approval.mixin"]


    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('waiting_for_verification',)
    ], string="Status")

    def action_request_approval(self):
        self.ensure_one()
        if self.state not in ('draft','revisi'):
            raise UserError(f'Silakan refresh halaman PO P2P ini, karena state sudah {self._get_state_value()}')
        self.validate_order()
        total = 0
        for qty in self.purchase_line_ids :
            total = total + qty.fix_qty
        return super().action_request_approval(value=total)
    
    def action_approval(self):
        result = super().action_approval()
        if result == 1:  # Only call verification if approved
            self.action_verification()
        return result

    