# -*- coding: utf-8 -*-

# 1: imports of python lib
import ast

# 2: import of known third party lib
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports
import logging

# 6: Import of unknown third party lib


class EmployeeCareerRecord(models.Model):
    _name = "tw.employee.career.record"
    _description = "Employee Career Record"
    _order = "date_assign DESC"

    # 7: defaults methods
    
    # 8: fields
    name = fields.Char(help="Descriptive name for the career record") 
    type = fields.Selection(
        selection=lambda self: self.env['tw.selection'].get_option_list('CareerRecordType'),
        required=True,
        help="Type of career transition (e.g., promotion, transfer, demotion)"
    )
    model_name = fields.Char(help="Technical name of the related model (e.g., 'hr.job', 'res.company')", required=True)
    model_id = fields.Integer(help="ID of the related record in the specified model")
    date_assign = fields.Datetime(string='Assign Date', help="Date and time when the new role or job assignment takes effect")
    remark = fields.Char(help="Additional notes or comments about this career transition")
    prev_id = fields.Integer(help="ID of the previous record in the related model before the transition")
    curr_id = fields.Integer(help="ID of the new record in the related model after the transition")
    prev_name = fields.Char(compute='_compute_previous_career_transition', help="Name of the previous record before the transition")
    curr_name = fields.Char(compute='_compute_current_career_transition', help="Name of the new record after the transition")
    
    # 9: relation fields
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee')  # Good for UI
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.depends('model_name', 'prev_id')
    def _compute_previous_career_transition(self):
        for record in self:
            if record.model_name and record.prev_id:
                prev = record.env[record.model_name].browse(record.prev_id)
                if prev.exists():
                    record.prev_name = prev.name
                else:
                    record.prev_name = f"Deleted Record ({record.prev_id})"
            else:
                record.prev_name = False

    @api.depends('model_name', 'curr_id')
    def _compute_current_career_transition(self):
        for record in self:
            if record.model_name and record.curr_id:
                curr = record.env[record.model_name].browse(record.curr_id)
                if curr.exists():
                    record.curr_name = curr.name
                else:
                    record.curr_name = f"Deleted Record ({record.curr_id})"
            else:
                record.curr_name = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        hr_employee = self.env['hr.employee']
        for vals in vals_list:
            model = self.env[vals.get('model_name')]
            curr_id = model.suspend_security().browse(vals.get('curr_id'))
            employee = hr_employee.suspend_security().browse(vals.get('employee_id'))

            if vals.get('prev_id'):
                prev_id = model.suspend_security().browse(vals.get('prev_id'))
                vals['name'] = f'{employee.registry_number}:: {prev_id.name} -> {curr_id.name}'
            else:
                vals['name'] = f'{employee.registry_number}:: {curr_id.name}'
            
        return super().create(vals_list)
    
    # 13: action methods
    def get_career_record_by_date(self, employee, date, record_type='role'):
        """
        Get the latest career record for an employee up to a given date and type.

        Args:
            employee (int): Employee ID.
            date (str or datetime): Search up to this date.
            record_type (str): Career record types.

        Returns:
            recordset: Latest matching career record.

        Raises:
            Warning: If no record is found.
        """

        types = ['promotion', 'demotion', 'new_hire', 'contract_renewal']
        if record_type == 'mutation':
            types = ['transfer', 'rotation']
        elif record_type == 'termination':
            types = ['resignation', 'termination', 'retirement']
        
        career = self.search([('employee_id', '=', employee),
                              ('date_assign', '<=', date),
                              ('type', 'in', types)],
                              order='date_assign DESC', limit=1)
        return career
    
    def get_current_model_record(self):
        self.ensure_one()
        return self.env[self.model_name].browse(self.curr_id)
    
    # 14: private methods
