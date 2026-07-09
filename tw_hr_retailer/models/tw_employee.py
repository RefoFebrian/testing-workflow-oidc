#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class EmployeeSales(models.Model):
    _inherit = "hr.employee"
    _description = "Employee for Sales"

    # 7: defaults methods

    # 8: fields
    temporary_id = fields.Char(string='Temporary ID',  help='')
    atpm_id = fields.Char( string='ATPM ID',  help='')
    
    # 10: constraints & sql constraints
    _sql_constraints = [
        ('atpm_id_uniq', 'unique (atpm_id)', 'ATPM ID harus unik.'),
        ('temporary_id_uniq', 'unique (temporary_id)', 'ATPM ID harus unik.')
    ]
