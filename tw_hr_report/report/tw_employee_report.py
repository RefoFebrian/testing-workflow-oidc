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
from datetime import date, datetime, time

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TwEmployeeReport(models.TransientModel):
    _name = "tw.employee.report"
    _description = "TW Report Employee"

    # 7: defaults methods
    def _get_default_date(self): 
        return datetime.now()

    # 8: fields
    name = fields.Char('File Name')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    status = fields.Selection([
        ('all','All'),
        ('aktif','Aktif'),
        ('non_aktif','Non Aktif')
    ])

    # 9: relation fields
    company_ids = fields.Many2many('res.company',string="Branch",required=True)
    job_ids = fields.Many2many('hr.job',string='Job Title',required=True)
    department_ids = fields.Many2many('hr.department', string='Department')

    # 10: Constraints & SQL Constraints

    # 11: Compute/Depends & On Change Methods

    # 12: Override Methods

    # 13: Action Methods
    def excel_report(self):
        # Querry
        start_date = self.start_date
        end_date = self.end_date
        branch_ids = self.company_ids.ids
        status = self.status
        job_ids = self.job_ids.ids
        department_ids = self.department_ids.ids

        query_where = " AND 1=1"
        
        if status == 'aktif' :
            query_where += " AND employee.working_end_date IS NULL"
        elif status == 'non_aktif' :
            query_where += " AND employee.working_end_date >= '%s'" %str(start_date) + " AND employee.working_end_date <= '%s'" %str(end_date) + " AND employee.working_end_date IS NOT NULL" 

        company_ids = [b.id for b in self.company_ids]
        if company_ids :
            query_where += " AND employee.company_id in %s " % str(tuple(company_ids)).replace(',)', ')')

        if branch_ids :
            query_where += " AND b.id in %s" % str(
                tuple(branch_ids)).replace(',)', ')')
        # where_job_ids = " and 1=1 "
        if job_ids :
            query_where += " AND job.id in %s" % str(
                tuple(job_ids)).replace(',)', ')')

        if department_ids :
            query_where += " AND employee.department_id in %s" % str(
                tuple(department_ids)).replace(',)', ')')

        query = f"""
            SELECT 
            b.code as branch_code, 
            b.name as branch_name, 
            area.code as area_code, 
            area.description as area_desc, 
            employee.registry_number as employee_nip,
            resource.name as resource_name, 
            employee.private_street as employee_street, 
            employee.private_street2 as employee_street2, 
            --employee.rt as rt, field tidak ada
            --employee.rw as rw, field tidak ada
            province.name as province, 
            city.name as city, 
            employee.district_id as kecamatan, 
            employee.sub_district_id as kelurahan,
            job.name->>'en_US' as job_name, 
            groups.name->>'en_US' as group_name, 
            employee.working_start_date  as tgl_masuk, 
            employee.working_end_date as tgl_keluar, 
            create_partner.name as created_by, 
            employee.create_date as created_date, 
            update_partner.name as updated_by, 
            employee.write_date as updated_date,
            users."login", 
            users.login_date, 
            users.active as login_active,
            bank.name as bank,
            emp_bank.acc_number as no_rekening,
            employee.identification_id as no_ktp,
            employee.tax_number as npwp
            FROM hr_employee employee INNER JOIN resource_resource resource ON employee.resource_id = resource.id
            LEFT JOIN res_users users ON resource.user_id = users.id
            LEFT JOIN res_company b ON employee.company_id = b.id
            LEFT JOIN res_area area ON employee.area_id = area.id
            LEFT JOIN res_country_state province ON employee.private_state_id = province.id
            LEFT JOIN res_city city ON employee.city_id = city.id
            LEFT JOIN hr_job job ON employee.job_id = job.id
            LEFT JOIN res_groups groups ON job.group_id = groups.id
            LEFT JOIN res_users create_by ON employee.create_uid = create_by.id
            LEFT JOIN res_partner create_partner ON create_by.partner_id = create_partner.id
            LEFT JOIN res_users update_by ON employee.write_uid = update_by.id
            LEFT JOIN res_partner update_partner ON update_by.partner_id = update_partner.id
            LEFT JOIN res_partner_bank emp_bank ON emp_bank.id = employee.bank_account_id 
            LEFT JOIN res_bank bank ON bank.id = emp_bank.bank_id
            WHERE employee.registry_number is not null {query_where}
            ORDER BY b.code, job.name, employee.registry_number
    
        """

        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        
        start_date,end_date = self._get_date_range()
        return self.env['web.report'].sudo().generate_report('Report Employee',ress, data_summary_header=False, start_date=start_date, end_date=end_date)

    def _get_date_range(self):
        if self.start_date:
            start_date = self.start_date.strftime('%Y-%m-%d')
        else:
            start_date = self._get_default_date().strftime('%Y-%m-%d')
        if self.end_date:
            end_date = self.end_date.strftime('%Y-%m-%d')
        else:
            end_date = self._get_default_date().strftime('%Y-%m-%d')
        return start_date,end_date