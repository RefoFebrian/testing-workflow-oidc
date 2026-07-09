# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class HrEmployeeOauth(models.Model):
    _inherit = "hr.employee"
    
    is_oauth = fields.Boolean(string='Is Oauth?')

    @api.onchange('is_user')
    def _onchange_is_user(self):
        if self.is_user:
            self.is_oauth = True
        else:
            self.is_oauth = False

    @api.model_create_multi
    def create(self, vals_list):
        create = super().create(vals_list)
        for employee in create:
            employee.sync_user_oauth()
        
        return create

    def write(self,vals):
        write = super().write(vals)
        for employee in self:
            if vals.get('work_email') and employee.user_id:
                employee.sync_user_oauth()
        return write
    
    def sync_user_oauth(self):
        if self.user_id and self.is_oauth:
            vals = self._get_user_oauth_vals(self.work_email)
            self.user_id.sudo().write(vals)
    
    def _get_user_vals(self):
        vals = super()._get_user_vals()
        if self.work_email and self.is_oauth:
            vals.update(self._get_user_oauth_vals(self.work_email))
        return vals
    
    def _get_user_oauth_vals(self, email):
        try:
            provider_code = email.split('@')[1].split('.')[0]
        except:
            # if email is not valid, use gmail as default
            provider_code = 'gmail'

        oauth_obj = self.env['auth.oauth.provider'].sudo().search([('enabled','=',True),('code','=',provider_code)],limit=1)
        return {
            'oauth_provider_id':oauth_obj.id if oauth_obj else False,
            'oauth_uid':email,
        }

