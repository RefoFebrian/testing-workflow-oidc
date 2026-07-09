# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ActivityPlanDepartment(models.Model):
    _inherit= "hr.department"

    code = fields.Char('Department Code')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = vals.get('name').upper()
                
            if vals.get('manager_id'):
                manager_emp = self.manager_id.browse(vals['manager_id'])
                # manager_emp.write({'is_dept_head':True})
            vals['active'] = True
        create = super(ActivityPlanDepartment,self).create(vals_list)
        return create

    def write(self,vals):
        if vals.get('name'):
             vals['name'] = vals.get('name').upper()

        if vals.get('manager_id'):
            # if self.manager_id:
                # self.manager_id.write({'is_dept_head':False})
            manager_emp = self.manager_id.browse(vals['manager_id'])
            # manager_emp.write({'is_dept_head':True})
            
        return super(ActivityPlanDepartment,self).write(vals)