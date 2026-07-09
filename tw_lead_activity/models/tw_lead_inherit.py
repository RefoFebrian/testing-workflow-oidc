# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwCRMLeadInherit(models.Model):
    _inherit = "tw.lead"

    # 7: default methods
    
    # 8: fields
    remark = fields.Text(string='Remark', help='')
    not_followed_up = fields.Boolean(string='Not Followed Up', compute='_compute_followup', store=True, help="")
    follow_up_date = fields.Datetime(string='Follow-Up Date', compute='_compute_followup', store=True, help="")
    follow_up_count = fields.Integer(string='Follow-Up Count', compute='_compute_followup', store=True, help="")
    
    # 9: relation fields
    activity_result_id = fields.Many2one(comodel_name='tw.lead.activity.result', string='Follow-up Result', help='')
    next_activity_id = fields.Many2one(comodel_name='tw.lead.activity', string="Next Activity", store=True)
    lead_activity_ids = fields.One2many(comodel_name='tw.lead.activity', inverse_name='lead_id')
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.depends('lead_activity_ids', 'lead_activity_ids.activity_result_id')
    def _compute_followup(self):
        for lead in self:
            lead.follow_up_count = len(lead.lead_activity_ids)
            if lead.lead_activity_ids:
                incompleted_activity = lead.lead_activity_ids.filtered(lambda activity: not activity.activity_result_id).sorted('id')
                if incompleted_activity:
                    lead.not_followed_up = True
                    lead.follow_up_date = incompleted_activity[0].date
                else:
                    lead.not_followed_up = False
                    lead.follow_up_date = False
    
    # 12: override methods
    
    # 13: action methods
    def action_show_deal_form(self):
        self.ensure_one()
        if self.lead_activity_ids:
            for act in self.lead_activity_ids:
                if not act.activity_result_id:
                    raise Warning(_(f"Please fill in the Follow-Up Result for the date {act.date}, the data is still empty"))
                
        return super().action_show_deal_form()
                
    def action_activity(self):
        self.ensure_one()

        form1_id = self.env.ref('tw_lead_activity.view_tw_lead_activity_first_view_form').id
        form2_id = self.env.ref('tw_lead_activity.view_tw_lead_activity_second_form').id

        outstanding_activity_obj = self.lead_activity_ids.filtered(lambda x: x.activity_result_id == False)
        if not self.next_activity_id and not outstanding_activity_obj:
            return {
                'name': ('Next activity'),
                'res_model': 'tw.lead.activity',
                'context': {
                    'default_lead_id': self.id,
                },
                'type': 'ir.actions.act_window',
                'view_id': False,
                'views': [(form1_id, 'form')],
                'view_mode': 'form',
                'target': 'new',
                'view_type': 'form',
                'res_id': False
            }
        
        if self.next_activity_id or outstanding_activity_obj:
            res_id = self.next_activity_id.id
            if not res_id:
                res_id = outstanding_activity_obj.id
                
            for record in self.lead_activity_ids:
                if record.activity_result_id or record.interest_id:
                    continue
                self.stage_id = record.stage_id.id
                if (not record.activity_result_id) or (not record.interest_id):
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Activity'),
                        'view_type': 'form',
                        'view_mode': 'list,form',
                        'res_model': 'tw.lead',
                        # 'context':{'active_id':self.id},
                        'res_id': self.id,
                        'views': [(form2_id, 'form')],
                        'target':'new'
                    }
                else:
                    return {
                        'type': 'ir.actions.act_window',
                        'name': ('Activity'),
                        'view_type': 'form',
                        'view_mode': 'list,form',
                        'res_model': 'tw.lead.activity',
                        # 'context':{'active_id':self.id},
                        'res_id': self.id,
                        'views': [(form2_id, 'form')],
                        'target':'new'
                    }
            return {
                'name': ('Next activity'),
                'res_model': 'tw.lead.activity',
                'context': {
                    'default_lead_id': self.id,
                },
                'type': 'ir.actions.act_window',
                'view_id': False,
                'views': [(form1_id, 'form')],
                'view_mode': 'form',
                'target': 'new',
                'view_type': 'form',
                'res_id': False
            }

    def action_add_only(self):
        self.ensure_one()
        outstanding_activity_obj = self.next_activity_id

        vals = {
            'activity_result_id': self.activity_result_id.id,
            'remark': self.remark,
        }

        riding_test_id = self.env.ref('tw_lead.tw_lead_crm_stage_riding_test').id
        if self.stage_id.id == riding_test_id:
            vals.update({'is_test_ride': True, 'test_ride_date': self._get_default_datetime()})
    
        outstanding_activity_obj.write(vals)
        self.next_activity_id = False

    def action_add_and_next_activity(self):
        self.ensure_one()
        self.action_add_only()
        form1_id = self.env.ref('tw_lead_activity.view_tw_lead_activity_first_view_form').id
        return {
            'name': ('Next Activity'),
            'res_model': 'tw.lead.activity',
            'context': {
                'default_lead_id': self.id,
            },
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(form1_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'view_type': 'form'
        }
    # 14: private methods
    