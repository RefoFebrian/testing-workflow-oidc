
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError as Warning
from datetime import date,timedelta

class TwReportSisaMarginDso(models.TransientModel):
    _name = "tw.report.sisa.margin.dso"
    _description = "Laporan Sisa Margin DSO"
    
    @api.model
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()

    def _get_default_branch(self):
        return [Command.set(self.env.user.company_ids.ids)]
    
    def _set_domain_employee_ids(self):
        return [('company_id','in',self.env.user.company_ids.ids)]

    status = fields.Selection([('all','All'),('aktif','Aktif'),('non_aktif','Non Aktif')], string='Status')
    start_date = fields.Date('Start Date',default=_get_default_date)    
    end_date = fields.Date('End Date',default=_get_default_date)
    company_ids = fields.Many2many(comodel_name='res.company', relation='tw_report_sisa_margin_dso_company_rel',column1='tw_report_sisa_margin_dso_id', column2='company_id',string="Branch")
    employee_ids = fields.Many2many('hr.employee', 'tw_report_sisa_margin_dso_employee_rel', 'tw_report_sisa_margin_dso_employee_id','employee_id', 'Sales', copy=False, domain=_set_domain_employee_ids)

    def action_excel_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        return self._download_report()

    def _download_report(self):
        company = self.company_ids or self.env.user.company_ids
        company_list = tuple(company.ids or company.search([]).ids)
        employee_list = tuple(self.employee_ids.ids or self.employee_ids.search([]).ids)
        
        query = """
                SELECT branch.code AS kode_dealer,
                    branch.name AS branch,
                    dso.name AS dso,
                    dso.state AS state,
                    emp.name AS employee,
                    emp.registry_number AS nip,
                    job.name->>'en_US' AS job_name,
                    series.name->>'en_US' AS series,
                    paytype.name AS payment_type,
                    CASE
                        WHEN job.sales_category = 'sales_koordinator'
                        THEN CASE
                             WHEN dsol.achieve_coordinator_target IS TRUE
                             THEN 'Yes'
                             ELSE 'No'
                             END
                        ELSE CASE
                             WHEN dsol.achieve_salesman_target IS TRUE
                             THEN 'Yes'
                             ELSE 'No'
                        END
                    END AS mencapai_target,
                    ROUND(COALESCE(dsol.net_margin, (dsol.gross_profit_unit + dsol.gross_profit_bbn) - dsol.commision_amount)) AS sisa_margin_actual,
                    CASE
                        WHEN job.sales_category = 'sales_koordinator' THEN (
                            CASE
                                WHEN paytype.name = 'credit'
                                THEN ROUND(COALESCE(tl_sco.credit, tl.credit))
                                ELSE ROUND(COALESCE(tl_sco.cash, tl.cash))
                            END
                        )
                        ELSE (
                            CASE
                                WHEN paytype.name = 'credit'
                                THEN ROUND(COALESCE(tl_sales.credit, tl.credit))
                                ELSE ROUND(COALESCE(tl_sales.cash, tl.cash))
                            END
                        )
                    END AS target_sisa_margin,
                    CASE
                        WHEN dso.state = 'cancel' THEN 'DSO Cancel'
                        WHEN dso.incentive_state = 'draft' THEN 'Incentive untuk DSO ini belum dihitung, menunggu sistem memproses'
                        WHEN dso.error_message IS NULL
                        AND (
                            (job.sales_category = 'sales_koordinator' AND tl_sco.id IS NULL)
                            OR
                            (job.sales_category != 'sales_koordinator' AND tl_sales.id IS NULL)
                        ) THEN 'Master margin ' || coalesce(series.name->>'en_US','') || ' tidak ditemukan'
                        ELSE dso.error_message
                    END AS error_message
                FROM (
                    SELECT e.id,
                        e.company_id,
                        e.registry_number,
                        e.name,
                        COALESCE((
                            SELECT id
                            FROM hr_job
                            WHERE id = (
                                    SELECT curr_id
                                    FROM tw_employee_career_record
                                    WHERE employee_id = e.id
                                        AND date_assign <= %(end)s
                                    ORDER BY date_assign DESC
                                    LIMIT 1
                                )
                                AND sales_category IS NOT NULL
                        ),e.job_id) AS job_id
                    FROM hr_employee AS e
                    GROUP BY e.id
                ) AS emp
                    JOIN hr_job AS job ON job.id = emp.job_id
                    JOIN res_company AS branch ON branch.id = emp.company_id
                    JOIN tw_dealer_sale_order AS dso ON (
                        CASE
                            WHEN job.sales_category = 'sales_koordinator'
                            THEN dso.sales_coordinator_id = emp.id OR dso.sales_id = emp.id
                            ELSE dso.sales_id = emp.id
                        END
                    )
                    JOIN tw_dealer_sale_order_line dsol ON dsol.order_id = dso.id and dsol.item_type = 'main'
                    JOIN product_product AS product ON product.id = dsol.product_id
                    JOIN product_template AS pt ON pt.id = product.product_tmpl_id
                    JOIN product_series AS series ON series.id = pt.series_id
                    JOIN tw_selection as paytype ON paytype.id = dso.payment_type_id
                    LEFT JOIN tw_master_target_margin_line AS tl_sales ON dsol.target_margin_sales_id  = tl_sales.id
                    LEFT JOIN tw_master_target_margin_line AS tl_sco ON dsol.target_margin_coordinator_id = tl_sco.id
                    LEFT JOIN tw_master_target_margin AS mar ON mar.id = (
                        SELECT max(id)
                        FROM tw_master_target_margin
                        WHERE 1 = 1
                            AND company_id = dso.company_id
                            AND state = 'active'
                            AND job = (
                                CASE
                                    WHEN job.sales_category = 'sales_koordinator' THEN 'sco'
                                    WHEN job.sales_category = 'sales_counter' THEN 'sc'
                                    WHEN job.sales_category IN ('sales_partner', 'sales_payroll') THEN 'sales'
                                    ELSE NULL
                                END
                            )
                    )
                    LEFT JOIN tw_master_target_margin_line AS tl ON tl.target_margin_id = mar.id AND tl."year" = dsol.production_year 
                    AND tl.series_id = pt.series_id
                WHERE 1 = 1
                AND dso.state in ('sale', 'done')
                    AND dso.date_order BETWEEN %(start)s AND %(end)s
                    AND emp.company_id IN %(company_list)s
                    AND emp.id IN %(employee_list)s
            """
        self.env.cr.execute(query, {
            'start': self.start_date,
            'end': self.end_date,
            'company_list': company_list,
            'employee_list': employee_list,
        })
        ress = self.env.cr.dictfetchall()
        if not ress:
            raise Warning("Tidak ada data.")
        
        return self.env['web.report'].generate_report('Laporan Sisa Margin (DSO)',ress)

    