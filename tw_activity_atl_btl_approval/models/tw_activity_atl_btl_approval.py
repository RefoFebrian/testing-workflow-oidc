# -*- coding: utf-8 -*-

# 1: imports of python lib
import time
from datetime import datetime, date
import calendar
import itertools
from lxml import etree

# 2: imports of odoo
from odoo import models, fields, exceptions, api, _
from odoo.exceptions import ValidationError as Warning

# 3: imports of odoo 

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class ApprovalActivityATLBTL(models.Model):
    _name = "tw.activity.atl.btl"
    _inherit = ["tw.activity.atl.btl", "tw.approval.mixin"]
    _description = 'Approval Activity ATL & BTL'
    
    # 8: fields
    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval',),
        ('approved',),
        ('open',),
        ('done',),
        ('rejected', 'Rejected')
    ])
    
    # Audit Trail
    approved_uid = fields.Many2one('res.users','Approved by')
    approved_date = fields.Datetime('Approved on')
    rejected_uid = fields.Many2one('res.users','Rejected by')
    rejected_date = fields.Datetime('Rejected on')
    
    # 9: relation fields
    approval_ids = fields.One2many('tw.approval.line', 'transaction_id', string="Table Approval", domain=[('model_id', '=', _inherit)])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_rfa(self):
        if not self.activity_line_ids:
            raise Warning('Activity Detail tidak boleh kosong !')

        total_cost = self.total_cost_btl or 1
        self.action_request_approval(value=total_cost, code='other', product_tmpl_id=False)

    def action_multi_approve(self):
        for activity in self:
            if activity.state != 'waiting_for_approval':
                raise Warning(f'Activity {activity.name} tidak dalam state Waiting For Approval !')
            if not activity.activity_line_ids:
                raise Warning(f'Activity Detail {activity.name} tidak boleh kosong !')
            
            activity.action_approve()

    def action_approval(self):
        super().action_approval()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def get_approve_additional_vals(self):
        approve_additional = super().get_approve_additional_vals()
        approve_additional.update({
            'approved_uid': self.env.user.id, 
            'approved_date': datetime.now()
        })
        for activity in self.activity_line_ids:
            if not activity.state == 'open':
                activity.action_open_activity()
        return approve_additional
    
    def action_reject(self):
        return super().action_reject_or_cancel(update_values={'state': 'draft'})
    

    def action_activity_atl_btl_approval(self):
        list_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_list_view').id
        form_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_form_view').id
        tgl = str(date.today())
        ids = []
        activity_ids = self.env['tw.activity.atl.btl'].search([('state','=','waiting_for_approval')]).ids
        domain = [('id','in',activity_ids)]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Approval Activity Plan',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.activity.atl.btl',
            'domain': domain,
            'views': [(list_id, 'list'), (form_id, 'form')],
            'context': {
                'approval_btl': True,
                'create': False,
                'edit': False,
                'delete': False,
            }
        }