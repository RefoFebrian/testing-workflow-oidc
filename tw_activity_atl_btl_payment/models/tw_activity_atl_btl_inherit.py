# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class ActivityATLBTLInherit(models.Model):
    _inherit = "tw.activity.atl.btl"

    total_ho_expense = fields.Float('Total Beban HO', compute="compute_expense_amount", store=True)
    total_leasing_expense = fields.Float('Total Beban Leasing', compute="compute_expense_amount", store=True)
    total_company_expense = fields.Float('Total Beban Cabang', compute="compute_expense_amount", store=True)
    total_support_fund = fields.Float('Total Dana Bantuan', compute="compute_expense_amount", store=True)
    total_tax_btl = fields.Float('Total Pajak', compute="compute_expense_amount", store=True)

    @api.depends('activity_line_ids', 'activity_line_ids.total_ho_expense', 'activity_line_ids.total_leasing_expense', 'activity_line_ids.total_company_expense', 'activity_line_ids.total_support_fund_expense', 'activity_line_ids.total_tax_amount')
    def compute_expense_amount(self):
        for record in self:
            total_ho_expense = 0
            total_leasing_expense = 0
            total_company_expense = 0
            total_support_fund = 0
            total_tax_btl = 0
            for activity_line in record.activity_line_ids:
                if activity_line.state != 'reject':
                    total_ho_expense += activity_line.total_ho_expense
                    total_leasing_expense += activity_line.total_leasing_expense
                    total_company_expense += activity_line.total_company_expense
                    total_support_fund += activity_line.total_support_fund_expense
                    total_tax_btl += activity_line.total_tax_amount

            record.total_ho_expense = total_ho_expense
            record.total_leasing_expense = total_leasing_expense
            record.total_company_expense = total_company_expense
            record.total_support_fund = total_support_fund
            record.total_tax_btl = total_tax_btl