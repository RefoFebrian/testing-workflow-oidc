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


class TwHutangKomisi(models.Model):
    _name = "tw.commission"     
    _inherit = ["tw.commission", "tw.approval.mixin"]
    _description = 'Approval Hutang Komisi'

    state = fields.Selection(
        selection_add=[
            ('waiting_for_approval','Waiting For Approval'),
            ('approved','Approved'),
            ('confirm',)
        ], 
        ondelete={
            'waiting_for_approval': 'set default',
            'approved': 'set default',
        }
    )

    approval_ids = fields.One2many('tw.approval.line', 'transaction_id', string="Table Approval", domain=[('model_id', '=', _name)])
    
    def action_request_approval(self):
        value = self.amount_commission or 0.0
        return super().action_request_approval(value=value)
    
    def action_approve(self):
        self.action_approval()
    
    def action_approval(self):
        res = super().action_approval()
        if res == 1:
            self.action_confirm()
        return res
    
    def action_set_to_draft(self):
        self.write({'state': 'draft'})
        
    def action_extend_periode(self):    
        so = self.env['tw.dealer.sale.order.line']
        so_search = so.search([('commission_id', '=', self.id)])
        if so_search:
            self.state = 'editable'
        else:
            self.state = 'on_revision' 
    
    def action_revise(self):    
        so = self.env['tw.dealer.sale.order.line']
        so_search = so.search([('commission_id', '=', self.id)])  
        if so_search:
            self.state = 'editable'
        else:
            self.state = 'on_revision'


    def get_approve_additional_vals(self):
        self.ensure_one()
        return {
            'confirm_uid': self._uid,
            'confirm_date': datetime.now(),
            'state': 'approved'
        }
