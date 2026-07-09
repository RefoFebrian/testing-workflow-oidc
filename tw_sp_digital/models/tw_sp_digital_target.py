# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class EmployeeSpDigitalTarget(models.Model):
    _name = "tw.sp.digital.target"
    _description = 'SP Digital Target'

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    # 8: fields
    date = fields.Date(string='Date', readonly=True, default=_get_default_date)

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', help='', domain=[('parent_id','!=',False)])
    line_ids = fields.One2many(comodel_name='tw.sp.digital.target.line', inverse_name='sp_digital_target_id', string='Lines', help='')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_sp_digital_target_tree(self):
        domain = []
        name = 'Master Target SP Digital'
        path = 'master-target-sp-digital'
        list_view_id = self.env.ref('tw_sp_digital.tw_sp_digital_target_list_view').id
        form_view_id = self.env.ref('tw_sp_digital.tw_sp_digital_target_form_view').id
        search_view_id = self.env.ref('tw_sp_digital.tw_sp_digital_target_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.sp.digital.target',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }

    # 14: private methods