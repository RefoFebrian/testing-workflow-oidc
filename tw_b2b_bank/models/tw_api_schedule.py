# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class ApiSchedule(models.Model):
    _name = "tw.api.schedule"
    _description = 'API Schedule'

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Schedule')

    # 9: relation fields
    line_ids = fields.One2many(comodel_name='tw.api.schedule.line', inverse_name='schedule_id', string='Detail Schedule API')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_api_schedule_tree(self):
        domain = []
        name = 'API Schedule'
        path = 'api-schedule'
        list_view_id = self.env.ref('tw_b2b_bank.tw_api_schedule_list_view').id
        form_view_id = self.env.ref('tw_b2b_bank.tw_api_schedule_form_view').id
        search_view_id = self.env.ref('tw_b2b_bank.tw_api_schedule_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.api.schedule',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }

    # 14: private methods