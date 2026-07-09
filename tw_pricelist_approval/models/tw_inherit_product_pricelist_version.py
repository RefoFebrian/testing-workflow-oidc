# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions

from odoo.exceptions import UserError as Warning

from datetime import datetime, date

import logging
_logger = logging.getLogger(__name__)

class ProductPricelistVersion(models.Model):
    _inherit = "tw.product.pricelist.version"

    # Approval
    state = fields.Selection(selection_add=[
        ('waiting_for_approval','Waiting Approval'),
        ('approved', 'Approved'),
        ('confirmed',),
        ])
    approval_line_ids = fields.One2many('tw.approval.line', 'transaction_id', string="Approval", domain=[('model_id','=','tw.product.pricelist.version')])
    approval_state = fields.Selection([
        ('b','Belum Request'),
        ('rf','Request For Approval'),
        ('a','Approved'),
        ('r','Rejected')
        ], 'Approval State', readonly=True, default='b'
    )
    company_id = fields.Many2one('res.company',string="Branch",related='pricelist_id.company_id')
    
    def write(self,vals):
        return super().write(vals)
    
    def action_confirm(self):
        self._validate_pricelist_version()
        if self.approval_state != 'a':
            return self.action_rfa()
        else:
            return super().action_confirm()

    def action_rfa(self):
        self.generate_matrix_approval()
        self.write({
            'state':'waiting_for_approval'
        })
    
    def action_approve(self):
        approval_sts = self.env['tw.approval.matrix'].approve(self)
        if approval_sts == 1:
            self.write({'approval_state':'a','confirm_uid':self._uid,'confirm_date':datetime.now(),'state':'approved'})
            self.action_confirm()
        elif approval_sts == 0:
                raise Warning("Kamu tidak termasuk group Approval")
    
    def prepare_approval(self):
        vals = super().prepare_approval()
        pricelist_supplier = True
        approval_sts = self.env["tw.approval.matrix"].approve(self)
        if approval_sts == 1:
            vals.update({"approval_state": "a"})
        elif approval_sts == 0:
            pricelist_supplier = False
            raise Warning("Kamu tidak termasuk group Approval")
        return vals,pricelist_supplier

    def generate_matrix_approval(self):
        # Check Matrix Approval Duplication
        if self.approval_line_ids:
            last_approval_line_sts = self.approval_line_ids[-1].state
            # Generate when status is not 'Belum Approve'
            if last_approval_line_sts != 'open':
                self.env["tw.approval.matrix"].suspend_security().request_by_value(self, value=5)
                self.write({"approval_state":"rf"})
        else:
            self.env["tw.approval.matrix"].suspend_security().request_by_value(self, value=5)