# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from collections import OrderedDict
from datetime import date,timedelta
from itertools import groupby

# 3:  imports of odoo
from odoo import models, fields, _, Command

# 4:  imports from odoo modules
from odoo.tools import SQL
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TWReportTeamLeader(models.TransientModel):
    _name = "tw.report.team.leader"
    _description = "Report Team Leader"

    def _get_default_date(self): 
        return date.today()

    def _get_default_branch(self):
        return [Command.set(self.env.user.company_ids.ids)]
    
    def _set_domain_employee_ids(self):
        return [('company_id', 'in', self.env.user.company_ids.ids)]
    
    file = fields.Char(string='File Name')
    start_date = fields.Date(string='Start Date', default=_get_default_date)
    end_date = fields.Date(string='End Date', default=_get_default_date)
    report_type = fields.Selection([('detail', 'Detail'), ('summary', 'Summary')], default='detail', string='Type')
    
    company_ids = fields.Many2many(
        comodel_name='res.company', relation='tw_report_team_leader_company_rel',
        column1='team_leader_id', column2='company_id',
        string='Branches', default=_get_default_branch
    )

    def excel_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        return self._download_report()

    def _download_report(self):
        company = self.company_ids.ids or self.env.user.company_ids.ids
        company_list = tuple(company)

        start_date = self.start_date.isoformat()
        end_date = self.end_date.isoformat()
        
        self._cr.execute(SQL("""
            SELECT COALESCE(sales.company_name, leads.company_name) AS company_name,
                COALESCE(sales.company_code, leads.company_code) AS company_code,
                COALESCE(sales.team_leader_name, leads.team_leader_name) AS team_leader_name,
                COALESCE(sales.team_leader_nip, leads.team_leader_nip) AS team_leader_nip,
                COALESCE(sales.salesman_name, leads.salesman_name) AS salesman_name,
                COALESCE(sales.salesman_nip, leads.salesman_nip) AS salesman_nip,
                COALESCE(leads.cold, 0) AS cold,
                COALESCE(leads.hot, 0) AS hot,
                COALESCE(sales.deal, 0) AS deal,
                TO_CHAR(COALESCE(sales.joined, leads.joined), 'YYYY/MM/DD') AS joined,
                COALESCE(sales.yos, leads.yos) AS yos,
                CASE
                    WHEN COALESCE(sales.yos, leads.yos) <= 1 AND COALESCE(leads.cold, 0) >= 125 THEN 100000
                    WHEN COALESCE(sales.yos, leads.yos) <= 2 AND COALESCE(leads.cold, 0) >= 125 AND COALESCE(leads.hot, 0) >= 25 AND COALESCE(sales.deal, 0) >= 2 THEN 100000
                    WHEN COALESCE(sales.yos, leads.yos) <= 3 AND COALESCE(leads.cold, 0) >= 125 AND COALESCE(leads.hot, 0) >= 25 AND COALESCE(sales.deal, 0) >= 3 THEN 100000
                    ELSE 0
                END AS trainee
            FROM (
                    SELECT b.id AS company_id,
                        b.code AS company_code,
                        b.name AS company_name,
                        tl.id AS team_leader_id,
                        tl.registry_number AS team_leader_nip,
                        tl.name AS team_leader_name,
                        s.id AS salesman_id,
                        s.registry_number AS salesman_nip,
                        s.name AS salesman_name,
                        COUNT(sol.id) AS deal,
                        COALESCE(s.working_start_date, %(start_date)s) AS joined,
                        EXTRACT(YEAR FROM age(%(end_date)s, COALESCE(s.working_start_date, %(start_date)s))) * 12 + EXTRACT(MONTH FROM age(%(end_date)s, COALESCE(s.working_start_date, %(start_date)s))) AS yos
                    FROM tw_dealer_sale_order AS so
                        LEFT JOIN tw_dealer_sale_order_line AS sol ON sol.order_id = so.id
                        LEFT JOIN hr_employee AS tl ON tl.id = so.sales_coordinator_id
                        LEFT JOIN hr_employee AS s ON s.id = so.sales_id
                        LEFT JOIN hr_job AS j ON j.id = tl.job_id
                        LEFT JOIN res_company AS b ON b.id = tl.company_id
                    WHERE so.date_order BETWEEN %(start_date)s AND %(end_date)s
                        AND so.company_id IN %(company_list)s
                        AND j.sales_category = 'sales_team_leader'
                        AND so.state != 'cancel'
                    GROUP BY b.id, tl.id, s.id
                ) sales
                FULL OUTER JOIN (
                    SELECT b.id AS company_id,
                        b.code AS company_code,
                        b.name AS company_name,
                        tl.id AS team_leader_id,
                        tl.registry_number AS team_leader_nip,
                        tl.name AS team_leader_name,
                        s.id AS salesman_id,
                        s.registry_number AS salesman_nip,
                        s.name AS salesman_name,
                        SUM(CASE WHEN l.interest = 'cold' THEN 1 ELSE 0 END) AS cold,
                        SUM(CASE WHEN l.interest = 'hot' THEN 1 ELSE 0 END) AS hot,
                        COALESCE(s.working_start_date, %(start_date)s) AS joined,
                        EXTRACT(YEAR FROM age(%(end_date)s, COALESCE(s.working_start_date, %(start_date)s))) * 12 + EXTRACT(MONTH FROM age(%(end_date)s, COALESCE(s.working_start_date, %(start_date)s))) AS yos
                    FROM tw_lead AS l
                        LEFT JOIN hr_employee AS tl ON tl.id = l.sales_coordinator_id
                        LEFT JOIN hr_employee AS s ON s.id = l.sales_id
                        LEFT JOIN hr_job AS j ON j.id = tl.job_id
                        LEFT JOIN res_company AS b ON b.id = tl.company_id
                    WHERE l.date BETWEEN %(start_date)s AND %(end_date)s
                        AND l.company_id IN %(company_list)s
                        AND j.sales_category = 'sales_team_leader'
                    GROUP BY b.id, tl.id, s.id
                ) leads ON leads.team_leader_id = sales.team_leader_id 
                AND leads.salesman_id = sales.salesman_id
                AND leads.company_code = sales.company_code
        """, start_date=start_date, end_date=end_date, company_list=company_list))
        results = self._cr.dictfetchall()

        final = []
        if self.report_type == 'summary':
            report_name = 'Report Team Leader'
            for result in results:
                yos = result.get('yos')
                cold = result.get('cold', 0)
                hot = result.get('hot', 0)
                deal = result.get('deal', 0)
                trainee = result.get('trainee', 0)
                years = int(yos // 12)
                months = int(yos % 12)
                final.append(OrderedDict([
                    ('Kode Cabang', result.get('company_code')),
                    ('Nama Cabang', result.get('company_name')),
                    ('Team Leader', result.get('team_leader_name')),
                    ('Salesman NIP', result.get('salesman_nip')),
                    ('Salesman', result.get('salesman_name')),
                    ('Cold', cold),
                    ('Hot', hot),
                    ('Deal', deal),
                    ('Masa Kerja', f"{years} tahun {months} bulan"),
                    ('Joined', result.get('joined')),
                    ('Trainee', trainee),
                ]))
                
        elif self.report_type == 'detail':
            report_name = 'Report Team Leader Detail'
            sorted_res = sorted(results, key=lambda x: x['team_leader_nip'])
            for key, value in groupby(sorted_res, lambda x: x['team_leader_nip']):
                value = list(value)
                cold = sum([val.get('cold', 0) for val in value])
                hot = sum([val.get('hot', 0) for val in value])
                deal = sum([val.get('deal', 0) for val in value])
                trainee = sum([val.get('trainee', 0) for val in value])
                incentive = deal * 20000 if deal >= 20 else deal * 15000
                reward = 0
                if deal >= 50:
                    reward = 3200000
                elif deal >= 40 and deal < 50:
                    reward = 2500000
                elif deal >= 30 and deal < 40:
                    reward = 2000000
                elif deal >= 20 and deal < 30:
                    reward = 800000
                elif deal >= 10 and deal < 20:
                    reward = 250000

                first_val = value[0]
                company = self.env['res.company'].search([('code', '=', first_val.get('company_code'))], limit=1)
                minimum_wage = company.branch_setting_id.regional_minimum_wages or 0
                professional_allowance = self._prorate_professional_allowance(key, (minimum_wage) * 0.5)
                row = OrderedDict([
                    ('Kode Cabang', first_val.get('company_code')),
                    ('Nama Cabang', first_val.get('company_name')),
                    ('Team Leader', first_val.get('team_leader_name')),
                    ('Team Leader NIP', key),
                    ('Joined Date', first_val.get('joined')),
                    ('Masa Kerja', first_val.get('yos')),
                    ('Team Member', len(value)),
                    ('Cold', cold),
                    ('Hot', hot),
                    ('Deal', deal),
                    ('Tunjangan Profesi', professional_allowance),
                    ('Tunjangan Pembinaan', trainee),
                    ('Incentive', incentive),
                    ('Reward', reward),
                    ('Grand Total', (professional_allowance) + trainee + incentive + reward),
                ])
                """
                    NOTE: TSK/2024/04/03103
                    report team leader incentive amount needs to be hidden,
                    since SCO level is not going to generate any incentive
                
                """

                final.append(row)
        
        return self.env['web.report'].generate_report(report_name, final, start_date=start_date, end_date=end_date)

    def _prorate_professional_allowance(self, nip, wage_rate):
        tl = self.env['hr.employee'].search([('registry_number', '=', nip)], limit=1)
        if tl and tl.working_start_date:
            if (self.end_date - self.start_date) > (self.end_date - tl.working_start_date):
                business_days = (self.end_date - tl.working_start_date).days
                per_day = wage_rate / (self.end_date - self.start_date).days
                return business_days * per_day
        
        return wage_rate    

    