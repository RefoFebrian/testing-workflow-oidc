# -*- coding: utf-8 -*-

# 1: imports of python lib
import ast

# 2: import of known third party lib
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning
from odoo.tools import SQL

# 5: local imports

# 6: Import of unknown third party lib


class EmployeeIncentiveHistory(models.Model):
    _name = "tw.employee.incentive.history"
    _description = "Employee Incentive History"
    _order = "id desc"

    # 7: defaults methods
    
    # 8: fields
    date = fields.Date(string="Date", help="Date of the incentive history record.")
    description = fields.Char(string="Description", help="Description or notes for this history entry.")
    value = fields.Integer(string="Value", help="Value associated with this history record (e.g., amount redeemed or penalty).")
    type = fields.Selection(
        selection=[('redeem', 'Redeem'), ('penalty', 'Penalty')],
        string="Type",
        help="Type of history record: Redeem (incentive redemption) or Penalty."
    )
    state = fields.Selection(
        selection=[('pending', 'Pending'), ('success', 'Success'), ('rejected', 'Rejected')],
        readonly=True,
        default='pending',
        string="State",
        help="Current state of this history record: Pending, Success, or Rejected."
    )
    alasan_reject = fields.Char(string="Alasan Reject", help="Reason for rejection, if this record was rejected.")
    
    # 8.1: audit trails
    reject_date = fields.Datetime(string="Reject On", help="Date when this history record was rejected.")
    reject_uid = fields.Many2one(comodel_name='res.users', string="Rejected By", help="User who rejected this record.")
    success_date = fields.Datetime(string="Success On", help="Date when this history record was marked as successful.")
    success_uid = fields.Many2one(comodel_name='res.users', string="Success By", help="User who marked this record as successful.")
    
    # 9: relation fields
    employee_incentive_id = fields.Many2one(
        comodel_name="tw.employee.incentive",
        string="Employee Incentive",
        help="Reference to the related employee incentive."
    )

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods
