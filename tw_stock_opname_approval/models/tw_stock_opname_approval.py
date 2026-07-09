from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning


class InheritStockOpname(models.Model):
    _name = "tw.stock.opname"
    _inherit = ["tw.stock.opname", "tw.approval.mixin"]

    state = fields.Selection(selection_add=[
        ('in_progress',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('done',),
    ], string="Status")
    
    def action_rfa(self):
        self._check_line()
        open_opname_ids = filter(lambda x: x.state == 'open', self.open_opname_ids)
        return self.action_open_wizard(open_opname_ids)

    def action_request_approval(self):
        self._check_line()
        return super().action_request_approval(5, 'other')
    
    def action_approval(self):
        self.action_force_done()
        return super().action_approval()
        
    def action_reject_or_cancel(self):
        for acc_opname in self.open_accessories_opname_ids:
            if acc_opname.reason:
                acc_opname.write({'reason': False})
        
        for unit_opname in self.open_opname_ids:
            if unit_opname.reason:
                unit_opname.write({'reason': False})
                
        return super().action_reject_or_cancel({"state" : "in_progress"})