# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.exceptions import ValidationError

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class EmployeeEvaluationPerformanceLine(models.Model):
    _name = "tw.employee.evaluation.performance.line"
    _description = 'Evaluation Performance Employee Line'
    _order = "id desc"

    # 7: defaults methods
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()
    
    def _get_default_datetime(self):
        return datetime.now()

    # 8: fields
    name = fields.Char(string='Name')
    point = fields.Integer(string='Point')
    target = fields.Integer(string='Target')
    result = fields.Integer(string='Result')
    point_result = fields.Integer(string='Point Result')
    is_achieve = fields.Boolean(string='Is Achieve?')

    # 9: relation fields
    employee_ep_id = fields.Many2one(comodel_name='tw.employee.evaluation.performance', string='Employee EP')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('result') >= vals.get('target'):
                vals['is_achieve'] = True

        return super(EmployeeEvaluationPerformanceLine, self).create(vals_list)

    def write(self, vals):
        if vals.get('result', 0) >= vals.get('target', 0):
            vals['is_achieve'] = True

        return super(EmployeeEvaluationPerformanceLine, self).write(vals)

    # 13: action methods

    # 14: private methods