from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning


class InheritStockOpnameAsset(models.Model):
    _name = "tw.stock.opname.asset"
    _inherit = ["tw.stock.opname.asset", "tw.approval.mixin"]

    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('posted',),
    ], string="Status")

    def action_request_approval(self):
        self._check_line()
        return super().action_request_approval(value=5)