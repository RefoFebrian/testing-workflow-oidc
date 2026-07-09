# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class ApiURL(models.Model):
    _name = "tw.api.url"
    _description = 'API URL'

    # 7: defaults methods

    # 8: fields
    type = fields.Selection(selection=lambda self: self.env['tw.selection'].get_option_list('ApiURL'), default='-', string='Type')
    url = fields.Char(string='URL')
    is_relative = fields.Boolean(string='Relative')

    # 9: relation fields
    api_config_id = fields.Many2one(comodel_name='tw.api.configuration', string='Config', domain=[('is_api_payment','=',True), ('partner_id','!=',False)])

    # 10: constraints & sql constraints
    _sql_constraints = [('config_type_unique', 'unique(api_config_id, type)', 'Type tidak boleh duplikat !')]

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_api_url_tree(self):
        domain = []
        name = 'API URL'
        path = 'api-url'
        list_view_id = self.env.ref('tw_b2b_bank.tw_api_url_list_view').id
        form_view_id = self.env.ref('tw_b2b_bank.tw_api_url_form_view').id
        search_view_id = self.env.ref('tw_b2b_bank.tw_api_url_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.api.url',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }

    # 14: private methods
    def _get_api_url_by_type(self, config_obj, type, is_relative=True, is_get_object=False):
        url_obj = self.sudo().search([
            ('api_config_id','=',config_obj.id),
            ('type','=',type)
        ], limit=1)
        if not url_obj:
            raise Warning(f'API URL untuk type {type} pada config {config_obj.name} tidak ada!')
        
        url = url_obj.url
        if not is_relative:
            url = config_obj.base_url + url

        if is_get_object:
            return url_obj
        else:
            return url