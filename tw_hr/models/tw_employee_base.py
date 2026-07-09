#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
from validate_email import validate_email
from datetime import datetime, date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class EmployeeBase(models.Model):
    _inherit = "hr.employee"
    _description = "Employee Base Inherit"

    # 7: defaults methods
    
    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def _create_work_contacts(self):

        res = super(EmployeeBase, self)._create_work_contacts()
        if self.work_contact_id:
            self.work_contact_id.category_id = self.env['hr.employee.category'].search([('name','=','Employees')],limit=1).id

        return res
        

    # 13: action methods 
