# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class EmployeeSpDigitalLine(models.Model):
    _name = "tw.sp.digital.line"
    _description = 'SP Digital Line'

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    # 8: fields
    name = fields.Char(string='Name')
    date = fields.Date(string='Date', readonly=True, default=_get_default_date)
    sp_level = fields.Selection(string='SP', selection=[
        ('1', '1'),
        ('2', '2'),
        ('3', '3')
    ])
    type = fields.Selection(string='Type', selection=[
        ('performance', 'Performance'),
        ('indisipliner', 'Indisipliner'),
        ('previous_sp', 'Previous SP')
    ])
    state = fields.Selection(string='State', selection=[
        ('active', 'Active'),
        ('done', 'Done')
    ], default='active')
    keterangan = fields.Text(string='Keterangan')

    # 9: relation fields
    sp_digital_id = fields.Many2one(comodel_name='tw.sp.digital', string='SP Digital')
    employee_id = fields.Many2one(comodel_name='hr.employee', related='sp_digital_id.employee_id', string='Employee')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                emp_obj = self.env['hr.employee'].suspend_security().browse(vals['employee_id'])
                vals['name'] = self.env['ir.sequence'].get_sequence_code('SPD', emp_obj.company_id.code)

        return super(EmployeeSpDigitalLine, self).create(vals_list)
    
    # 13: action methods

    # 14: private methods