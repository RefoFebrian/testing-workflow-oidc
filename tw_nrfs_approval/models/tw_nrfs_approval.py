from odoo import models, fields
from odoo.exceptions import UserError as Warning

class ApprovalNRFS(models.Model):
    _name = "tw.nrfs"
    _inherit = ["tw.nrfs", "tw.approval.mixin"]

    state = fields.Selection(selection_add=[
        ('cancel',),
        ('draft',),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('approved', 'Approved'),
        ('confirmed',), # NOTE: in this state, all stock part OK
        ('in_progress',),
        ('done',)
    ], string="Status")

    approval_ids = fields.One2many('tw.approval.line', 'transaction_id', string="Table Approval", domain=[('model_id', '=', _inherit)])
    
    def action_rfa(self):
        if not self.line_ids:
            raise Warning("Perhatian!\nTab Line tidak boleh kosong!")
        
        self._check_line_ids()
        self.action_check_availability()
        value = sum(int(line.qty) for line in self.line_ids)
        return super().action_request_approval(value=value)

    def action_approve(self):
        self._check_line_ids()
        self.action_check_availability()
        return super().action_approval()
