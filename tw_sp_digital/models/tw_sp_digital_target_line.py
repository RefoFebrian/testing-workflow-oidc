# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class EmployeeSpDigitalTargetLine(models.Model):
    _name = "tw.sp.digital.target.line"
    _description = 'SP Digital Target Line'

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    # 8: fields
    qty = fields.Integer(string='Qty', help='')

    # 9: relation fields
    job_id = fields.Many2one(comodel_name='hr.job', string='Job', help='')
    sp_digital_target_id = fields.Many2one(comodel_name='tw.sp.digital.target', string='SP Digital Target', help='')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods

    # 14: private methods