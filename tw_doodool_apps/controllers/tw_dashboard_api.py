#-*- coding: utf-8 -*-

# 1: imports of python lib
import base64
import json
import logging
import traceback

from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib
from odoo.addons.tw_api.controllers.main import valid_response, invalid_response, check_sensitive_value
from odoo.addons.rest_api.controllers.main import check_valid_token, validate_payload

# 3:  imports of odoo

from odoo import _, http, Command

# 4:  imports from odoo modules
from odoo.http import request, Response
from odoo.exceptions import UserError as Warning, ValidationError
from odoo.tools import SQL

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)


class ControllerREST(http.Controller):
    @http.route('/api/doodool/<version>/get_resume_dashboard', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_resume_dashboard(self, version):
        uid = request.session.uid
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', uid)],limit=1)
        company_ids = request.env.user.company_ids
        if not company_ids:
            return invalid_response(400, 'Company not found', 'Company not found')

        today = datetime.now()
        first_day_of_month = today.replace(day=1)

        company_id = employee.company_id.id

        resume = {}
        query_target = SQL(f"""
            WITH latest_targets AS (
                SELECT DISTINCT ON (ts.name, tsp.company_id)
                    ts.name AS category,
                    tsp.company_id,
                    tsp_line.target
                FROM tw_target_sales_people_line tsp_line
                JOIN tw_target_sales_people tsp ON tsp.id = tsp_line.target_id
                JOIN hr_job hj ON hj.id = tsp.job_id
                JOIN tw_selection ts ON ts.id = tsp_line.category_id
                WHERE tsp.company_id = {company_id}
                AND hj.name->>'en_US' = 'Sales Counter'
                AND tsp_line.type = 'Daily'
                ORDER BY ts.name, tsp.company_id, tsp_line.id DESC
            )
            SELECT 
                COALESCE(MAX(CASE WHEN category = 'Cold Prospect' THEN target END), 0) AS target_cold,
                COALESCE(MAX(CASE WHEN category = 'Hot Prospect' THEN target END), 0) AS target_hot,
                COALESCE(MAX(CASE WHEN category = 'Deal Prospect' THEN target END), 0) AS target_deal,
                COALESCE(MAX(CASE WHEN category = 'Propose Prospect' THEN target END), 0) AS target_propose,
                COALESCE(MAX(CASE WHEN category = 'Sales' THEN target END), 0) AS target_dso,
                0 AS target_dso
            FROM res_company rc
            LEFT JOIN latest_targets lt ON lt.company_id = rc.id
            WHERE rc.id = {company_id};
        """)

        try:
            request.env.cr.execute(query_target)
            target = request.env.cr.dictfetchone()
            resume['target'] = target
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))


        query_prospect = SQL(f"""
            SELECT 
                COALESCE(SUM(CASE WHEN ts.name = 'Cold' AND lead.state = 'open' THEN 1 ELSE 0 END), 0) AS cold_prospect
                , COALESCE(SUM(CASE WHEN ts.name = 'Hot' AND lead.state = 'open' THEN 1 ELSE 0 END), 0) AS hot_prospect
                , COALESCE(SUM(CASE WHEN lead.state = 'dealt' THEN 1 ELSE 0 END), 0) AS deal_prospect
                , COALESCE(SUM(CASE WHEN lead.state not in ('open','cancel','dealt') AND lead.propose_date is not null THEN 1 ELSE 0 END), 0) AS propose_prospect
            FROM tw_lead lead
            LEFT JOIN tw_selection ts ON ts.id = lead.interest_id 
            WHERE lead.state != 'cancel'
            AND lead.sales_id = {employee.id}
            AND lead.date = '{today}'
        """)

        try:
            request.env.cr.execute(query_prospect)
            prospect = request.env.cr.dictfetchone()
            resume['actual'] = prospect
            resume['actual'].update({
                'incentive':str(employee.total_incentive),
                'incentive_pending_in':str(employee.total_incentive_pending_in),
                'incentive_pending_out':str(employee.total_incentive_pending_out),
            })
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))

        query_sp = SQL(f"""
            SELECT 
                COALESCE(sp.sp_level,'0') as sp_level
            FROM hr_employee he 
            LEFT JOIN tw_sp_digital sp on sp.employee_id = he.id 
                AND sp.state in ('confirmed','done')
                AND sp.date > '{first_day_of_month}'
            WHERE he.id = {employee.id}
        """)

        try:
            request.env.cr.execute(query_sp)
            sp = request.env.cr.dictfetchone()
            resume['sp'] = sp
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))

        query_dso = SQL(f"""
            SELECT 
                COUNT(dsol.id) as dso,
                COALESCE(SUM(CASE WHEN ts.name = 'Cash' THEN 1 ELSE 0 END),0) as cash,
                COALESCE(SUM(CASE WHEN ts.name = 'Credit' THEN 1 ELSE 0 END),0) as credit
            FROM hr_employee he 
            LEFT JOIN tw_dealer_sale_order dso on dso.sales_id = he.id 
                AND dso.date_order BETWEEN '{first_day_of_month}' AND '{today}'
            LEFT JOIN tw_dealer_sale_order_line dsol on dsol.order_id = dso.id
            LEFT JOIN tw_selection ts on dso.payment_type_id = ts.id
            WHERE he.id = {employee.id}
            GROUP BY he.id
        """)

        try:
            request.env.cr.execute(query_dso)
            dso = request.env.cr.dictfetchone()
            resume['dso'] = dso
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))

        return valid_response(200, 'Success', resume)

    
    @http.route('/api/doodool/<version>/get_resume_dashboard_ol', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_resume_dashboard_ol(self, version):
        # OL mean Operational Leader
        uid = request.session.uid
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', uid)],limit=1)
        company_ids = request.env.user.company_ids
        if not company_ids:
            return invalid_response(400, 'Company not found', 'Company not found')

        today = datetime.now()
        first_day_of_month = today.replace(day=1)

        job_sales_force = 'sales_operation_head'
        company = tuple([employee.company_id.id])
        total_sales = 1
        additional_where = " AND 1=1"

        if employee.job_id.sales_force_id.name == 'sales_coordinator':
            query_salesman = SQL(f"""
                SELECT 
                    count(he.id) as total_sales
                    , string_agg(he.id::VARCHAR,',') as id_sales
                FROM res_company rc 
                LEFT JOIN hr_employee he on he.company_id = rc.id 
                LEFT JOIN hr_job hj on hj.id = he.job_id 
                LEFT JOIN tw_selection ts on ts.id = hj.sales_force_id 
                WHERE 1=1
                AND he.working_end_date is null 
                AND he.parent_id = {employee}
                AND rc.id = {employee.company_id.id}
                AND ts.name in ('salesman','sales_counter') 
            """)

            try:
                request.env.cr.execute(query_salesman)
                salesman = request.env.cr.dictfetchone()
            except Exception as e:
                return invalid_response(500, e.__class__.__name__, str(e))

            total_sales = salesman.get('total_sales', 0) if salesman else '0'
            sales_ids = salesman.get('id_sales', '') if salesman else ''
            job_sales_force = employee.job_id.sales_force_id.name
            if sales_ids:
                additional_where = " AND he.id in ({},{})".format(sales_ids, employee.id)
            else:
                additional_where = " AND he.id = {}".format(employee.id)
        elif employee.job_id.sales_force_id.name == 'area_manager':
            total_sales = len(company_ids)
            company = tuple(company_ids.ids)

        resume = {}
        query_target = SQL(f"""
            WITH latest_targets AS (
                SELECT DISTINCT ON (ts.name, target.company_id, ts2.name)
                    ts2.name as category,
                    target.company_id,
                    line.target
                FROM tw_target_sales_people_line AS line
                JOIN tw_target_sales_people AS target ON target.id = line.target_id
                JOIN hr_job AS job ON job.id = target.job_id
                JOIN tw_selection AS ts ON ts.id = job.sales_force_id
                JOIN tw_selection AS ts2 ON ts2.id = line.category_id
                WHERE ts.value = '{job_sales_force}'
                AND line.type = 'Daily'
                AND target.company_id = {employee.company_id.id}
                AND ts2.value IN ('Cold Prospect', 'Hot Prospect', 'Deal Prospect', 'Propose Prospect', 'Sales')
                ORDER BY ts.name, target.company_id, ts2.name, line.id DESC
            )
            SELECT 
                COALESCE(MAX(CASE WHEN category = 'Cold Prospect' THEN target END) * {total_sales}, 0) AS target_cold,
                COALESCE(MAX(CASE WHEN category = 'Hot Prospect' THEN target END) * {total_sales}, 0) AS target_hot,
                COALESCE(MAX(CASE WHEN category = 'Deal Prospect' THEN target END) * {total_sales}, 0) AS target_deal,
                COALESCE(MAX(CASE WHEN category = 'Propose Prospect' THEN target END) * {total_sales}, 0) AS target_propose,
                COALESCE(MAX(CASE WHEN category = 'Sales' THEN target END) * {total_sales}, 0) AS target_do
            FROM res_company AS company
            LEFT JOIN latest_targets lt ON lt.company_id = company.id
            WHERE company.id = {employee.company_id.id};
        """)

        try:
            request.env.cr.execute(query_target)
            target = request.env.cr.dictfetchone()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))

        resume['target'] = target
        company_list = str(company).replace(',)', ')')
        query_prospect = f"""
            SELECT 
                COALESCE(SUM(CASE WHEN ts.name = 'Cold' AND lead.state = 'open' THEN 1 ELSE 0 END), 0) AS cold_prospect
                , COALESCE(SUM(CASE WHEN ts.name = 'Hot' AND lead.state = 'open' THEN 1 ELSE 0 END), 0) AS hot_prospect
                , COALESCE(SUM(CASE WHEN lead.state = 'dealt' THEN 1 ELSE 0 END), 0) AS deal_prospect
                , COALESCE(SUM(CASE WHEN lead.state not in ('open','cancel','dealt') AND lead.propose_date is not null THEN 1 ELSE 0 END), 0) AS propose_prospect 
            FROM tw_lead lead
            LEFT JOIN hr_employee he on he.id = lead.sales_id 
            LEFT JOIN hr_job hj on hj.id = he.job_id 
            LEFT JOIN tw_selection ts on ts.id = lead.interest_id 
            WHERE 1=1
            AND lead.state != 'cancel'
            AND lead.company_id in ({company_list})
            AND he.working_end_date is null
            AND hj.sales_force_id is not null
            AND (lead.date = '{today}' OR (lead.deal_date + INTERVAL '7 hours')::DATE = '{today}' OR (lead.propose_date + INTERVAL '7 hours')::DATE = '{today}')
            {additional_where}
        """.format(today=today, company_list=company_list, additional_where=additional_where)

        try:
            request.env.cr.execute(query_prospect)
            prospect = request.env.cr.dictfetchone()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))

        resume['actual'] = prospect
        resume['actual'].update({
            'incentive':str(employee.total_incentive),
            'incentive_pending_in':str(employee.total_incentive_pending_in),
            'incentive_pending_out':str(employee.total_incentive_pending_out),
        })

        query_sp = SQL(f"""
            SELECT 
                COALESCE(sp.sp_level,'0') as sp_level
            FROM hr_employee he 
            LEFT JOIN tw_sp_digital sp on sp.employee_id = he.id 
                AND sp.state in ('confirmed','done')
                AND sp.date > '{first_day_of_month}'
            WHERE he.id = {employee.id}
        """)

        try:
            request.env.cr.execute(query_sp)
            sp = request.env.cr.dictfetchone()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))

        resume['sp'] = sp
        
        query_dso = SQL(f"""
            SELECT 
                COUNT(distinct he.id) as total_active_employee
                , count(distinct he.id) filter (WHERE ts.name = 'sales_coordinator') as total_active_sco
                , count(dsol.id) as dso
                ,COALESCE(SUM(CASE WHEN ts2.name = 'Cash' THEN 1 ELSE 0 END),0) as cash
                ,COALESCE(SUM(CASE WHEN ts2.name = 'Credit' THEN 1 ELSE 0 END),0) as credit
            FROM hr_employee he 
            LEFT JOIN hr_job hj on hj.id = he.job_id 
            LEFT JOIN tw_selection ts on ts.id = hj.sales_force_id 
            LEFT JOIN tw_dealer_sale_order dso on dso.sales_id = he.id 
                AND dso.date_order BETWEEN '{first_day_of_month}' AND '{today}'
            LEFT JOIN tw_selection ts2 on ts2.id = dso.payment_type_id 
            LEFT JOIN tw_dealer_sale_order_line dsol on dsol.order_id = dso.id
            WHERE 1=1
            AND he.company_id in {company_list}    
            {additional_where}        
        """)

        try:
            request.env.cr.execute(query_dso)
            dso = request.env.cr.dictfetchone()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))

        resume['dso'] = dso
        resume['dso'].update({'total_company':len(company)})

        return valid_response(200, resume)


    @http.route('/api/doodool/<version>/list_sales_performer', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def list_sales_performer(self, version, **post):
        uid = request.session.uid
        employee_id = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)
        if not employee_id:
            return invalid_response(400, 'Bad Request', 'Employee not found')

        today = (datetime.now()).date()
        company_id = False

        main_query = """
            SELECT 
                rr.user_id as user_id 
                , employee.id as id 
                , employee.name as nama_sales
                , sco.name as nama_sco
                , sco.id as sco_id
                , company.id as company_id 
                , '[' || company.code || '] ' || company.name as company
                , kacab.id as kacab_id
                , md.id as md_id
                , md.name as md_name
                , COALESCE(SUM(CASE WHEN ts.name = 'Cold Prospect' AND lead.state = 'open' THEN 1 ELSE 0 END),0)::int as cold_prospect
                , COALESCE(SUM(CASE WHEN ts.name = 'Hot Prospect' AND lead.state = 'open' THEN 1 ELSE 0 END),0)::int as hot_prospect
                , COALESCE(SUM(CASE WHEN lead.state = 'dealt' THEN 1 ELSE 0 END),0)::int as deal_prospect
                , COALESCE(SUM(CASE WHEN lead.state not in ('open','cancel','dealt') AND lead.propose_date is not null THEN 1 ELSE 0 END),0)::int as propose_prospect
                , COALESCE(employee.mobile_phone, employee.work_phone) as phone
                , COALESCE(kacab.mobile_phone, kacab.work_phone) as kacab_phone
                , sp.sp_level
            FROM hr_employee employee
            LEFT JOIN tw_sp_digital sp on sp.employee_id = employee.id
                AND sp."year" = date_part('year', (select current_timestamp))::VARCHAR 
                AND sp."month" = date_part('month', (select current_timestamp))::VARCHAR
            LEFT JOIN res_company company on company.id = employee.company_id 
            LEFT JOIN res_company md on md.id = company.default_supplier_id
            LEFT JOIN hr_employee sco on sco.id = employee.parent_id
            LEFT JOIN tw_branch_setting branch_set on branch_set.id = company.branch_setting_id
            LEFT JOIN hr_employee kacab on kacab.id = branch_set.branch_head_id 
            LEFT JOIN tw_lead lead on (lead.date = '{today}'
                OR (lead.deal_date + interval '7 hours')::date = '{today}'
                OR (lead.propose_date + interval '7 hours')::date = '{today}')
                AND lead.sales_id = employee.id
            LEFT JOIN hr_job job on job.id = employee.job_id
            LEFT JOIN tw_selection ts on ts.id = lead.interest_id 
            INNER JOIN resource_resource rr on rr.id = employee.resource_id
            WHERE employee.working_end_date IS NULL 
            AND job.sales_force_id IS NOT NULL 
            {where}
            GROUP BY company.id, md.id, rr.user_id, employee.id, sco.id, sp.id, kacab.id
            ORDER BY sco.name, sco.id, company.id
            {limit}
        """

        company_ids = request.env.user.company_ids
        company_id = str(tuple(company_ids.ids)).replace(',)', ')')

        if not company_id:
            return invalid_response(401, 'Unauthorized', 'Company not found')

        employee_role = employee_id.job_id.sales_force_id.value

        # Dashboard KaCab
        if employee_role == 'sales_operation_head':
            limit = "LIMIT 100"
            where = f" AND employee.company_id in {company_id}"
            query = f"""
                SELECT 
                    sales.sco_id as id
                    , sales.nama_sco as nama_sco
                    , sum(sales.cold_prospect) as cold_prospect
                    , sum(sales.hot_prospect) as hot_prospect
                    , sum(sales.deal_prospect) as deal_prospect
                    , sum(sales.propose_prospect) as propose_prospect
                    , json_agg(json_build_object(
                        'id', sales.id,
                        'user_id', sales.user_id,
                        'nama_sales', sales.nama_sales,
                        'cold_prospect', sales.cold_prospect,
                        'hot_prospect', sales.hot_prospect,
                        'deal_prospect', sales.deal_prospect,
                        'propose_prospect', sales.propose_prospect,
                        'phone', sales.phone,
                        'sp_level', sales.sp_level
                        )::jsonb) as list_sales
                FROM (
                    {main_query}
                ) as sales
                WHERE sales.id != sales.sco_id
                GROUP BY sales.sco_id, sales.nama_sco
            """
        # Dashboard AM
        elif employee_role == 'area_manager':
            limit = " "
            where = f" AND employee.company_id in {company_id}"
            query = f"""
                SELECT 
                    sales.md_id as md_id
                    , sales.md_name as md_name
                    , sum(sales.cold_prospect) as cold_prospect
                    , sum(sales.hot_prospect) as hot_prospect
                    , sum(sales.deal_prospect) as deal_prospect
                    , sum(sales.propose_prospect) as propose_prospect
                    , json_agg(json_build_object(
                        'id', sales.company_id,
                        'user_id', sales.company_id,
                        'nama_sales', sales.company,
                        'cold_prospect', sales.cold_prospect,
                        'hot_prospect', sales.hot_prospect,
                        'deal_prospect', sales.deal_prospect,
                        'propose_prospect', sales.propose_prospect,
                        'phone', sales.kacab_phone,
                        'sp_level', 0
                        )::jsonb) as list_sales
                FROM (
                    SELECT 
                        sales.md_id as md_id
                        , sales.md_name as md_name
                        , sales.company as company
                        , sales.company_id as company_id
                        , sales.kacab_phone as kacab_phone
                        , sum(sales.cold_prospect) as cold_prospect
                        , sum(sales.hot_prospect) as hot_prospect
                        , sum(sales.deal_prospect) as deal_prospect
                        , sum(sales.propose_prospect) as propose_prospect
                    FROM (
                        {main_query}
                    ) as sales
                    GROUP BY sales.md_id, sales.md_name, sales.company, sales.company_id, sales.kacab_phone) as sales
                GROUP BY sales.md_id, sales.md_name
            """
        # Dashboard SCO
        else:
            limit = "LIMIT 100"
            where = f" AND employee.company_id in {company_id}"
            query = main_query
        
        try:
            query = query.format(today=today, limit=limit, where=where)
            request.env.cr.execute(query)
            result = request.env.cr.dictfetchall()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))

        return valid_response(200, result)

    @http.route('/api/doodool/<version>/get_ranking_poin', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_ranking_poin(self, version, **post):
        # TODO: di skip dlu kata kak Majid, karena query point belum tahu fieldnya darimana
        WHERE=" "

        uid = request.session.uid
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',uid)],limit=1)
        job_sales_force = employee_id.job_id.sales_force_id.value

        if job_sales_force == 'sales_coordinator':
            job="('SALES COUNTER COORDINATOR','SALES COORDINATOR')"
        elif job_sales_force == 'sales_operation_head':
            job="('KEPALA CABANG','BRANCH HEAD')"
        else:
            job = "('SALESMAN','SALES COUNTER', SWAT, WSP)"

        WHERE += f" AND job.name IN {job}"
        query_jumlah = f"""
            SELECT 
                count(hre.id) as jumlah_sales
            FROM hr_employee hre 
            LEFT JOIN hr_job job on hre.job_id=job.id 
            LEFT JOIN tw_selection ts on job.sales_force_id = ts.id
            WHERE ts.value in ('salesman','sales_counter','sales_partner','sales_operation_head')      
            --Currently tunas_id is not available
            --need to confirm if this field will exist in future
            --AND hre.tunas_id is not null
            AND hre.working_end_date IS NULL 
            {WHERE}
        """

        try:
            request.env.cr.execute(query_jumlah)
            result = request.env.cr.fetchone()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))

        jumlah_sales = result[0]

        query_point = f"""
            SELECT 
            a.point as poin
            ,a.incentive::int as incentive
            ,a.point_earned as poin_earned
            ,a.incentive_earned as incentive_earned
            ,a.point_pending as poin_pending
            ,a.incentive_pending as incentive_pending
            ,a.rank_all ranking
            --, a.rating_count as agent_rating_count
            from  hr_employee as a
            WHERE a.id = {employee_id.id}
        """
        try:
            request.env.cr.execute(query_point)
            result_point = request.env.cr.dictfetchall()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))

        result_point[0]['jumlah_sales'] = jumlah_sales
        if result_point:
            result = result_point[0]
        else:
            result = {}

        return valid_response(200, result)



