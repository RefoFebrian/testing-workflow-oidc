# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date,timedelta

# 3:  imports of odoo
from odoo import models, fields, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools import SQL

# 5: local imports

# 6: Import of unknown third party lib


class TWReportNetMarginDso(models.TransientModel):
    _name = "tw.report.net.margin.dso"
    _description = "Report Net Margin DSO"
    
    def _get_default_date(self): 
        return date.today()

    def _get_default_branch(self):
        return [Command.set(self.env.user.company_ids.ids)]
    
    def _set_domain_employee_ids(self):
        return [('company_id', 'in', self.env.user.company_ids.ids)]

    file = fields.Char('File Name')
    data_x = fields.Binary('File', readonly=True)
    state_x =  fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    status = fields.Selection([('all', 'All'), ('active', 'Active'), ('non_active', 'Non Active')],  string='Status')
    start_date = fields.Date('Start Date', default=_get_default_date)    
    end_date = fields.Date('End Date', default=_get_default_date)

    company_ids = fields.Many2many(
        comodel_name='res.company', relation='tw_report_net_margin_dso_rel',
        column1='tw_report_net_margin_dso_id', column2='company_id',
        string='Branches', default=_get_default_branch
    )
    employee_ids = fields.Many2many(
        comodel_name='hr.employee', relation='tw_report_net_margin_dso_employee_rel',
        column1='tw_report_net_margin_employee_id', column2='employee_id',
        string='Sales', copy=False, domain=_set_domain_employee_ids
    )

    def excel_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        return self._download_report()

    def _download_report(self):
        company = self.company_ids or self.env.user.company_ids
        company_list = tuple(company.ids or company.search([]).ids)
        employee_list = tuple(self.employee_ids.ids or self.employee_ids.search([]).ids)
        
        query = SQL("""
                SELECT company.code AS code,
                    company.name AS branch,
                    dso.name AS dso,
                    emp.name AS employee,
                    emp.registry_number AS nip,
                    job.name->>'en_US' AS job_name,
                    series.name->>'en_US' AS series,
                    CASE
                        WHEN dso.finco_id IS NULL
                        THEN 'Cash'
                        ELSE 'Credit'
                    END AS payment_type,
                    CASE
                        WHEN job.sales_category = 'sales_coordinator'
                        THEN (
                            CASE WHEN dsol.achieve_coordinator_target IS TRUE
                            THEN 'Yes' ELSE 'No' END
                        ) ELSE (
                            CASE WHEN dsol.achieve_salesman_target IS TRUE
                            THEN 'Yes' ELSE 'No' END
                        )
                    END AS mencapai_target,
                    COALESCE(dsol.net_margin, 0) AS net_margin_actual,
                    CASE
                        WHEN job.sales_category = 'sales_coordinator' THEN (
                            CASE
                                WHEN dso.finco_id IS NOT NULL
                                THEN COALESCE(tl_sco.credit, tl.credit)
                                ELSE COALESCE(tl_sco.cash, tl.cash)
                            END
                        )
                        ELSE (
                            CASE
                                WHEN dso.finco_id IS NOT NULL
                                THEN COALESCE(tl_sales.credit, tl.credit)
                                ELSE COALESCE(tl_sales.cash, tl.cash)
                            END
                        )
                    END AS target_net_margin,
                    CASE
                        WHEN dso.incentive_state = 'draft'
                        THEN 'Incentive untuk DSO ini belum dihitung, menunggu sistem memproses'
                        WHEN dso.error_message IS NULL
                            AND (
                                (job.sales_category = 'sales_coordinator' AND tl_sco.id IS NULL)
                                OR (job.sales_category != 'sales_coordinator' AND tl_sales.id IS NULL)
                            ) THEN CONCAT('Master margin ', series.name->>'en_US', ' tidak ditemukan')
                        ELSE dso.error_message
                    END AS error_message
                FROM (
                    SELECT e.id,
                        e.company_id,
                        e.registry_number,
                        e.name,
                        (
                            SELECT id
                            FROM hr_job
                            WHERE id = (
                                SELECT jh.curr_id
                                FROM tw_employee_career_record jh
                                WHERE jh.employee_id = e.id
                                    AND model_name = 'hr.job'
                                    AND jh.date_assign <= %(end)s
                                    AND jh.type IN ('promotion', 'demotion', 'new_hire', 'contract_renewal', 'transfer', 'rotation')
                                ORDER BY id DESC
                                LIMIT 1
                            ) AND sales_category IS NOT NULL
                        ) AS job_id
                    FROM hr_employee AS e
                    GROUP BY e.id
                ) AS emp
                    JOIN hr_job AS job ON job.id = emp.job_id
                    JOIN res_company AS company ON company.id = emp.company_id
                    JOIN tw_dealer_sale_order AS dso ON (
                        CASE
                            WHEN job.sales_category = 'sales_coordinator'
                            THEN dso.sales_coordinator_id = emp.id OR dso.sales_id = emp.id
                            ELSE dso.sales_id = emp.id
                        END
                    ) JOIN tw_dealer_sale_order_line dsol ON dsol.order_id = dso.id
                    JOIN product_product AS product ON product.id = dsol.product_id
                    JOIN product_template AS pt ON pt.id = product.product_tmpl_id
                    JOIN product_series AS series ON series.id = pt.series_id
                    LEFT JOIN tw_master_target_margin_line AS tl_sales ON dsol.target_margin_sales_id = tl_sales.id
                    LEFT JOIN tw_master_target_margin_line AS tl_sco ON dsol.target_margin_coordinator_id = tl_sco.id --FOR OLD Transaction
                    LEFT JOIN tw_master_target_margin AS mar ON mar.id = (
                        SELECT max(id)
                        FROM tw_master_target_margin
                        WHERE 1 = 1
                            AND company_id = dso.company_id
                            AND state = 'active'
                            AND job = (
                                CASE
                                    WHEN job.sales_category = 'sales_coordinator' THEN 'sco'
                                    WHEN job.sales_category = 'sales_counter' THEN 'sc'
                                    WHEN job.sales_category IN ('sales_partner', 'sales_payroll') THEN 'sales'
                                    ELSE NULL
                                END
                            )
                    )
                    LEFT JOIN tw_master_target_margin_line AS tl ON tl.target_margin_id = mar.id
                    AND tl.series_id = pt.series_id
                WHERE 1 = 1
                    AND dso.date_order BETWEEN %(start)s AND %(end)s
                    AND emp.company_id IN %(company_list)s
                    AND emp.id IN %(employee_list)s
            """, start=self.start_date, end=self.end_date, company_list=company_list, employee_list=employee_list)
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        if not ress:
            raise Warning(_("No data found for the selected criteria."))

        return self.env['web.report'].generate_report('Report Net Margin (DSO)', ress)

    


