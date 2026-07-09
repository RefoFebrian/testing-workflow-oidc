# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from datetime import datetime, timedelta

class TWReportLogin(models.TransientModel):
    _name = "tw.report.login"
    _description = "TW Report Login"
        
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()
    
    name = fields.Char(string="Filename", readonly=True)
    file = fields.Binary(string="File", readonly=True)
    company_id = fields.Many2one('res.company', string="Branch", required=True,default=lambda self: self.env.company)
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    resource_ids = fields.Many2many('hr.employee', string='Employee')

    def action_generate_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query_where = "WHERE 1=1"
        if self.company_id:
            query_where += " AND hr_sales.company_id = '%s' " % self.company_id.id
        if self.start_date:
            query_where += " AND users.login_date >= '%s' " % self.start_date
        if self.end_date:
            query_where +=  " AND users.login_date <= '%s' " % self.end_date
        if self.resource_ids:
            if len(self.resource_ids) == 1:
                query_where += " AND hr_sales.resource_id = %s " % self.resource_ids.id
            else:
                query_where += " AND hr_sales.resource_id IN %s " % str(tuple(self.resource_ids.ids))

        summary_header = self._get_summary_header_data()

        query="""
                SELECT 
                    branch.name as branch,
                    users.login as login,
                    hr_sales.name as nama, 
                    COALESCE(job.name ->>'id_ID', job.name ->>'en_US', '') as job,
                    rd.first_activity as date
                FROM res_device as rd
                    INNER JOIN res_users users ON rd.user_id = users.id
                    LEFT JOIN resource_resource sales ON users.id = sales.user_id 
                    LEFT JOIN hr_employee hr_sales ON sales.id = hr_sales.resource_id
                    LEFT JOIN res_company as branch ON branch.id=hr_sales.company_id
                    LEFT JOIN hr_job job ON hr_sales.job_id = job.id
                %s
            """ %(query_where)

        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        if not ress:
            raise Warning('Data tidak ada...')
        report_name = f"Laporan Login"
        return self.env['web.report'].sudo().generate_report(report_name, ress,show_total_footer=False,data_summary_header=summary_header,data_summary_header_col_size=False, freeze_panes_column=3)

    def _get_summary_header_data(self):
        company_name = self.company_id.name
        return {
            "A3": company_name,
            "A4": "Tanggal : %s s/d %s" % (self.start_date if self.start_date else '-', self.end_date if self.end_date else '-'),
        }