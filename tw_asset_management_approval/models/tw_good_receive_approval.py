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

class InheritStockPickingAsset(models.Model):
    _name = "tw.good.receive"
    _inherit = ['tw.good.receive','tw.approval.mixin']

    def _get_new_state_selection(self):
        return [
            ('draft', 'Draft'),
            ('waiting_for_approval','Waiting For Approval'),
            ('approved','Approved'),
            ('open', 'Open'),
            ('partial_invoiced', 'Partial Invoiced'),
            ('invoiced', 'Invoiced'),
            ('cancel', 'Cancelled'),
            ('done', 'Done')
        ]
    state = fields.Selection(_get_new_state_selection, string="Status")

    approval_ids = fields.One2many('tw.approval.line', 'transaction_id', string="Table Approval", domain=[('model_id', '=', 'tw.good.receive')])

    def _get_state_value(self):
        """Mengambil label yang sesuai dengan key di state."""
        selection = self._fields.get('state') and self._fields['state'].selection
        if callable(selection):
            selection = selection(self)
        return dict(selection).get(self.state, self.state) if selection else self.state

    def action_request_approval(self):
        if self.state != 'draft':
                raise Warning(f'Tidak bisa melakukan RFA. Silakan refresh halaman ini,karena state sudah {self._get_state_value()}')
            
        self.ensure_one()
        if self.is_asset:
            total = self.tax_totals.get('total_amount')
            return super().action_request_approval(value=total)
        else:
            return super().action_request_approval()