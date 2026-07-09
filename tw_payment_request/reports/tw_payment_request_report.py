# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
import pytz
import base64
import csv
import xlsxwriter
import calendar
from io import StringIO,BytesIO
from datetime import date, datetime, time, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TwPaymentRequestReport(models.TransientModel):
    _name = "tw.payment.request.report"
    _description = "Report Payment Request"

    def _get_default_date(self): 
        return datetime.now()
    
    name = fields.Char('File Name')
    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)
    transaction_type = fields.Selection([
        ('non_recurring', 'Non-Recurring'),
        ('recurring', 'Recurring'),
    ], string='Transaction Type', default='non_recurring')

    # 9: relation fields
    user_id = fields.Many2one('res.users', string='Upload By')
    payment_ids = fields.Many2many('tw.payment.request',string='Vouchers', domain="[('type','=','payment_request')]",)
    company_ids = fields.Many2many('res.company',string="Branch")
    employee_ids = fields.Many2many('hr.employee',string='Employees')
    payment_request_type_id = fields.Many2one('tw.payment.request.type', string='Payment Request Type')
    
    
    def action_download(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query_where = "WHERE 1=1 AND payment.type = 'payment_request'"
        query_where += f" AND payment.date BETWEEN '{self.start_date}' AND '{self.end_date}'"
        
        if self.company_ids:
            query_where += f" AND payment.company_id IN {str(tuple([b.id for b in self.company_ids])).replace(',)', ')')}"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND payment.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        if self.user_id:
            query_where += f" AND payment.user_id = {self.user_id.id}"
        if self.payment_request_type_id:
            query_where += f" AND payment.payment_request_type_id = {self.payment_request_type_id.id}"
        if self.transaction_type:
            query_where += f" AND payment.transaction_type = '{self.transaction_type}'"
        if self.employee_ids:
            query_where += f" AND emp.id IN {str(tuple([e.id for e in self.employee_ids])).replace(',)', ')')}"
        if self.payment_ids:
            query_where += f" AND payment.id IN {str(tuple([v.id for v in self.payment_ids])).replace(',)', ')')}"

        query = f"""
            SELECT
                COALESCE(TO_CHAR(payment.date, 'YYYY/MM'),'') AS period
                ,COALESCE(payment.name,'') AS ref
                ,COALESCE(payment.state,'') AS state
                ,COALESCE(emp.name,'') AS name
                ,COALESCE(emp.tax_number,'') AS npwp
                ,COALESCE(emp.identification_id,'') AS no_ktp
                ,COALESCE(emp.private_street,'') AS address
                ,COALESCE(line.amount,0)::BIGINT AS bruto
            FROM tw_payment_request_line line
                JOIN tw_payment_request payment ON payment.id = line.payment_id
                LEFT JOIN hr_employee emp ON emp.id = line.employee_id
            {query_where}
        """
        
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        filename = f"Report Payment Request_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.xlsx"
        return self.env['web.report'].sudo().generate_report('Report Payment Request',ress)
    
    
