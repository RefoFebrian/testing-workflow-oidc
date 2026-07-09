# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwLeadCrmMatrixAssignmentLine(models.Model):
    _name = "tw.lead.crm.matrix.assignment.line"
    _order = "sequence DESC"
    _description = 'Matrix Lead Assignment Line'

    # 7: defaults methods

    # 8: fields
    sequence = fields.Integer(string='Sequence')

    # 9: relation fields
    matrix_assignment_id = fields.Many2one(comodel_name='tw.lead.crm.matrix.assignment', string='Matrix Lead Assignment')
    job_id = fields.Many2one(comodel_name='hr.job', string='Job')

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('seq_uniq', 'unique(sequence, matrix_assignment_id)', 'Sequence tidak boleh sama !'),
        ('job_id_uniq', 'unique(job_id, matrix_assignment_id)', 'Job Title yang dipilih tidak boleh sama !')
    ]

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('sequence') == 0:
                raise Warning('Sequence Harus Lebih dari 0.')
        
        return super(TwLeadCrmMatrixAssignmentLine, self).create(vals)
    
    def write(self, vals):
        if vals.get('sequence') == 0:
            raise Warning('Sequence Harus Lebih dari 0.')
        
        return super(TwLeadCrmMatrixAssignmentLine, self).write(vals)

    # 13: action methods

    # 14: private methods