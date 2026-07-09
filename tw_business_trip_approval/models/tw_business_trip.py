from odoo import models, fields
from odoo.exceptions import UserError as Warning
from datetime import datetime

class TwBusinessTrip(models.Model):
    _name = "tw.business.trip"
    _inherit = ["tw.business.trip", "tw.approval.mixin"]
    
    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('upload_ticket',),
        ('selesai_upload_ticket',),
        ('departed',),
        ('arrived',),
        ('advance_payment',),
        ('settlement',),
        ('payment_request',),
        ('supplier_payment',),
        ('done',),
        ('reject','Rejected'),
        ('revisi',),
    ])

    def action_rfa(self):
        planning_amount_total = self.planning_amount_total
        self.action_request_approval(value=planning_amount_total, code='other', product_tmpl_id=False, departement_id=self.pic_id.department_id.id)



    
   