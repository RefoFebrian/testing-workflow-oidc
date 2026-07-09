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

class ApprovalLineActivityATLBTL(models.Model):
    _name = "tw.activity.atl.btl.line"
    _inherit = ["tw.activity.atl.btl.line", "tw.approval.mixin"]
    _description = 'Approval Activity ATL & BTL Line'

    state = fields.Selection(selection_add=[
        ('draft',),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('approved', 'Approved'),
        ('open',),
        ('confirmed',),
        ('done',),
        ('rejected',),
        ('revision',),
    ])

    line_approval_ids = fields.One2many('tw.approval.line', 'transaction_id', string="Table Approval", domain=[('model_id', '=', _inherit)])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        create = super().create(vals_list)
        for record in create:
            is_add_activity = self._context.get('add_activity', False)
            if is_add_activity:
                record.action_open_activity()

        return create
    
    # 13: action methods
    def action_multi_rfa_event(self):
        for event in self:
            if event.state != 'open':
                raise Warning(f'Activity {event.name} tidak dalam state Open !')
            
            event.action_rfa()

        menu = self.env['ir.ui.menu'].search([('name', '=', 'Outstanding BTL')])
        return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {'menu_id': menu.id},
            }
            
    def action_rfa(self):
        total_cost = self.total_cost or 1
        self.action_request_approval(value=total_cost, code='other', product_tmpl_id=False)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def action_multi_approve_event(self):
        for event in self:
            if event.state != 'waiting_for_approval':
                raise Warning(f'Event {event.name} tidak dalam state Waiting For Approval !')
            
            event.action_approve()
        
        menu = self.env['ir.ui.menu'].search([('name', '=', 'Outstanding BTL')])
        return {
                'type': 'ir.actions.client',
                'tag': 'reload',
                'params': {'menu_id': menu.id},
            }

    def action_approve(self):
        # Menyetujui permintaan approval
        approval_sts = super().action_approval()
        if approval_sts == 1:
            self.write({
                'approved_loc_uid': self.env.user.id, 
                'approved_loc_date': datetime.now()
            })
            self.action_confirm_outstanding()
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        
    def action_reject(self):
        update_values = {
            'state': 'rejected',
            'reject_outstanding_uid':self._uid,
            'reject_outstanding_date':datetime.now(),
        }
        return super().action_reject_or_cancel(update_values=update_values)

    def action_revision(self):
        self.write(
            {'state': 'revision'}
        )
        return self.action_act_plan_status_reject_list()
    
    def action_activity_atl_btl_line_approval(self):
        list_id = self.env.ref('tw_activity_atl_btl_approval.tw_activity_atl_btl_line_approve_list_view').id
        form_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_line_all_form_view').id
        tgl = str(date.today())
        ids = []
        activity_ids = self.env['tw.activity.atl.btl.line'].search([('state','=','waiting_for_approval')]).ids
        domain = [('id','in',activity_ids)]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Approval Activity BTL',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.activity.atl.btl.line',
            'domain': domain,
            'views': [(list_id, 'list'), (form_id, 'form')],
        }

    def action_act_plan_status_reject_list(self):
        list_id = self.env.ref('tw_activity_atl_btl_approval.tw_activity_atl_btl_line_reject_list_view').id
        form_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_line_all_form_view').id
        search_id = self.env.ref('tw_activity_atl_btl_approval.tw_activity_atl_btl_line_reject_filter').id
        tgl = str(date.today())
        domain = [('state','=','rejected')]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Activity BTL Reject',
            'view_mode': 'list,form',
            'res_model': 'tw.activity.atl.btl.line',
            'domain': domain,
            'views': [(list_id, 'list'), (form_id, 'form')],
            'search_view_id': search_id,
            'context': {
                'reject_btl': True,
            },
            'flags': {
                'create': False,
                'edit': False,
                'delete': False,
            }
        }

    def action_act_plan_status_revision_list(self):
        list_id = self.env.ref('tw_activity_atl_btl_approval.tw_activity_atl_btl_line_reject_list_view').id
        form_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_line_all_form_view').id
        search_id = self.env.ref('tw_activity_atl_btl_approval.tw_activity_atl_btl_line_reject_filter').id
        tgl = str(date.today())
        domain = [('state','=','revision')]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Activity BTL Revision',
            'view_mode': 'list,form',
            'res_model': 'tw.activity.atl.btl.line',
            'domain': domain,
            'views': [(list_id, 'list'), (form_id, 'form')],
            'search_view_id': search_id,
            'context': {
                'revision_btl': True,
            },
            'flags': {
                'create': False,
                'edit': True,
                'delete': False,
            }
        }
    