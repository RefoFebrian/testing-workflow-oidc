# -*- coding: utf-8 -*-

from odoo import models, fields


class HrEmployeeDGI(models.Model):
    """Inherit hr.employee to add ATPM code for DGI integration"""
    _inherit = "hr.employee"

    md_employee_id = fields.Char(
        string='MD Employee ID',
        help='Employee code from ATPM/DGI system (idSalesPeople)'
    )
