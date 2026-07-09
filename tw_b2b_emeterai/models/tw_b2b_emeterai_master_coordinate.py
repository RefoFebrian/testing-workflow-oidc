# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError, ValidationError

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class TwB2BeMeteraiMasterCoordinate(models.Model):
    _name = "tw.b2b.emeterai.master.coordinate"
    _description = 'Master Koordinat Stamp e-Meterai'

    # 7: defaults methods
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()
    
    def _get_default_datetime(self):
        return datetime.now()

    # 8: fields
    name = fields.Char(string='Name')
    list_coordinate = fields.Char(string='Koordinat')
    amount_limit = fields.Float(string='Amount Limit', default=5000000)
    date = fields.Date(string='Date', default=_get_default_date)

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', domain=[('parent_id','!=',False)])
    model_id = fields.Many2one(comodel_name='ir.model', string='Model')
    report_id = fields.Many2one(comodel_name='ir.actions.report', string='Report')

    # 10: constraints & sql constraints
    _sql_constraints = [('master_coordinate_emeterai_unique', 'unique(company_id, model_id, report_id)', 'Master Koordinat e-Meterai tidak boleh duplikat !')]

    @api.constrains('list_coordinate')
    def _check_list_coordinate(self):
        if self.list_coordinate:
            # rule 1 & 2: check allowed characters and comma count
            allowed = set('0123456789., ')
            only_allowed = all(ch in allowed for ch in self.list_coordinate)
            comma_count = self.list_coordinate.count(',')

            # rule 3: check each split part is a valid decimal number
            valid_numbers = all(part.strip().replace('.', '', 1).isdigit() for part in self.list_coordinate.split(','))

            if not (only_allowed and comma_count == 3 and valid_numbers):
                raise ValidationError(_('Invalid value of Coordinate, please input like of e.g. !\ne.g. valid input: 154, 203, 201, 246'))

    # 11: compute/depends & on change methods
    @api.onchange('report_id')
    def _onchange_report_id(self):
        self.model_id = False
        if self.report_id:
            self.model_id = self.report_id.model_id.id
    
    @api.onchange('list_coordinate')
    def _onchange_list_coordinate(self):
        if self.list_coordinate:
            self.list_coordinate = ', '.join(self.list_coordinate.replace(' ', '').split(','))

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            branch_obj = self.env['res.company'].suspend_security().browse(vals['company_id'])
            vals['name'] = self.env['ir.sequence'].get_sequence_code('EMET-COORDINATE', branch_obj.code)

        emeterai = super(TwB2BeMeteraiMasterCoordinate, self).create(vals_list)

        return emeterai
    
    def write(self, vals):
        return super(TwB2BeMeteraiMasterCoordinate, self).write(vals)

    # 13: action methods
    def action_b2b_emeterai_master_coordinate_tree(self):
        domain = []
        name = 'Master Koordinat e-Meterai'
        path = 'master-koordinat-emeterai'
        list_view_id = self.env.ref('tw_b2b_emeterai.tw_b2b_emeterai_master_coordinate_list_view').id
        form_view_id = self.env.ref('tw_b2b_emeterai.tw_b2b_emeterai_master_coordinate_form_view').id
        search_view_id = self.env.ref('tw_b2b_emeterai.tw_b2b_emeterai_master_coordinate_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.b2b.emeterai.master.coordinate',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }

    # 14: private methods