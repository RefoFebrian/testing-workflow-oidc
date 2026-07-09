# -*- coding: utf-8 -*-

# 1: imports of python lib
import base64
import xlsxwriter

# 2: import of known third party lib
from datetime import date,timedelta
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from io import BytesIO

# 3:  imports of odoo
from odoo import models, fields, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools import SQL

# 5: local imports

# 6: Import of unknown third party lib



class TWReportIncentive(models.TransientModel):
    _name = "tw.report.incentive"
    _rec_name = "file"
    _description = "Report Incentive"
    
    def _get_default_date(self):
        return date.today()
    
    def _get_default_branch(self):
        return [Command.set(self.env.user.company_ids.ids)]
    
    file = fields.Char(string='File Name')
    data_x = fields.Binary(string='File', readonly=True)
    status = fields.Selection(selection=[('all', 'All'), ('active', 'Active'), ('non_active', 'Non active')], default='all', string='Status')
    type = fields.Selection(selection=[('detail', 'Detail'), ('summary', 'Summary')], default='summary')
    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)
    
    company_ids = fields.Many2many(
        comodel_name='res.company', relation='tw_report_incentive_company_rel',
        column1='tw_report_employee_id', column2='company_id',
        string='Companies', default=_get_default_branch)
    job_ids = fields.Many2many(
        comodel_name='hr.job', relation='tw_report_incentive_job_rel',
        column1='tw_report_employee_job_id', column2='job_id',
        string='Job Title', copy=False)

    wbf = {}
    
    def excel_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        if self.type == 'summary':
            return self._download_report_summary()
        elif self.type == 'detail':
            return self._download_report_detail()

    def _download_report_summary(self):
        first_day_next_month = self.start_date + relativedelta(months=1) + relativedelta(day=1)
        last_day_next_month = self.end_date + relativedelta(months=2) + relativedelta(day=1) - relativedelta(days=1)

        company = self.company_ids or self.env.user.company_ids
        company_list = tuple([b.id for b in company])

        query = SQL("""
                SELECT 
                company.name AS dealer,
                company.code AS kode_dealer,
                emp.registry_number nik,
                emp.name AS nama,
                initcap(replace(COALESCE(job.sales_category, job.name->>'en_US'), '_', ' ')) AS job,
                (
                    SELECT ROUND(COALESCE(SUM(inc.incentive_value), 0))
                    FROM tw_employee_incentive AS inc
                    WHERE inc.employee_id = emp.id
                        AND inc.transaction_ref IN (
                            SELECT DISTINCT name
                            FROM tw_dealer_sale_order
                            WHERE (
                                    CASE
                                        WHEN sales_category = 'sales_coordinator'
                                        THEN sales_coordinator_id = emp.id
                                        ELSE sales_id = emp.id
                                    END
                                )
                                AND date_order BETWEEN %(start_date)s AND %(end_date)s
                        )
                        AND inc.state in ('earned','pending')
                        AND inc.model_name = 'tw.dealer.sale.order'
                ) AS incentive_final,
                (
                    SELECT ROUND(COALESCE(SUM(inc.incentive_value), 0))
                    FROM tw_employee_incentive AS inc
                    WHERE inc.employee_id = emp.id
                        AND inc.transaction_ref IN (
                            SELECT DISTINCT name
                            FROM tw_dealer_sale_order
                            WHERE (
                                    CASE
                                        WHEN sales_category = 'sales_coordinator'
                                        THEN sales_coordinator_id = emp.id
                                        ELSE sales_id = emp.id
                                    END
                                )
                                AND date_order BETWEEN %(start_date)s AND %(end_date)s
                        )
                        AND inc.state = 'earned'
                        AND inc.model_name = 'tw.dealer.sale.order'
                ) AS "Incentive (AR Lunas)",
                (
                    SELECT ROUND(COALESCE(SUM(incentive_value), 0))
                    FROM tw_employee_incentive
                    WHERE model_name = 'tw.sp.digital'
                        AND date BETWEEN %(nomonth)s AND %(nolmonth)s
                        AND employee_id = emp.id
                ) AS "Incentive (SP / Other)",
                (
                    SELECT ROUND(COALESCE(SUM(inc.incentive_value), 0))
                    FROM tw_employee_incentive AS inc
                    WHERE inc.employee_id = emp.id
                        AND inc.transaction_ref IN (
                            SELECT DISTINCT name
                            FROM tw_dealer_sale_order
                            WHERE (
                                    CASE
                                        WHEN sales_category = 'sales_coordinator'
                                        THEN sales_coordinator_id = emp.id
                                        ELSE sales_id = emp.id
                                    END
                                )
                                AND date_order BETWEEN %(start_date)s AND %(end_date)s
                        )
                        AND inc.state = 'pending'
                        AND inc.model_name = 'tw.dealer.sale.order'
                ) AS "Incentive (Pending)",
                COUNT(DISTINCT dsol.id) AS total_unit,
                COUNT(DISTINCT dsol.id) FILTER(WHERE dso.finco_id IS NULL) AS cash,
                COUNT(DISTINCT dsol.id) FILTER(WHERE dso.finco_id IS NOT NULL) AS credit,
                CASE
                    WHEN job.sales_category = 'sales_coordinator'
                    THEN COUNT(DISTINCT dsol.id) FILTER(
                        WHERE dsol.achieve_coordinator_target IS NOT TRUE
                            AND dso.finco_id IS NULL
                    )
                    ELSE COUNT(DISTINCT dsol.id) FILTER(
                        WHERE dsol.achieve_salesman_target IS NOT TRUE
                            AND dso.finco_id IS NULL
                    )
                END AS "Sisa Margin (Cash)",
                CASE
                    WHEN job.sales_category = 'sales_coordinator'
                    THEN COUNT(DISTINCT dsol.id) FILTER(
                        WHERE dsol.achieve_coordinator_target IS NOT TRUE
                            AND dso.finco_id IS NOT NULL
                    )
                    ELSE COUNT(DISTINCT dsol.id) FILTER(
                        WHERE dsol.achieve_salesman_target IS NOT TRUE
                            AND dso.finco_id IS NOT NULL
                    )
                END AS "Sisa Margin (Credit)",
                COALESCE((
                    SELECT value
                    FROM tw_employee_incentive_detail
                    WHERE employee_incentive_id = MAX(inc.id) AND name = 'Subordinates'
                ), 0) AS "Bawahan",
                COALESCE((
                    SELECT value
                    FROM tw_employee_incentive_detail
                    WHERE employee_incentive_id = MAX(inc.id) AND name = 'Productivity'
                ), 0) AS "Produktifitas",
                COALESCE(max(inc.remarks), ' ') AS remark,
                COUNT(DISTINCT dsol.id) FILTER(WHERE dsol.incentive_state = 'error') AS error
            FROM hr_employee AS emp
                LEFT JOIN LATERAL (
                    SELECT jh.curr_id AS job_id,
                        jh.employee_id
                    FROM tw_employee_career_record jh
                    WHERE jh.employee_id = emp.id
                        AND model_name = 'hr.job'
                        AND jh.date_assign < %(end_date)s
                        AND jh.type IN ('promotion', 'demotion', 'new_hire', 'contract_renewal', 'transfer', 'rotation')
                    ORDER BY id DESC
                    LIMIT 1
                ) AS jh ON jh.employee_id = emp.id
                LEFT JOIN hr_job job ON job.id = jh.job_id
                LEFT JOIN res_company AS company ON company.id = emp.company_id
                LEFT JOIN tw_dealer_sale_order AS dso ON (
                    CASE
                        WHEN job.sales_category = 'sales_coordinator' THEN dso.sales_coordinator_id = emp.id
                        OR dso.sales_id = emp.id
                        ELSE dso.sales_id = emp.id
                    END
                )
                LEFT JOIN tw_employee_incentive AS inc ON inc.employee_id = emp.id and inc.transaction_ref = dso.name
                LEFT JOIN tw_dealer_sale_order_line dsol ON dsol.order_id = dso.id and dsol.item_type = 'main'
            WHERE emp.company_id IN %(company_ids)s
                AND dso.date_order BETWEEN %(start_date)s AND %(end_date)s
                AND dso.state in ('sale', 'done')
            GROUP BY company.id, emp.id, job.id     
            """, start_date=self.start_date, end_date=self.end_date, nomonth=first_day_next_month, nolmonth=last_day_next_month, company_ids=company_list)
        
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        if not ress:
            raise Warning(_("No data found for the selected criteria."))
        return self.env['web.report'].sudo().generate_report('Report Incentive Detail', ress, start_date=self.start_date, end_date=self.end_date)
    
    def _download_report_detail(self):
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)       
        workbook = self.add_workbook_format(workbook)
        wbf = self.wbf
        worksheet = workbook.add_worksheet('Report Incentive Detail')

        worksheet.set_column('B1:B1', 20)
        worksheet.set_column('C1:C1', 8)
        worksheet.set_column('D1:D1', 20)
        worksheet.set_column('E1:E1', 30)
        worksheet.set_column('F1:F1', 20)
        worksheet.set_column('G1:G1', 25)
        worksheet.set_column('H1:H1', 25)
        worksheet.set_column('I1:I1', 25)
        worksheet.set_column('J1:J1', 25)
        worksheet.set_column('K1:K1', 25)
        worksheet.set_column('L1:L1', 25)
        worksheet.set_column('M1:M1', 25)
        worksheet.set_column('N1:N1', 25)
        worksheet.set_column('O1:O1', 8)
        worksheet.set_column('P1:P1', 8)
        worksheet.set_column('Q1:Q1', 8)
        worksheet.set_column('R1:R1', 8)
        worksheet.set_column('S1:S1', 8)
        worksheet.set_column('T1:T1', 8)
        worksheet.set_column('U1:U1', 8)
        worksheet.set_column('V1:V1', 25)
        worksheet.set_column('W1:W1', 25)
        worksheet.set_column('X1:X1', 25)
        worksheet.set_column('Y1:Y1', 150)
        worksheet.set_column('Z1:Z1', 20)
        
        user_id = self.env['res.users'].search([('id','=',self._uid)])
        user = user_id.name 
        company = user_id.company_id.name
        filename = 'Report Incentive Detail' + str(self.start_date)+'.xlsx'

        start_date = self.start_date - relativedelta(months=1)
        end_date = self.end_date
        next_start = self.start_date + relativedelta(months=1)
        next_end = self.end_date + relativedelta(months=1)
        company_ids = tuple(self.company_ids.ids)
        if not self.company_ids:
            company_ids = tuple(self.env['res.company'].search([]).ids)

        self._cr.execute(SQL("""
            SELECT *,
                (
                    SELECT COALESCE(SUM(incentive_value), 0)
                    FROM tw_employee_incentive
                    WHERE model_name = 'tw.sp.digital'
                        AND date BETWEEN %(next_start)s AND %(next_end)s
                        AND employee_id = dt.employee_id
                ) AS other,
                COALESCE((
                    SELECT value FROM tw_employee_incentive_detail
                    WHERE employee_incentive_id = incentive_id
                    AND name = 'Subordinates'
                ), 0) AS subordinate,
                COALESCE((
                    SELECT value FROM tw_employee_incentive_detail
                    WHERE employee_incentive_id = incentive_id
                    AND name = 'Productivity'
                ), 0) AS productivity
            FROM (
                    (
                        SELECT b.code AS branch_code,
                            b.name AS branch_name,
                            b.branch_class AS branch_category,
                            emp.id AS employee_id,
                            emp.registry_number AS employee_registry_number,
                            emp.name AS employee_name,
                            job.name->>'en_US' AS job_name,
                            job.sales_category,
                            COALESCE(SUM(i.incentive_value) FILTER (WHERE i.state = 'earned' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS earned,
                            COALESCE(SUM(i.incentive_value) FILTER (WHERE i.state = 'earned' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(lmonth)s), 0) AS lm_earned,
                            COALESCE(SUM(i.incentive_value) FILTER (WHERE i.state = 'pending' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS pending,
                            COALESCE(SUM(i.incentive_value) FILTER (WHERE i.state = 'cancelled' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS cancel,
                            COALESCE(SUM(i.incentive_value) FILTER (WHERE i.state = 'cancelled' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(lmonth)s), 0) AS lm_cancel,
                            COALESCE(MAX(i.incentive_sales) FILTER (WHERE i.state = 'earned' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS incentive_sales,
                            COALESCE(MAX(i.incentive_credit) FILTER (WHERE i.state = 'earned' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS incentive_credit,
                            COALESCE(MAX(i.incentive_reward) FILTER (WHERE i.state = 'earned' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS incentive_reward,
                            COALESCE(COUNT(dsol.id) FILTER (WHERE TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS sales,
                            COALESCE(COUNT(dsol.id) FILTER (WHERE dso.finco_id IS NULL AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS cash,
                            COALESCE(COUNT(dsol.id) FILTER (WHERE dso.finco_id IS NOT NULL AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS credit,
                            COUNT(DISTINCT dsol.id) FILTER(WHERE dsol.incentive_state = 'error' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s) AS error,
                            CASE
                                WHEN job.sales_category = 'sales_coordinator'
                                THEN COUNT(DISTINCT dsol.id) FILTER(WHERE dsol.achieve_coordinator_target IS NOT TRUE AND dso.finco_id IS NULL AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s)
                                ELSE COUNT(DISTINCT dsol.id) FILTER(WHERE dsol.achieve_salesman_target IS NOT TRUE AND dso.finco_id IS NULL AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s)
                            END AS mediator_cash,
                            CASE
                                WHEN job.sales_category = 'sales_coordinator'
                                THEN COUNT(DISTINCT dsol.id) FILTER(WHERE dsol.achieve_coordinator_target IS NOT TRUE AND dso.finco_id IS NOT NULL AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s)
                                ELSE COUNT(DISTINCT dsol.id) FILTER(WHERE dsol.achieve_salesman_target IS NOT TRUE AND dso.finco_id IS NOT NULL AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s)
                            END AS mediator_credit,
                            MAX(i.id) filter (where i.state in ('pending', 'earned')) as incentive_id
                        FROM tw_dealer_sale_order AS dso
                            LEFT JOIN tw_dealer_sale_order_line AS dsol ON dso.id = dsol.order_id
                            LEFT JOIN hr_employee AS emp ON emp.id = dso.sales_coordinator_id
                            LEFT JOIN tw_employee_incentive AS i ON i.employee_id = dso.sales_coordinator_id AND i.transaction_ref = dso.name
                            LEFT JOIN res_company AS b ON b.id = i.company_id
                            LEFT JOIN hr_job AS job ON job.id = i.job_id
                        WHERE dso.date_order BETWEEN %(start)s AND %(end)s
                            AND dso.company_id IN %(company_ids)s
                            AND job.sales_category = 'sales_coordinator'
                        GROUP BY b.id, emp.id, job.id
                    )
                    UNION
                    (
                        SELECT b.code AS branch_code,
                            b.name AS branch_name,
                            b.branch_class AS branch_category,
                            emp.id AS employee_id,
                            emp.registry_number AS employee_registry_number,
                            emp.name AS employee_name,
                            job.name->>'en_US' AS job_name,
                            job.sales_category,
                            COALESCE(SUM(i.incentive_value) FILTER (WHERE i.state = 'earned' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS earned,
                            COALESCE(SUM(i.incentive_value) FILTER (WHERE i.state = 'earned' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(lmonth)s), 0) AS lm_earned,
                            COALESCE(SUM(i.incentive_value) FILTER (WHERE i.state = 'pending' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS pending,
                            COALESCE(SUM(i.incentive_value) FILTER (WHERE i.state = 'cancelled' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS cancel,
                            COALESCE(SUM(i.incentive_value) FILTER (WHERE i.state = 'cancelled' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(lmonth)s), 0) AS lm_cancel,
                            COALESCE(MAX(i.incentive_sales) FILTER (WHERE i.state = 'earned' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS incentive_sales,
                            COALESCE(MAX(i.incentive_credit) FILTER (WHERE i.state = 'earned' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS incentive_credit,
                            COALESCE(MAX(i.incentive_reward) FILTER (WHERE i.state = 'earned' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS incentive_reward,
                            COALESCE(COUNT(dso.id) FILTER (WHERE TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS sales,
                            COALESCE(COUNT(dso.id) FILTER (WHERE dso.finco_id IS NULL AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS cash,
                            COALESCE(COUNT(dso.id) FILTER (WHERE dso.finco_id IS NOT NULL AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s), 0) AS credit,
                            COUNT(DISTINCT dsol.id) FILTER(WHERE dsol.incentive_state = 'error' AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s) AS error,
                            CASE
                                WHEN job.sales_category = 'sales_coordinator'
                                THEN COUNT(DISTINCT dsol.id) FILTER(WHERE dsol.achieve_coordinator_target IS NOT TRUE AND dso.finco_id IS NULL AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s)
                                ELSE COUNT(DISTINCT dsol.id) FILTER(WHERE dsol.achieve_salesman_target IS NOT TRUE AND dso.finco_id IS NULL AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s)
                            END AS mediator_cash,
                            CASE
                                WHEN job.sales_category = 'sales_coordinator'
                                THEN COUNT(DISTINCT dsol.id) FILTER(WHERE dsol.achieve_coordinator_target IS NOT TRUE AND dso.finco_id IS NOT NULL AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s)
                                ELSE COUNT(DISTINCT dsol.id) FILTER(WHERE dsol.achieve_salesman_target IS NOT TRUE AND dso.finco_id IS NOT NULL AND TO_CHAR(dso.date_order, 'YYYY/MM') = %(month)s)
                            END AS mediator_credit,
                            MAX(i.id) filter (where i.state in ('pending', 'earned')) as incentive_id
                        FROM tw_dealer_sale_order AS dso
                            LEFT JOIN tw_dealer_sale_order_line AS dsol ON dso.id = dsol.order_id and dsol.item_type = 'main'
                            LEFT JOIN hr_employee AS emp ON emp.id = dso.sales_id
                            LEFT JOIN tw_employee_incentive AS i ON i.employee_id = dso.sales_id AND i.transaction_ref = dso.name
                            LEFT JOIN res_company AS b ON b.id = i.company_id
                            LEFT JOIN hr_job AS job ON job.id = i.job_id
                        WHERE dso.date_order BETWEEN %(start)s AND %(end)s
                            AND dso.company_id IN %(company_ids)s
                            AND job.sales_category NOT IN ('sales_coordinator', 'sales_team_leader')
                        GROUP BY b.id, emp.id, job.id
                    )
                ) dt
            -- WHERE dt.remark IS NOT NULL
        """, start=start_date, end=end_date, company_ids=company_ids,
        next_start=next_start, next_end=next_end,
        month=self.end_date.strftime('%Y/%m'), lmonth=(self.end_date - relativedelta(months=1)).strftime('%Y/%m')))
        
        ress = self._cr.dictfetchall()
        if not ress:
            raise Warning("Tidak ada data.")
        
        worksheet.merge_range('A1:B1', company , wbf['company'])
        worksheet.merge_range('A2:B2', 'Report Incentive Detail' , wbf['company'])
        
        row = 5

        worksheet.merge_range(f'A{row}:A{row+1}', 'No' , wbf['header_left'])
        worksheet.merge_range(f'B{row}:B{row+1}', 'Dealer' , wbf['header'])
        worksheet.merge_range(f'C{row}:C{row+1}', 'Kode Dealer' , wbf['header'])
        worksheet.merge_range(f'D{row}:D{row+1}', 'Nik' , wbf['header'])
        worksheet.merge_range(f'E{row}:E{row+1}', 'Nama' , wbf['header'])
        worksheet.merge_range(f'F{row}:F{row+1}', 'Job' , wbf['header'])
        worksheet.merge_range(f'G{row}:G{row+1}', 'Sales Category' , wbf['header'])

        worksheet.merge_range(f'H{row}:K{row}', 'Incentive', wbf['header'])
        worksheet.write('H%s' % (row+1), 'Final' , wbf['header'])
        worksheet.write('I%s' % (row+1), 'AR Lunas' , wbf['header'])
        worksheet.write('J%s' % (row+1), 'SP / Other' , wbf['header'])
        worksheet.write('K%s' % (row+1), 'Pending' , wbf['header'])
        
        worksheet.merge_range(f'L{row}:N{row}', 'Incentive Diff', wbf['header'])
        worksheet.write('L%s' % (row+1), 'Earned M-1' , wbf['header'])
        worksheet.write('M%s' % (row+1), 'Cancelled M-1' , wbf['header'])
        worksheet.write('N%s' % (row+1), 'Diff' , wbf['header'])
        
        worksheet.merge_range(f'O{row}:U{row}', 'Sales Info', wbf['header'])
        worksheet.write('O%s' % (row+1), 'Total Unit' , wbf['header'])
        worksheet.write('P%s' % (row+1), 'Cash' , wbf['header'])
        worksheet.write('Q%s' % (row+1), 'Credit' , wbf['header'])
        worksheet.write('R%s' % (row+1), 'Sisa Margin (Cash)' , wbf['header'])
        worksheet.write('S%s' % (row+1), 'Sisa Margin (Credit)' , wbf['header'])
        worksheet.write('T%s' % (row+1), 'Bawahan' , wbf['header'])
        worksheet.write('U%s' % (row+1), 'Produktifitas' , wbf['header'])
        
        worksheet.merge_range(f'V{row}:X{row}', 'Incentive Detail', wbf['header'])
        worksheet.write('V%s' % (row+1), 'Sales' , wbf['header'])
        worksheet.write('W%s' % (row+1), 'Credit' , wbf['header'])
        worksheet.write('X%s' % (row+1), 'Reward' , wbf['header'])
        
        worksheet.merge_range(f'Y{row}:Y{row+1}', 'Remark' , wbf['header'])
        worksheet.merge_range(f'Z{row}:Z{row+1}', 'Error' , wbf['header'])

        row += 2       
        no = 1
       
        if ress == []:
            worksheet.merge_range('A%s:H%s' % (row,row), 'Data tidak ada !' , wbf['content'])
            
        for res in ress:
            branch = res.get('branch_name')
            branch_code = res.get('branch_code')
            registry_number = res.get('employee_registry_number')
            employee = res.get('employee_name')
            job_name = res.get('job_name')
            sales_category = res['sales_category'].replace('_',' ').title() if res.get('sales_category') else ''
            incentive_earned = res.get('earned', 0.00)
            incentive_pending = res.get('pending', 0.00)
            incentive_other = res.get('other', 0.00)
            incentive_earned_lm = res.get('lm_earned', 0.00)
            incentive_cancelled_lm = res.get('lm_cancel', 0.00)
            incentive_diff = incentive_earned_lm - incentive_cancelled_lm
            incentive = incentive_earned + incentive_other
            dsol = res.get('sales', 0)
            cash = res.get('cash', 0)
            credit = res.get('credit', 0)
            error = res.get('error', 0)
            mediator_cash = res.get('mediator_cash')
            mediator_credit = res.get('mediator_credit')
            subordinate = res.get('subordinate')
            productivity = res.get('productivity')
            remark = res.get('remark')
            incentive_sales = res.get('incentive_sales', 0)
            incentive_credit = res.get('incentive_credit', 0)
            incentive_reward = res.get('incentive_reward', 0)

            worksheet.write('A%s' % row, no , wbf['content_left']) 
            worksheet.write('B%s' % row, branch , wbf['content']) 
            worksheet.write('C%s' % row, branch_code , wbf['content'])
            worksheet.write('D%s' % row, registry_number , wbf['content'])
            worksheet.write('E%s' % row, employee, wbf['content'])
            worksheet.write('F%s' % row, job_name, wbf['content'])
            worksheet.write('G%s' % row, sales_category, wbf['content'])
            worksheet.write('H%s' % row, incentive, wbf['content_float'])
            worksheet.write('I%s' % row, incentive_earned, wbf['content_float'])
            worksheet.write('J%s' % row, incentive_other, wbf['content_float'])
            worksheet.write('K%s' % row, incentive_pending, wbf['content_float'])
            worksheet.write('L%s' % row, incentive_earned_lm, wbf['content_float'])
            worksheet.write('M%s' % row, incentive_cancelled_lm, wbf['content_float'])
            worksheet.write('N%s' % row, incentive_diff, wbf['content_float'])
            worksheet.write('O%s' % row, dsol , wbf['content_int'])
            worksheet.write('P%s' % row, cash , wbf['content_int'])
            worksheet.write('Q%s' % row, credit , wbf['content_int'])
            worksheet.write('R%s' % row, mediator_cash , wbf['content_int'])
            worksheet.write('S%s' % row, mediator_credit , wbf['content_int'])
            worksheet.write('T%s' % row, subordinate , wbf['content_int'])
            worksheet.write('U%s' % row, productivity , wbf['content_int'])
            worksheet.write('V%s' % row, incentive_sales , wbf['content_float'])
            worksheet.write('W%s' % row, incentive_credit , wbf['content_float'])
            worksheet.write('X%s' % row, incentive_reward , wbf['content_float'])
            worksheet.write('Y%s' % row, remark , wbf['content'])
            worksheet.write('Z%s' % row, error , wbf['content'])

            no += 1 
            row += 1     

        worksheet.autofilter('A6:W%s' % (row)) 
        worksheet.freeze_panes(6, 1)
        worksheet.merge_range('A%s:B%s'%(row+2,row+2), '%s %s' % ((str(self.start_date)+'-'+str(self.start_date)),user) , wbf['footer']) 
        
        workbook.close()
        out=base64.encodebytes(fp.getvalue())
        self.data_x = out
        self.file = filename
        
        fp.close()
        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': '/web/content/tw.report.incentive/%s/data_x/%s?download=true' % (self.id, filename)
        }
    

    def add_workbook_format(self, workbook):
        self.wbf['company'] = workbook.add_format({'bold':1,'align': 'left','font_color':'#000000','num_format': 'dd-mm-yyyy'})
        self.wbf['company'].set_font_size(12)

        self.wbf['footer'] = workbook.add_format({'align':'left'})

        self.wbf['header'] = workbook.add_format({'bg_color':'#FFFF00','bold': 1,'align': 'center','font_color': '#000000', 'valign': 'center'})
        self.wbf['header'].set_top(2)
        self.wbf['header'].set_bottom()
        self.wbf['header'].set_left()
        self.wbf['header'].set_right()
        self.wbf['header'].set_font_size(11)
        self.wbf['header'].set_align('vcenter')

        self.wbf['header_left'] = workbook.add_format({'bg_color':'#FFFF00','bold': 1,'align': 'center','font_color': '#000000'})
        self.wbf['header_left'].set_top(2)
        self.wbf['header_left'].set_bottom()
        self.wbf['header_left'].set_left(2)
        self.wbf['header_left'].set_right()
        self.wbf['header_left'].set_font_size(11)
        self.wbf['header_left'].set_align('vcenter')
        
        self.wbf['header_right'] = workbook.add_format({'bg_color':'#FFFF00','bold': 1,'align': 'center','font_color': '#000000'})
        self.wbf['header_right'].set_top(2)
        self.wbf['header_right'].set_bottom()
        self.wbf['header_right'].set_left()
        self.wbf['header_right'].set_right(2)
        self.wbf['header_right'].set_font_size(11)
        self.wbf['header_right'].set_align('vcenter')


        self.wbf['content'] = workbook.add_format({'align': 'left','font_color': '#000000'})
        self.wbf['content'].set_left()
        self.wbf['content'].set_right()
        self.wbf['content'].set_top()
        self.wbf['content'].set_bottom()
        self.wbf['content'].set_font_size(10)                

        self.wbf['content_float'] = workbook.add_format({'align': 'right','num_format': '#,##0'})
        self.wbf['content_float'].set_right() 
        self.wbf['content_float'].set_left()
        self.wbf['content_float'].set_top()
        self.wbf['content_float'].set_bottom()
        self.wbf['content_float'].set_font_size(10)     
        
        self.wbf['content_int'] = workbook.add_format({'align': 'right','num_format': '#'})
        self.wbf['content_int'].set_right() 
        self.wbf['content_int'].set_left()
        self.wbf['content_int'].set_top()
        self.wbf['content_int'].set_bottom()
        self.wbf['content_int'].set_font_size(10)     

        self.wbf['content_bg'] = workbook.add_format({'bg_color': '#81DAF5','align': 'center','font_color': '#000000'})
        self.wbf['content_bg'].set_left()
        self.wbf['content_bg'].set_right()
        self.wbf['content_bg'].set_top()
        self.wbf['content_bg'].set_bottom()
        self.wbf['content_bg'].set_font_size(10)                
      
        self.wbf['content_center'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_center'].set_left()
        self.wbf['content_center'].set_right()
        self.wbf['content_center'].set_top()
        self.wbf['content_center'].set_bottom()
        self.wbf['content_center'].set_font_size(10)
        
        self.wbf['content_left'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_left'].set_left(2)
        self.wbf['content_left'].set_right()
        self.wbf['content_left'].set_top()
        self.wbf['content_left'].set_bottom()
        self.wbf['content_left'].set_font_size(10)
        
        self.wbf['content_right'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_right'].set_left()
        self.wbf['content_right'].set_right(2)
        self.wbf['content_right'].set_top()
        self.wbf['content_right'].set_bottom()
        self.wbf['content_right'].set_font_size(10)

        self.wbf['content_bottom'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_bottom'].set_left()
        self.wbf['content_bottom'].set_right()
        self.wbf['content_bottom'].set_top()
        self.wbf['content_bottom'].set_bottom(2)
        self.wbf['content_bottom'].set_font_size(10)

        self.wbf['content_left_bottom'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_left_bottom'].set_left(2)
        self.wbf['content_left_bottom'].set_right()
        self.wbf['content_left_bottom'].set_top()
        self.wbf['content_left_bottom'].set_bottom(2)
        self.wbf['content_left_bottom'].set_font_size(10)
        
        self.wbf['content_right_bottom'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_right_bottom'].set_left()
        self.wbf['content_right_bottom'].set_right(2)
        self.wbf['content_right_bottom'].set_top()
        self.wbf['content_right_bottom'].set_bottom(2)
        self.wbf['content_right_bottom'].set_font_size(10)

        self.wbf['content_center_bg'] = workbook.add_format({'bg_color':'#85C1E9', 'align': 'center','font_color': '#000000'})
        self.wbf['content_center_bg'].set_left()
        self.wbf['content_center_bg'].set_right()
        self.wbf['content_center_bg'].set_top()
        self.wbf['content_center_bg'].set_bottom()
        self.wbf['content_center_bg'].set_font_size(10)                
        
        self.wbf['content_center_bg_bottom'] = workbook.add_format({'bg_color':'#85C1E9', 'align': 'center','font_color': '#000000'})
        self.wbf['content_center_bg_bottom'].set_left()
        self.wbf['content_center_bg_bottom'].set_right()
        self.wbf['content_center_bg_bottom'].set_top()
        self.wbf['content_center_bg_bottom'].set_bottom(2)
        self.wbf['content_center_bg_bottom'].set_font_size(10)                
        
        return workbook   

    