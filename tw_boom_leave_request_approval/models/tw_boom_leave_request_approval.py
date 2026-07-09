# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import traceback
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib

class ApprovalLeave(models.Model):
    _name = "tw.boom.leave.request"
    _inherit = ["tw.boom.leave.request", "tw.approval.mixin"]

    # 7: defaults methods
    def get_default_datetime(self):
        return datetime.now()

    # 8: fields
    state = fields.Selection(selection_add=[
        ('waiting_for_approval', 'Waiting for Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string="State")
    
    # Audit Trail
    approved_uid = fields.Many2one('res.users','Approved by')
    approved_date = fields.Datetime('Approved on')
    rejected_uid = fields.Many2one('res.users','Rejected by')
    rejected_date = fields.Datetime('Rejected on')

    approval_ids = fields.One2many('tw.approval.line', 'transaction_id', string="Approval", domain=[('model_id', '=', 'tw.boom.leave.request')])

    def action_rfa(self):
        default = self.env['ir.config_parameter'].sudo().get_param('tw_boom_leave_request_approval.limit_approval_leave_request')
        self.action_request_approval(value=int(default), code='other')

    def action_approve(self):
        # Menyetujui permintaan approval
        approval_sts = super().action_approval()
        if approval_sts == 1:
            self.write({
                'approved_uid': self.env.user.id, 
                'approved_date': datetime.now()
            })

    def action_reject_or_cancel(self):
        # Menolak atau membatalkan permintaan approval
        update_values = {
            'state': 'draft',
            'rejected_uid':self._uid,
            'rejected_date':datetime.now(),
        }
        return super().action_reject_or_cancel(update_values=update_values)

    