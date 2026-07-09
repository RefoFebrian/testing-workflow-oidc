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
from datetime import date, datetime, time,timedelta
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TwEmployeeHistoricalReport(models.TransientModel):
    _name = "tw.employee.historical.report"
    _description = "TW Employee Historical Report"

    # 7: defaults methods
    def _get_default_date(self): 
        return datetime.now()

    # 8: fields
    name = fields.Char('File Name')
    month = fields.Selection([
        ('01', 'Januari'), ('02', 'Februari'), ('03', 'Maret'),
        ('04', 'April'), ('05', 'Mei'), ('06', 'Juni'),
        ('07', 'Juli'), ('08', 'Agustus'), ('09', 'September'),
        ('10', 'Oktober'), ('11', 'November'), ('12', 'Desember'),
    ], string='Month',default=str(datetime.now().month).zfill(2))
    year = fields.Selection(
        [(str(num), str(num)) for num in range(1978, (datetime.now().year)+3)],
        string='Year',
        default=str(datetime.now().year)
    )

    # 9: relation fields
    company_ids = fields.Many2many('res.company',string="Branch",required=True)
    department_ids = fields.Many2many('hr.department',string='Departments',required=True)

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods

    # 12: Override Methods

    # 13: Action Methods
    def excel_report(self):
        date_end = (
            date(int(self.year), int(self.month), 1) 
            + relativedelta(months=1)
        ) - timedelta(days=1)
        
        query_where = " WHERE he.working_start_date >= '%s'" %str(self.year + '-' + self.month + '-01') + " AND he.working_start_date <= '%s'" %str(self.year + '-' + self.month + '-' + str(date_end.day))
        
        if self.company_ids:
            query_where += f" AND he.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND he.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        if self.department_ids:
            query_where += " AND he.department_id in %s" % str(tuple(self.department_ids.ids)).replace(',)', ')')

        query = f"""
            select
            rc.name as "Dealer",
            he.name as "Nama Pegawai",
            he.registry_number as "NIP",
            he.working_start_date as "Tanggal Masuk",
            he.working_end_date as "Tanggal Keluar",
            hj.name->>'en_US' as "Pekerjaan",
            hd.name->>'en_US' as "Departemen",
            coach.name as "Atasan",
            ra.name as "Area",
            he.mobile_phone as "No. HP",
            he.work_email as "Email",
            karir_type.name as "Type"
            from hr_employee he 
            left join res_company rc on rc.id = he.company_id
            left join hr_job hj on hj.id = he.job_id
            left join hr_department hd on hd.id = he.department_id
            left join hr_employee coach on coach.id = he.coach_id
            left join res_area ra on ra.id = he.area_id
            left join tw_employee_career_record karir on karir.employee_id = he.id
            left join tw_selection karir_type on karir.type = karir_type.value
            {query_where}
            group by he.name,rc.name,he.registry_number,he.working_start_date,he.working_end_date,hj.name,hd.name,coach.name,ra.name,he.mobile_phone,he.work_email,karir_type.name
            order by he.name
        """
        
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
        start_date,end_date = self._get_date_range()
        return self.env['web.report'].sudo().generate_report('Report Employee Historical',ress, data_summary_header=False, start_date=start_date, end_date=end_date)

    def _get_date_range(self):
        # Get the day end of the current month
        date_end = (
            date(int(self.year), int(self.month), 1) 
            + relativedelta(months=1)
        ) - timedelta(days=1)

        if self.month:
            start_date = f"{self.year}-{self.month}-01"
        else:
            start_date = self._get_default_date().strftime('%Y-%m-%d')
        if self.year:
            end_date = f"{self.year}-{self.month}-{date_end.day}"
        else:
            end_date = date_end.strftime('%Y-%m-%d')
        return start_date,end_date