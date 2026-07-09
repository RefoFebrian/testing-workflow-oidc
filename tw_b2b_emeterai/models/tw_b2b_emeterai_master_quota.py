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


class TwB2BeMeteraiMasterQuota(models.Model):
    _name = "tw.b2b.emeterai.master.quota"
    _description = 'Master Kuota Stamp e-Meterai'

    # 7: defaults methods
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()

    # 8: fields
    name = fields.Char(string='Name')
    quota = fields.Integer(string='Kuota')
    total_usage = fields.Integer(string='Total Penggunaan')
    date = fields.Date(string='Date', default=_get_default_date)

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', domain=[('parent_id','!=',False)])

    # 10: constraints & sql constraints
    _sql_constraints = [('master_quota_emeterai_unique', 'unique(company_id)', 'Master quota stamp e-Meterai tidak boleh duplikat !')]

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            branch_obj = self.env['res.company'].suspend_security().browse(vals['company_id'])
            vals['name'] = self.env['ir.sequence'].get_sequence_code('EMET-QUOTA', branch_obj.code)

        emeterai = super(TwB2BeMeteraiMasterQuota, self).create(vals_list)

        return emeterai
    
    def write(self, vals):
        return super(TwB2BeMeteraiMasterQuota, self).write(vals)

    # 13: action methods
    def action_b2b_emeterai_master_quota_tree(self):
        domain = []
        name = 'Master Kuota e-Meterai'
        path = 'master-kuota-emeterai'
        list_view_id = self.env.ref('tw_b2b_emeterai.tw_b2b_emeterai_master_quota_list_view').id
        form_view_id = self.env.ref('tw_b2b_emeterai.tw_b2b_emeterai_master_quota_form_view').id
        search_view_id = self.env.ref('tw_b2b_emeterai.tw_b2b_emeterai_master_quota_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.b2b.emeterai.master.quota',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def action_reset_total_usage_stamp_emeterai(self):
        self.suspend_security().write({'total_usage': 0})

    def schedule_auto_reset_total_usage_stamp_emeterai(self, **params):
        query_where = ''
        if 'query_where' in params:
            query_where = params.get('query_where')
        query = f"""
            SELECT
                JSON_AGG(tbemq.id) AS ids
            FROM tw_b2b_emeterai_master_quota tbemq
            WHERE 1=1
            AND tbemq.quota = tbemq.total_usage
            {query_where}
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        if ress:
            master_quota_objs = self.sudo().browse(ress[0]['ids'])
            for quota_obj in master_quota_objs:
                quota_obj.suspend_security().action_reset_total_usage_stamp_emeterai()
        
        return True

    # 14: private methods