# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwLeadCrmMatrixAssignment(models.Model):
    _name = "tw.lead.crm.matrix.assignment"
    _order = "id DESC"
    _description = 'Matrix Lead Assignment'

    # 7: defaults methods

    # 8: fields
    data_source = fields.Selection(selection=[
        ('web','Web'),
        ('apps','Apps'),
        ('s3_aws','S3 AWS')
    ], string='Data source')

    # 9: relation fields
    line_ids = fields.One2many(comodel_name='tw.lead.crm.matrix.assignment.line', inverse_name='matrix_assignment_id', string='Matrix Assignment Line')

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('data_source_uniq', 'unique(data_source)', 'Data source sudah terbuat !')
    ]

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_lead_crm_matrix_assignment_tree(self):
        domain = []
        list_view_id = self.env.ref('tw_lead_crm.tw_lead_crm_matrix_assignment_list_view').id
        form_view_id = self.env.ref('tw_lead_crm.tw_lead_crm_matrix_assignment_form_view').id
        search_view_id = self.env.ref('tw_lead_crm.tw_lead_crm_matrix_assignment_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Matrix Lead Assignment',
            'path': 'lead-crm-matrix-assignment',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.lead.crm.matrix.assignment',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {'search_default_fieldname': 1},
        }

    # 14: private methods