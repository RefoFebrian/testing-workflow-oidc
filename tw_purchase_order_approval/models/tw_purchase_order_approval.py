# -*- coding: utf-8 -*-

# 1: imports of python lib
import time
from datetime import datetime
import itertools
from lxml import etree

# 2: imports of odoo
from odoo import models, fields, exceptions, api, _
from odoo.exceptions import ValidationError as Warning

# 3: imports of odoo 

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class ApprovalPurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order","tw.approval.mixin"]
    
    
    # 8: fields
    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('purchase',),
    ])
    is_button_confirm_visible = fields.Boolean(compute="_compute_is_button_confirm_visible", string="Show Confirm")
    is_button_approve_visible = fields.Boolean(compute="_compute_is_button_confirm_visible", string="Show Approve")

    def _get_state_value(self):
        # Mengambil value yang sesuai dengan key di state
        selection = self._fields.get('state') and self._fields['state'].selection
        return dict(selection).get(self.state, self.state) if selection else self.state
    
    # Audit Trail
    confirm_date = fields.Datetime(string='Approved on')
    confirm_uid = fields.Many2one('res.users', string="Approved by")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('state','is_need_approval')
    def _compute_is_button_confirm_visible(self):
        for rec in self:
            is_asset = rec._context.get('is_asset')

            if not rec.is_need_approval:     
                #jika is need approval di setting branch = false, namun masih ada record yang butuh menjalankan proses approval
                if rec.state == 'waiting_for_approval':
                    rec.is_button_approve_visible = (rec.state == 'waiting_for_approval' and not is_asset)
                    rec.is_button_confirm_visible = False
                    continue
                rec.is_button_confirm_visible = (rec.state in ['approved','waiting_for_approval','draft'] and not is_asset)
                rec.is_button_approve_visible = False
                continue

            rec.is_button_confirm_visible = (rec.state == 'approved' and not is_asset)
            rec.is_button_approve_visible = (rec.state == 'waiting_for_approval' and not is_asset)

    # 12: override methods
    def button_confirm(self):
        for order in self:
            order.write({'state': 'draft'})

        return super().button_confirm()
    
    # 13: action methods
    def action_request_approval(self,code='other'):
        #jegatan double tab dengan cek state PO
        if self.state != 'draft':
            raise UserError(f'Silakan refresh halaman ini, karena state telah {self._get_state_value()}')
        # Mengajukan permintaan approval
        self._check_valid_po()
        
        return super(ApprovalPurchaseOrder,self).action_request_approval(code='purchase')

