#-*- coding: utf-8 -*-

# 1: imports of python lib
import base64
import json
import logging
import traceback

from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib
from odoo.addons.tw_api.controllers.main import valid_response, invalid_response, check_sensitive_value
from odoo.addons.rest_api.controllers.main import check_valid_token, validate_payload

# 3:  imports of odoo

from odoo import _, http, Command

# 4:  imports from odoo modules
from odoo.http import request, Response
from odoo.exceptions import UserError as Warning, ValidationError, RedirectWarning
from odoo.tools import SQL

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)

class ControllerREST(http.Controller):

    def _get_validated_selection_values(self, post):
        vals = {}
        selection = request.env['tw.selection']
        try:
            if 'gender_id' in post:
                vals['gender_id'] = selection.validate_selection(int(post['gender_id']), 'Gender')
            if 'interest_id' in post:
                vals['interest_id'] = selection.validate_selection(int(post['interest_id']), 'Interest')
            # Support both app key 'golongan_darah_id' and model key 'blood_type_id'
            if 'golongan_darah_id' in post:
                vals['blood_type_id'] = selection.validate_selection(int(post['golongan_darah_id']), 'BloodType')
            elif 'blood_type_id' in post:
                vals['blood_type_id'] = selection.validate_selection(int(post['blood_type_id']), 'BloodType')
            # Support both app key 'agama_id' and model key 'religion_id'
            if 'agama_id' in post:
                vals['religion_id'] = selection.validate_selection(int(post['agama_id']), 'Religion')
            elif 'religion_id' in post:
                vals['religion_id'] = selection.validate_selection(int(post['religion_id']), 'Religion')
            # Support both app key 'pekerjaan_id' and model key 'occupation_id'
            if 'pekerjaan_id' in post:
                vals['occupation_id'] = selection.validate_selection(int(post['pekerjaan_id']), 'Occupation')
            elif 'occupation_id' in post:
                vals['occupation_id'] = selection.validate_selection(int(post['occupation_id']), 'Occupation')
            if 'motor_brand_id' in post:
                vals['motor_brand_id'] = selection.validate_selection(int(post['motor_brand_id']), 'MotorBrand')
            if 'motor_type_id' in post:
                vals['motor_type_id'] = selection.validate_selection(int(post['motor_type_id']), 'MotorType')
            # Support both app key 'hobi_id' and model key 'hobby_id'
            if 'hobi_id' in post:
                vals['hobby_id'] = selection.validate_selection(int(post['hobi_id']), 'Hobby')
            elif 'hobby_id' in post:
                vals['hobby_id'] = selection.validate_selection(int(post['hobby_id']), 'Hobby')
            # Support both app key 'pendidikan_id' and model key 'education_id'
            if 'pendidikan_id' in post:
                vals['education_id'] = selection.validate_selection(int(post['pendidikan_id']), 'Education')
            elif 'education_id' in post:
                vals['education_id'] = selection.validate_selection(int(post['education_id']), 'Education')
            # Support both app key 'pengguna_id' and model key 'unit_operator_id'
            if 'pengguna_id' in post:
                vals['unit_operator_id'] = selection.validate_selection(int(post['pengguna_id']), 'MotorUser')
            elif 'unit_operator_id' in post:
                vals['unit_operator_id'] = selection.validate_selection(int(post['unit_operator_id']), 'MotorUser')
            # Support both app key 'penggunaan_id' and model key 'unit_usage_id'
            if 'penggunaan_id' in post:
                vals['unit_usage_id'] = selection.validate_selection(int(post['penggunaan_id']), 'MotorUtilization')
            elif 'unit_usage_id' in post:
                vals['unit_usage_id'] = selection.validate_selection(int(post['unit_usage_id']), 'MotorUtilization')
            # Support both app key 'status_hp_id' and model key 'mobile_plan_status_id'
            if 'status_hp_id' in post:
                vals['mobile_plan_status_id'] = selection.validate_selection(int(post['status_hp_id']), 'StatusMobilePhone')
            elif 'mobile_plan_status_id' in post:
                vals['mobile_plan_status_id'] = selection.validate_selection(int(post['mobile_plan_status_id']), 'StatusMobilePhone')
            # Support both app key 'status_rumah_id' and model key 'housing_tenure_id'
            if 'status_rumah_id' in post:
                vals['housing_tenure_id'] = selection.validate_selection(int(post['status_rumah_id']), 'HousingTenure')
            elif 'housing_tenure_id' in post:
                vals['housing_tenure_id'] = selection.validate_selection(int(post['housing_tenure_id']), 'HousingTenure')
            if 'marital_status_id' in post:
                vals['marital_status_id'] = selection.validate_selection(int(post['marital_status_id']), 'MaritalStatus')
            # Support both app key 'pengeluaran_id' and model key 'expense_id'
            if 'pengeluaran_id' in post:
                vals['expense_id'] = selection.validate_selection(int(post['pengeluaran_id']), 'Expense')
            elif 'expense_id' in post:
                vals['expense_id'] = selection.validate_selection(int(post['expense_id']), 'Expense')
            if 'income_id' in post:
                vals['income_id'] = selection.validate_selection(int(post['income_id']), 'Income')
            # Support both app key 'payment_type' and model key 'payment_type_id'
            if 'payment_type' in post and post['payment_type']:
                payment_type_id = selection.validate_selection(int(post['payment_type']), 'PaymentType')
                vals['payment_type_id'] = payment_type_id
                vals['payment_type'] = selection.browse(payment_type_id).value
            elif 'payment_type_id' in post and post['payment_type_id']:
                payment_type_id = selection.validate_selection(int(post['payment_type_id']), 'PaymentType')
                vals['payment_type_id'] = payment_type_id
                vals['payment_type'] = selection.browse(payment_type_id).value
            if 'sales_channel_id' in post:
                vals['sales_channel_id'] = selection.validate_selection(int(post['sales_channel_id']), 'SalesChannel')
            if 'customer_grade_id' in post:
                vals['customer_grade_id'] = selection.validate_selection(int(post['customer_grade_id']), 'CustomerGrade')
            if 'motor_ownership_id' in post:
                motor_ownership_id = selection.validate_selection(int(post['motor_ownership_id']), 'MotorOwnership')
                vals['motor_ownership_id'] = motor_ownership_id
                vals['motor_ownership'] = selection.browse(motor_ownership_id).value
        except Warning as e:
            return invalid_response(400, 'Selection Value not found', f"Selection Value not found: {e}")
        except ValueError as e:
            return invalid_response(400, 'Selection Value not found', f"Selection Value not found: {e}")
        
        return vals

    def _get_partner_id(self, partner_data):
        partner = request.env['res.partner']
        partner_stnk_identification_number = partner_data.get('identification_number')
        partner_stnk = partner.sudo().search([('identification_number', '=', partner_stnk_identification_number)])
        if not partner_stnk:
            partner_stnk = partner.sudo().create(partner_data)
        else:
            partner_data.pop('identification_number')
            partner_stnk.sudo().write(partner_data)
        return partner_stnk.id

    @http.route('/api/doodool/<version>/get_prospect', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_prospect(self, **post):
        uid = request.session.uid
        company_ids = request.env.user.company_ids
        WHERE = " " 
        team_list=[]
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', uid)],limit=1)
        team_list.append(employee.id)
        category = employee.job_id.job_category_id
        query = """
            SELECT 
                l.id as lead_id
                , l.customer_name as nama_customer
                , ((l.create_date + INTERVAL '7 hours')::date)::varchar as tgl_lead
                , l.interest as interest
                , COALESCE(s.name->>'en_US', '') as next_follow_up
                , (la.date + INTERVAL '7 hours')::varchar as next_tgl_follow_up
                , hr.name as assigned_by
                , b.name as branch_name
                , lar.id as respond_followup_id
                , lar.name as respond_followup
                , l.facebook
                , l.twitter
                , l.instagram
                , l.youtube
                , l.rejection_reason as rejection_reason
            FROM tw_lead l
            LEFT JOIN tw_lead_activity la ON la.id = l.next_activity_id
            LEFT JOIN tw_lead_activity_result lar ON lar.id = la.activity_result_id
            LEFT JOIN crm_stage s ON s.id = la.stage_id 
            LEFT JOIN hr_employee hr ON hr.id = l.sales_id
            LEFT JOIN hr_job job ON job.id = hr.job_id
            LEFT JOIN resource_resource r ON r.id = hr.resource_id 
            LEFT JOIN res_company b ON b.id = l.company_id
            WHERE l.state = 'open'
            AND l.data_by = 'lead'
        """

        kwargs = {}
        if uid != 1:
            if employee.job_id.sales_force_id.value == 'area_manager':
                query += " AND l.company_id IN %(company_ids)s"
                kwargs['company_ids'] = tuple(company_ids.ids)

            elif getattr(category, 'value', None) == 'dealer':
                if employee.job_id.name in ['Koordinator Sales Digital', 'Kepala Cabang Sales Digital']:
                    query += " AND job.name in ('Sales Digital','Koordinator Sales Digital','Kepala Cabang Sales Digital') "
                elif employee.job_id.sales_force_id.value in ['sales_coordinator', 'sales_operation_head']:
                    query += " AND l.company_id = %(company_id)s"
                    kwargs['company_id'] = employee.company_id.id
                else:
                    query += " AND l.sales_id = %(employee_id)s"
                    kwargs['employee_id'] = employee.id

            else:
                query += " AND l.sales_id = %(employee_id)s"
                kwargs['employee_id'] = employee.id
    
        agent_id = post.get('agent_id')
        limit = post.get('limit', 10)
        offset = post.get('offset', 0)
        string = post.get('string')

        if 'interest' in post:
            query += " AND l.interest = %(interest)s"
            kwargs.update({'interest': post['interest']})
        if 'followup_state' in post:
            if post['followup_state'] == 'Belum Ada Activity':
                query += " AND la.id IS NULL"
            elif post['followup_state'] == 'Belum Followup':
                query += " AND s.name IS NOT NULL AND la.stage_id IS NULL"
            elif post['followup_state'] == 'Sudah Followup':
                query += " AND la.id IS NOT NULL AND NOT (s.name IS NOT NULL AND la.stage_id IS NULL)"
        
        if string:
            query += " AND l.customer_name ILIKE %(customer_name)s"
            kwargs['customer_name'] = f'%{string}%'

        if agent_id:
            query += " AND hr.id = %(agent_id)s"
            kwargs['agent_id'] = agent_id if isinstance(agent_id, int) else int(agent_id)

        if 'sort_parameter' in post:
            if post['sort_parameter'] == 'interest':
                query += " ORDER BY l.interest ASC"
            if post['sort_parameter'] == 'followup_terdekat':
                query += " AND la.date IS NOT NULL"
                query += " ORDER BY la.date ASC"
        else:
            query += " ORDER BY l.id DESC"
        
        if limit:
            query += " LIMIT %(limit)s"
            kwargs['limit'] = limit if isinstance(limit, int) else int(limit)
        
        if offset:
            query += " OFFSET %(offset)s"
            kwargs['offset'] = offset if isinstance(offset, int) else int(offset)

        # Based on the odoo.tools SQL class, this approach is better for handling security and bugs from psycopg2.
        sql = SQL(query, **kwargs)
        try:
            request.env.cr.execute(sql)
            ress = request.env.cr.dictfetchall()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))
        
        return valid_response(200,ress)

    @http.route('/api/doodool/<version>/get_dealt_prospect', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_dealt_prospect(self, **post):
        uid = request.session.uid
        company_ids = request.env.user.company_ids
        WHERE = "WHERE deal_date IS NOT NULL AND lead.state != 'open' "
        team_list=[]
        employee = request.env['hr.employee'].sudo().search([('user_id','=',uid)],limit=1)
        team_list.append(employee.id)
        category = employee.job_id.job_category_id.value

        query = """
            SELECT 
                lead.id as lead_id
                , lead.customer_name as nama_customer
                , pt.name->>'en_US'  as product
                , pav.name->>'en_US' as warna_product
                --, type.name as tipe
                , lead.date::varchar as tgl_lead
                , COALESCE(((lead.deal_date  + INTERVAL '7 hours')::date)::varchar, 'null') as deal_date
                , COALESCE(((lead.propose_date  + INTERVAL '7 hours')::date)::varchar, 'null') as propose_date
                , COALESCE(((lead.receipt_date  + INTERVAL '7 hours')::date)::varchar, 'null') as receipt_date
                , COALESCE(((lead.approve_date  + INTERVAL '7 hours')::date)::varchar, 'null') as approve_date
                , 'null' as tgl_spk
                , 'null' as tgl_do
                , 'null' as tgl_stnk
                , 'null' as tgl_bpkb
                , 'null' no_bpkb
                , 'null' no_stnk
                --, COALESCE((spk.confirm_date + INTERVAL '7 hours','null'))::varchar as tgl_spk
                --, COALESCE((so.confirm_date + INTERVAL '7 hours','null'))::varchar as tgl_do
                --, COALESCE((lot.tgl_terima_stnk,'null'))::varchar as tgl_stnk
                --, COALESCE((lot.tgl_terima_bpkb,'null'))::varchar as tgl_bpkb
                --, COALESCE(lot.no_bpkb,'null') no_bpkb
                --, COALESCE(lot.no_stnk,'null') no_stnk
                , bb.name as branch_name
                , hr.name as assigned_by
                 ,lead.facebook
                ,lead.twitter
                ,lead.instagram
                ,lead.youtube
                -- ,lead.status_api_tdm
                -- ,lead.status_lead_teds
                , CASE WHEN lead.payment_type = '1' THEN 'Cash'
                    WHEN lead.payment_type = '2' THEN 'Credit'
                  END as payment_type
                ,  initcap(lead.unit_availability) AS status_unit
            FROM tw_lead AS lead
            LEFT JOIN product_product pp ON pp.id = lead.product_id
            JOIN product_template as pt on pt.id = pp.product_tmpl_id
            JOIN product_variant_combination as combination on combination.product_product_id = pp.id
            JOIN product_template_attribute_value as ptav on ptav.id = combination.product_template_attribute_value_id
            JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id			
            -- LEFT JOIN tw_product_type type ON type.id = pt.product_type_id
            INNER JOIN hr_employee hr ON hr.id = lead.sales_id
            LEFT JOIN hr_job job ON job.id = hr.job_id
            INNER JOIN resource_resource r ON r.id = hr.resource_id 
            LEFT JOIN res_company bb ON bb.id = lead.company_id
            WHERE 1 = 1
        """
        kwargs = {}
        if uid != 1:
            if employee.job_id.sales_force_id.value == 'area_manager':
                query += " AND lead.company_id IN ANY(%(company_ids)s)"
                kwargs['company_ids'] = company_ids.ids
            elif category == 'dealer':
                if employee.job_id.name in ['Koordinator Sales Digital','Kepala Cabang Sales Digital']:
                    query += " AND job.name in ('Sales Digital','Koordinator Sales Digital','Kepala Cabang Sales Digital') "
                elif employee.job_id.sales_force_id.value in ('sales_coordinator', 'sales_operation_head'):
                    query += " AND lead.company_id = %(company_id)s "
                    kwargs['company_id'] = employee.company_id.id
                else:  
                    query += " AND lead.sales_id = %(sales_id)s "
                    kwargs['sales_id'] = employee.id
            else:
                query += " AND lead.sales_id = %(sales_id)s "
                kwargs['sales_id'] = employee.id

        limit = post.get('limit', 10)
        offset = post.get('offset', 0)
        status_unit = post.get('status_unit', 'ready')
        product = post.get('product')
        agent_id = post.get('agent_id')
        string = post.get('string')
        status_unit = post.get('status_unit')

        if status_unit:
            query += " AND lead.unit_availability = %(status_unit)s "
            kwargs['status_unit'] = status_unit

        if product:
            query += " AND pp.id = %(product_id)s "
            kwargs['product_id'] = product if isinstance(product, int) else int(product)

        if agent_id:
            query += " AND hr.id = %(agent_id)s "
            kwargs['agent_id'] = agent_id if isinstance(agent_id, int) else int(agent_id)
        
        if string:
            query += " AND lead.customer_name ILIKE %(customer_name)s"
            kwargs['customer_name'] = f'%%{string}%%'

        query += " ORDER BY lead.deal_date DESC "
        
        if limit:
            query += f" LIMIT {limit}"
            kwargs['limit'] = limit if isinstance(limit, int) else int(limit)

        if offset:
            query += f" OFFSET {offset}"
            kwargs['offset'] = offset if isinstance(offset, int) else int(offset)
        
        sql = SQL(query, **kwargs)
        try:
            request.env.cr.execute(sql)
            ress = request.env.cr.dictfetchall()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))
        return valid_response(200,ress)
    
    @http.route('/api/doodool/<version>/get_proposed_prospect', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_proposed_prospect(self, **post):
        company_ids = request.env.user.company_ids
        if not company_ids:
            result = json.dumps({
                'message': "User does not have access to any company.",
                'error': "data_not_found",
            })
            return invalid_response(401, 'data_not_found', 'User does not have access to any branch.')

        query = """
            SELECT 
                l.id as lead_id
                , l.customer_name as nama_customer
                , (l.deal_date + INTERVAL '7 hours')::varchar as deal_date
                , l.facebook
                , l.twitter
                , l.instagram
                , l.youtube
                , pt.id as product_id
                , pt.name->>'en_US' as name_unit
                , pp.default_code as code_unit
                , pav.name->>'en_US' as warna
                , pav.code as code_warna
                , partner_finco.id as finco_id
                , partner_finco.name as finco_name
                , l.payment_type
                , l.tenor as tenor
                , l.installment as installment
                , l.down_payment as down_payment
                , rp.name as assigned_by
                , b.name as branch_name
                , '2' as owner
            FROM tw_lead l 
            LEFT JOIN tw_lead_activity la ON la.id = l.next_activity_id
            LEFT JOIN product_product pp ON pp.id = l.product_id
            LEFT JOIN product_template as pt on pt.id = pp.product_tmpl_id
            LEFT JOIN product_variant_combination as combination on combination.product_product_id = pp.id
            LEFT JOIN product_template_attribute_value as ptav on ptav.id = combination.product_template_attribute_value_id
            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id			
            -- LEFT JOIN tw_product_type type ON type.id = pt.product_type_id
            LEFT JOIN res_partner as partner_finco ON partner_finco.id=l.finco_id
            LEFT JOIN hr_employee hr ON hr.id = l.sales_id
            LEFT JOIN hr_job job ON job.id = hr.job_id
            LEFT JOIN resource_resource r ON r.id = hr.resource_id 
            INNER JOIN res_users ru on ru.id = l.create_uid
            INNER JOIN res_partner rp ON rp.id = ru.partner_id
            LEFT JOIN res_company b ON b.id = l.company_id
            WHERE l.state='dealt'
        """
        
        kwargs = {}
        uid = request.session.uid
        agent_id = post.get('agent_id', False)
        limit = post.get('limit', 10)
        offset = post.get('offset', 0)
        string = post.get('string', False)
        interest = post.get('interest')
        sort_parameter = post.get('sort_parameter')

        koordinator_id = 0
        sales_id = request.env['hr.employee'].sudo().search([('user_id', '=', uid)], limit=1)
        if uid != 1:
            if sales_id.job_id.name in ['Koordinator Sales Digital', 'Kepala Cabang Sales Digital']:
                query += " AND job.name in ('Sales Digital', 'Koordinator Sales Digital', 'Kepala Cabang Sales Digital') "
            elif sales_id.job_id.sales_force_id in ('area_manager','sales_operation_head'):
                query += " AND l.company_id IN %(company_ids)s "
                kwargs['company_ids'] = company_ids.ids
            else:
                if sales_id:
                    if sales_id.job_id.sales_force_id.value == 'sales_coordinator':
                        koordinator_id = sales_id.id
                if koordinator_id:
                    query += " AND (hr.parent_id = %(sales_id)s OR hr.id = %(sales_id)s) "
                    kwargs['sales_id'] = sales_id.id
                    
        if interest:
            query += " AND l.interest = %(interest)s "
            kwargs['interest'] = interest

        if agent_id:
            query += " AND hr.id = %(agent_id)s "
            kwargs['agent_id'] = agent_id if isinstance(agent_id, int) else int(agent_id)
        
        if string:
            query += " AND l.customer_name ILIKE %(customer_name)s"
            kwargs['customer_name'] = f'%{string}%'
        
        if sort_parameter:
            if sort_parameter == 'interest':
                query += " ORDER BY l.interest ASC "
            elif sort_parameter == 'followup_terdekat':
                query += " AND la.date IS NOT NULL "
                query += " ORDER BY la.date ASC "
        else:
            query += "ORDER BY l.deal_date DESC"

        if limit:
            query += f" LIMIT {limit} "
        
        if offset:
            query += f" OFFSET {offset} "
        
        try:
            request.env.cr.execute(SQL(query, **kwargs))
            ress = request.env.cr.dictfetchall()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))

        return valid_response(200, ress)
    
    @http.route('/api/doodool/<version>/get_crm_prospect', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_crm_prospect(self, **post):
        uid = request.session.uid
        WHERE = " " 
        team_list=[]
        employee= request.env['hr.employee'].sudo().search([('user_id','=',uid)],limit=1)
        team_list.append(employee.id)
        category = employee.job_id.job_category_id.value
        company_ids = request.env.user.company_ids
        
        query = """
            SELECT
                l.id as lead_id
                , l.customer_name as nama_customer
                , l.date::varchar as tgl_lead
                , l.interest as interest
                , s.name as next_follow_up
                , (la.date + INTERVAL '7 hours')::varchar  as next_tgl_follow_up
                , hr.name as assigned_by
                -- , (crm.open_date + INTERVAL '7 hours')::varchar  as tgl_crm
                , '' honda_id_sblm
                -- , crm.last_date_order::varchar  as tgl_pembelian_sblm
                , '' no_mesin_sblm
                -- , crm.product_type motor_sblm
                , l.mobile mobile_2
                , l.whatsapp mobile_3
                , '' subject_fu
                , (DATE_PART('YEAR', AGE(CURRENT_DATE, l.birthdate)))::varchar  umur 
                , b.name as branch_name
                , l.facebook
                , l.twitter
                , l.instagram
                , l.youtube
            FROM tw_lead l
            -- LEFT JOIN tw_lead_crm crm ON l.id = crm.lead_id
            LEFT JOIN tw_lead_activity la ON la.id = l.next_activity_id
            LEFT JOIN crm_stage s ON la.stage_id = s.id
            LEFT JOIN hr_employee hr ON hr.id = l.sales_id
            LEFT JOIN resource_resource r ON r.id = hr.resource_id 
            INNER JOIN res_users ru on ru.id = l.create_uid
            INNER JOIN res_partner rp ON rp.id = ru.partner_id
            LEFT JOIN res_company b ON b.id = l.company_id
            WHERE l.deal_date is null
            AND l.data_by='crm'
            AND l.state!= 'cancel'
        """

        kwargs = {}
        sort_parameter = False
        interest = post.get('interest')
        agent_id = post.get('agent_id')
        limit = post.get('limit', 10)
        offset = post.get('offset', 0)
        string = post.get('string')

        if uid != 1:
            if employee.job_id.sales_force_id.value == 'area_manager':
                query += " AND l.company_id IN %(company_ids)s"
                kwargs['company_ids'] = company_ids.ids
            elif category == 'dealer':
                if employee.job_id.name in ['Koordinator Sales Digital','Kepala Cabang Sales Digital']:
                    query += " AND job.name in ('Sales Digital','Koordinator Sales Digital','Kepala Cabang Sales Digital') "
                elif employee.job_id.sales_force_id.value in ('sales_coordinator', 'sales_operation_head'):
                    query += " AND l.company_id = %(company_id)s "
                    kwargs['company_id'] = employee.company_id.id
                else:  
                    query += " AND l.sales_id = %(sales_id)s "
                    kwargs['sales_id'] = employee.id
            else:
                query += " AND l.sales_id = %(sales_id)s "
                kwargs['sales_id'] = employee.id

        if 'followup_state' in post:
            if post['followup_state'] == 'Belum Ada Activity':
                query += " AND la.id IS NULL"
            elif post['followup_state'] == 'Belum Followup':
                query += " AND s.name IS NOT NULL AND la.stage_id IS NULL"
            elif post['followup_state'] == 'Sudah Followup':
                query += " AND la.id IS NOT NULL AND NOT (s.name IS NOT NULL AND la.stage_id IS NULL)"
        
        if interest:
            query += " AND l.interest = %(interest)s "
            kwargs['interest'] = interest

        if agent_id:
            query += " AND hr.id = %(agent_id)s "
            kwargs['agent_id'] = agent_id if isinstance(agent_id, int) else int(agent_id)
        
        if string:
            query += " AND l.customer_name ILIKE '%(customer_name)s'"
            kwargs['customer_name'] = f'%{string}%'
        
        if sort_parameter:
            if sort_parameter == 'interest':
                query += " ORDER BY l.interest ASC "
            elif sort_parameter == 'followup_terdekat':
                query += " AND la.date IS NOT NULL "
                query += " ORDER BY la.date ASC "
        else:
            query += " ORDER BY l.date DESC "

        if limit:
            query += f" LIMIT {limit} "
        
        if offset:
            query += f" OFFSET {offset} "

        try:
            request.env.cr.execute(SQL(query, **kwargs))
            ress = request.env.cr.dictfetchall()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))
        
        return valid_response(200, ress)
        
    @http.route('/api/doodool/<version>/get_detailed_prospect', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token    
    def get_detailed_prospect(self, **post):
        uid = request.session.uid
        sales_id = request.env['hr.employee'].sudo().search([('user_id', '=', uid)],limit=1)
        lead_id = post.get('id', False)
        if not lead_id:
            return invalid_response(401, 'data_not_found', 'Lead ID', 'GET')
        
        url = str(request.httprequest.url).split('/api/')[0]
        query_lead = """
            WITH address AS (
                SELECT l.id as lead_id,
                    state.id AS state_id,
                    state.code AS state_code,
                    state.name AS state_name,
                    city.id AS city_id,
                    city.code AS city_code,
                    city.name AS city_name,
                    district.id AS disctrict_id,
                    district.code AS disctrict_code,
                    district.name AS disctrict_name,
                    sub_district.id AS sub_disctrict_id,
                    sub_district.code AS sub_disctrict_code,
                    sub_district.name AS sub_disctrict_name,
                    sub_district.zip_code AS sub_disctrict_zip_code,
                    a.address_type_id
                FROM tw_lead l 
                    left join crm_lead_addresses a on a.lead_id = l.id
                    LEFT JOIN res_country_state state ON state.id = a.state_id
                    LEFT JOIN res_city city ON city.id = a.city_id
                    LEFT JOIN res_district district ON district.id = a.district_id
                    LEFT JOIN res_sub_district sub_district ON sub_district.id = a.sub_district_id
            )
            SELECT
                lead.id as lead_id
                , lead.id as id
                , CASE WHEN lead.interest_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',interest.id,   
                    'value',interest.value,
                    'name',interest.name
                    )::jsonb)) ELSE NULL END AS interest_id
                , COALESCE(lead.name,'') as name
                , COALESCE(lead.customer_name,'') as nama_customer
                , COALESCE(lead.identification_number,'') as identification_number
                , COALESCE(lead.identification_family_number,'') as identification_family_number
                , COALESCE(to_char(lead.birthdate,'YYYY-MM-DD'),'') as tgl_lahir
                , COALESCE(lead.birthplace,'') as tempat_tgl_lahir
                -- , COALESCE(lead.suku,'') as suku
                -- , COALESCE(lead.jabatan,'') as jabatan
                -- , COALESCE(lead.test_ride,null) as test_ride
                , COALESCE(lead.mobile,'') as mobile
                , COALESCE(lead.whatsapp,'') as whatsapp
                , COALESCE(lead.phone,'') as phone
                , COALESCE(lead.street,'') as street
                , COALESCE(lead.rt,'') as rt
                , COALESCE(lead.rw,'') as rw
                --, COALESCE(lead.latitude,'') as latitude
                --, COALESCE(lead.longitude,'') as longitude
                --, COALESCE(lead.domisili_street,'') as domisili_street
                --, COALESCE(lead.domisili_rt,'') as domisili_rt
                --, COALESCE(lead.domisili_rw,'') as domisili_rw
                --, COALESCE(lead.kantor_street,'') as kantor_street
                --, COALESCE(lead.kantor_rt,'') as kantor_rt
                --, COALESCE(lead.kantor_rw,'') as kantor_rw
                --, COALESCE(lead.kantor_kontak,'') as kantor_kontak
                --, COALESCE(lead.kk_street,'') as kk_street
                --, COALESCE(lead.kk_rt,'') as kk_rt
                --, COALESCE(lead.kk_rw,'') as kk_rw
                , COALESCE(lead.email,'') as email
                , COALESCE(lead.facebook,'') as facebook
                , COALESCE(lead.instagram,'') as instagram
                , COALESCE(lead.twitter,'') as twitter
                , COALESCE(lead.youtube,'') as youtube
                , COALESCE(lead.due_date::varchar,'') as due_date
                , CASE WHEN lead.sales_channel_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',sales_channel.id,
                    'value',sales_channel.value,
                    'name',sales_channel.name
                    )::jsonb)) ELSE NULL END AS sales_channel_id
                -- , COALESCE(lead.customer_code,'') as kode_customer
                , COALESCE(lead.rejection_reason,'') as rejection_reason
                , COALESCE(lead.price_otr,0) as price_otr
                , lead.payment_type
                , lead.tenor
                -- , lead.is_hc
                , COALESCE(lead.discount,0) as discount
                , lead.down_payment
                , COALESCE(to_char(lead.down_payment_date,'YYYY-MM-DD'),'') as down_payment_date
                , COALESCE(lead.current_motorcycle,'') as current_motorcycle
                , COALESCE(to_char(lead.propose_date,'YYYY-MM-DD hh:mm:ss'),'') as propose_date
                , COALESCE(to_char(lead.deal_date,'YYYY-MM-DD hh:mm:ss'),'') as deal_date
                , COALESCE(to_char(lead.receipt_date,'YYYY-MM-DD hh:mm:ss'),'') as receipt_date
                , COALESCE(to_char(lead.approve_date,'YYYY-MM-DD hh:mm:ss'),'') as approve_date
                , lead.installment
                , 'null' as tgl_spk
                , 'null' as tgl_do
                , 'null' as no_stnk
                , 'null' as tgl_stnk
                , 'null' as no_bpkb
                , 'null' as tgl_terima_bpkb
                , 'null' as is_fif_error
                , COALESCE((next_activity.date + INTERVAL '7 hours')::varchar,'') as next_tgl_follow_up
                , COALESCE(stage.name->>'en_US', '') as next_follow_up
                , stage.id as next_follow_up_id
                , next_activity.id as next_lead_activity_id
                , '[' || product.default_code || '] ' || (pt.name->>'en_US')::varchar || ' (' || (pav.name->>'en_US')::varchar || ')' AS product_name
                
                , CASE WHEN lead.company_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id', company.id,
                    'name', '[' || company.code || ']' || company.name
                    )::jsonb)) ELSE NULL END AS company_id
                
                , CASE WHEN lead.product_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id' , product.id,
                    'name' , pt.name->>'en_US',
                    'code' , product.default_code,
                    'warna' , pav.name->>'en_US',
                    'code_warna' , pav.code,
                    'price' , lead.price_otr
                    )::jsonb)) ELSE NULL END AS product_id
                
                , CASE WHEN lead.finco_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id', finco.id,
                    'name', finco.name
                    )::jsonb)) ELSE NULL END AS finco
                
                , CASE WHEN lead.sales_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id', employee.id,
                    'name', employee.name
                    )::jsonb)) ELSE NULL END AS sales_id

                , CASE WHEN lead.partner_stnk_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id', partner_stnk.id,
                    'name', partner_stnk.name
                    )::jsonb)) ELSE NULL END AS partner_stnk_id

                , CASE WHEN lead.sales_coordinator_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id', sco.id,
                    'name', sco.name
                    )::jsonb)) ELSE NULL END AS sales_coordinator_id
                
                , CASE WHEN lead.next_activity_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id', next_activity.id,
                    'name', next_activity.stage_id,
                    'date', next_activity.date::varchar
                    )::jsonb)) ELSE NULL END AS next_activity_id
                        
                , CASE WHEN count(activity) > 0 THEN (json_agg(DISTINCT json_build_object(
                    'id', activity.id,
                    'name', activity.stage_id,
                    'date', activity.date::varchar
                    )::jsonb)) ELSE NULL END AS activity_id
                
                 , CASE WHEN act_line.id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                     'id', act_line.id,
                     'name', titik_keramaian.name
                     )::jsonb)) ELSE NULL END AS titik_keramaian_id
                
                , CASE WHEN location.id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id', location.id,
                    'name', location.complete_name
                    )::jsonb)) ELSE NULL END AS sales_source_location_id
                
                , CASE WHEN act_type.id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id', act_type.id,
                    'name', act_type.name,
                    'is_activity', act_type.is_activity,
                    'code', act_type.code
                    )::jsonb)) ELSE NULL END AS act_type_id
                        
                --street KTP
                , CASE WHEN lead.state_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id', state.id,
                    'code', state.code,
                    'name', state.name
                    )::jsonb)) ELSE NULL END AS state
                , CASE WHEN lead.city_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id', city.id,
                    'code', city.code,
                    'name', city.name
                    )::jsonb)) ELSE NULL END AS city
                , CASE WHEN lead.district_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id', district.id,
                    'code', district.code,
                    'name', district.name
                    )::jsonb)) ELSE NULL END AS district
                , CASE WHEN lead.sub_district_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id', sub_district.id,
                    'code', sub_district.code,
                    'kode_pos', sub_district.zip_code,
                    'name', sub_district.name
                    )::jsonb)) ELSE NULL END AS sub_disctrict
                
                --QUESTIONAIRE
                , CASE WHEN lead.gender_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',gender.id,
                    'value',gender.value,
                    'name',gender.name
                )::jsonb)) ELSE NULL END AS gender_id
                , CASE WHEN lead.blood_type_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',blood_type.id,
                    'value',blood_type.value,
                    'name',blood_type.name
                )::jsonb)) ELSE NULL END AS gol_darah
                , CASE WHEN lead.religion_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',religion.id,
                    'value',religion.value,
                    'name',religion.name
                )::jsonb)) ELSE NULL END AS religion_id
                , CASE WHEN lead.education_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',education.id,
                    'value',education.value,
                    'name',education.name
                )::jsonb)) ELSE NULL END AS education_id
                , CASE WHEN lead.occupation_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',occupation.id,
                    'value',occupation.value,
                    'name',occupation.name
                )::jsonb)) ELSE NULL END AS occupation_id
                , CASE WHEN lead.expense_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',expense.id,
                    'value',expense.value,
                    'name',expense.name
                )::jsonb)) ELSE NULL END AS expense
                , CASE WHEN lead.income_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',income.id,
                    'value',income.value,
                    'name',income.name
                )::jsonb)) ELSE NULL END AS income_id
                , CASE WHEN lead.motor_brand_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',motor_brand.id,
                    'value',motor_brand.value,
                    'name',motor_brand.name
                )::jsonb)) ELSE NULL END AS motor_brand
                , CASE WHEN lead.motor_type_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',motor_type.id,
                    'value',motor_type.value,
                    'name',motor_type.name
                )::jsonb)) ELSE NULL END AS motor_type
                , CASE WHEN lead.hobby_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',hobby.id,
                    'value',hobby.value,
                    'name',hobby.name
                )::jsonb)) ELSE NULL END AS hobby_id
                , CASE WHEN lead.housing_tenure_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',housing_tenure.id,
                    'value',housing_tenure.value,
                    'name',housing_tenure.name
                )::jsonb)) ELSE NULL END AS housing_tenure_id
                , CASE WHEN lead.mobile_plan_status_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',mobile_plan_status.id,
                    'value',mobile_plan_status.value,
                    'name',mobile_plan_status.name
                )::jsonb)) ELSE NULL END AS mobile_plan_status_id
                , CASE WHEN lead.marital_status_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',marital_status.id,
                    'value',marital_status.value,
                    'name',marital_status.name
                )::jsonb)) ELSE NULL END AS marital_status_id
                , CASE WHEN lead.unit_operator_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',unit_operator.id,
                    'value',unit_operator.value,
                    'name',unit_operator.name
                )::jsonb)) ELSE NULL END AS unit_operator_id
                , CASE WHEN lead.motor_ownership_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',motor_ownership.id,
                    'value',motor_ownership.value,
                    'name',motor_ownership.name
                )::jsonb)) ELSE NULL END AS motor_ownership_id
                , CASE WHEN lead.unit_usage_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',unit_usage.id,
                    'value',unit_usage.value,
                    'name',unit_usage.name
                )::jsonb)) ELSE NULL END AS unit_usage_id
                , CASE WHEN lead.unit_availability_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',unit_availability.id,
                    'value',unit_availability.value,
                    'name',unit_availability.name
                )::jsonb)) ELSE NULL END AS unit_availability_id
                , CASE WHEN lead.payment_type_id IS NOT NULL THEN (json_agg(DISTINCT json_build_object(
                    'id',payment_type.id,
                    'value',payment_type.value,
                    'name',payment_type.name
                )::jsonb)) ELSE NULL END AS payment_type_id

                , (SELECT JSON_AGG(
                        JSONB_BUILD_OBJECT(
                            'ket', ts.name,
                            'url', %(url)s || '/web/content/tw.lead.documents/' || ld.id || '/document_show/' || ld.document_filename
                        )
                    ) AS docs
                FROM tw_lead l 
                LEFT JOIN tw_lead_documents ld on ld.lead_id = l.id
                LEFT JOIN tw_selection ts on ts.id = ld.document_type_id
                WHERE l.id = lead.id
                GROUP BY l.id)

            FROM tw_lead as lead
            LEFT JOIN tw_lead_activity as activity on activity.lead_id = lead.id
            LEFT JOIN tw_lead_activity as next_activity on next_activity.id = lead.next_activity_id
            LEFT JOIN crm_stage as stage on stage.id = next_activity.stage_id
            LEFT JOIN res_company as company on company.id = lead.company_id
            LEFT JOIN res_partner as finco on finco.id = lead.finco_id
            LEFT JOIN res_partner as partner_stnk on partner_stnk.id = lead.partner_stnk_id
            LEFT JOIN hr_employee as employee on employee.id = lead.sales_id
            LEFT JOIN hr_employee as sco on sco.id = lead.sales_coordinator_id
            LEFT JOIN stock_location as location on location.id = lead.source_location_id
            LEFT JOIN tw_master_act_type as act_type on act_type.id = lead.act_type_id

            --TITIK KERAMAIAN
            LEFT JOIN tw_activity_atl_btl_line as act_line on act_line.id = lead.activity_plan_id
            LEFT JOIN tw_mapping_titik_keramaian as mapping_tk on mapping_tk.id =  act_line.mapping_activity_id
            LEFT JOIN tw_titik_keramaian as titik_keramaian on titik_keramaian.id = mapping_tk.activity_point_id

            --street KTP
            LEFT JOIN res_country_state state ON state.id = lead.state_id
            LEFT JOIN res_city city ON city.id = lead.city_id
            LEFT JOIN res_district district ON district.id = lead.district_id
            LEFT JOIN res_sub_district sub_district ON sub_district.id = lead.sub_district_id

            --PRODUCT
            LEFT JOIN product_product product ON product.id = lead.product_id
            LEFT JOIN product_template as pt on pt.id = product.product_tmpl_id
            LEFT JOIN product_variant_combination as combination on combination.product_product_id = product.id
            LEFT JOIN product_template_attribute_value as ptav on ptav.id = combination.product_template_attribute_value_id
            LEFT JOIN product_attribute_value pav ON pav.id = ptav.product_attribute_value_id		
            
            --QUESTIONNAIRE
            LEFT JOIN tw_selection as interest on interest.id = lead.interest_id
            LEFT JOIN tw_selection as sales_channel on sales_channel.id = lead.sales_channel_id
            LEFT JOIN tw_selection as gender on gender.id = lead.gender_id
            LEFT JOIN tw_selection as blood_type on blood_type.id = lead.blood_type_id
            LEFT JOIN tw_selection as religion on religion.id = lead.religion_id
            LEFT JOIN tw_selection as education on education.id = lead.education_id
            LEFT JOIN tw_selection as occupation on occupation.id = lead.occupation_id
            LEFT JOIN tw_selection as expense on expense.id = lead.expense_id
            LEFT JOIN tw_selection as income on income.id = lead.income_id
            LEFT JOIN tw_selection as motor_brand on motor_brand.id = lead.motor_brand_id
            LEFT JOIN tw_selection as motor_type on motor_type.id = lead.motor_type_id
            LEFT JOIN tw_selection as hobby on hobby.id = lead.hobby_id
            LEFT JOIN tw_selection as housing_tenure on housing_tenure.id = lead.housing_tenure_id
            LEFT JOIN tw_selection as mobile_plan_status on mobile_plan_status.id = lead.mobile_plan_status_id
            LEFT JOIN tw_selection as unit_operator on unit_operator.id = lead.unit_operator_id
            LEFT JOIN tw_selection as motor_ownership on motor_ownership.id = lead.motor_ownership_id
            LEFT JOIN tw_selection as unit_usage on unit_usage.id = lead.unit_usage_id
            LEFT JOIN tw_selection as marital_status on marital_status.id = lead.marital_status_id
            LEFT JOIN tw_selection as unit_availability on unit_availability.id = lead.unit_availability_id
            LEFT JOIN tw_selection as payment_type on payment_type.id = lead.payment_type_id
            
            WHERE 1 = 1
            AND lead.id = %(lead_id)s
            GROUP BY lead.id,product.default_code,pt.name,pav.name,stage.id,next_activity.id,act_line.id,location.id,act_type.id
        """ 
        
        try:
            request.env.cr.execute(SQL(query_lead, **{
                'company_id': sales_id.company_id.id,
                'url': url,
                'lead_id': lead_id
            }))
            ress = request.env.cr.dictfetchone()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))

        return valid_response(200,ress)
    
    @http.route('/api/doodool/<version>/post_prospect', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_prospect(self, **kwargs):
        uid = request.session.uid
        post = json.loads(request.httprequest.get_data(as_text=True))
        sales_id = request.env['hr.employee'].sudo().search([('user_id','=',uid)],limit=1).id
        # TODO : Check SP Digital
        # check_sp_digital = request.env['tw.sp.digital'].sudo().search([('sales_id','=',sales_id),('state','=','confirmed'),('date','>=','2024-05-01')],limit=1)
        # if check_sp_digital:
        #     return {
        #             'error': 'error_create_prospect',
        #             'message':'Mohon Terima SP Digital (%s) terlebih dahulu' %(check_sp_digital.name),
        #             'status':0,
        #         }
        company_ids = request.env.user.company_ids
        company = company_ids[0]

        if not company:
            return invalid_response(400, 'Company not found', "User does not have access to any company or the provided company code was not found!")

        otr_fix = 0
        vals = {}

        mobile = post['mobile'].replace("-", "") if 'mobile' in post else False
        whatsapp = post['whatsapp'].replace("-", "") if 'whatsapp' in post else False
        finco = request.env['res.partner']
        if post.get('finco_id'):
            finco = finco.sudo().browse(int(post['finco_id']))

        otr = post.get('otr', False)
        if otr:
            otr = int(otr)

        product_id = post.get('product_id', False)
        if product_id:
            product_id = int(product_id)
            product = request.env['product.product'].sudo().browse(product_id)
            if product:
                pricelist = company.branch_setting_id.pricelist_sale_unit_id
                # TODO: create branch settings for link pricelist bbn to its branch
                # pricelist_bbn_hitam = branch.branch_setting_id.pricelist_jual_unit_bbn_hitam_id
                plate = request.env['tw.selection'].sudo().search([('value', '=', 'H'), ('type', '=', 'PlateType')])
                pricelist_bbn_hitam = request.env['product.pricelist']._get_bbn_sales_pricelist(company, plate)
                try:
                    unit_price = pricelist._price_get(product.product_tmpl_id, 1)[pricelist.id]
                    price_bbn = pricelist_bbn_hitam._price_get(product.product_tmpl_id, 1)[pricelist_bbn_hitam.id]
                except (RedirectWarning, Warning, ValidationError) as e:
                    return invalid_response(400, 'warning', str(e.args[0]))

                price = unit_price
                tax = False
                otrnya = False
                taxes = product.product_tmpl_id.taxes_id.compute_all(price,None, 1 ,product,None)
                if taxes.get('taxes', False):
                    tax = taxes['taxes'][0].get('amount', '')
                otrnya = taxes.get('total_excluded', 0)
                otr_fix = otrnya + price_bbn + tax
        
        activity_plan_id = post.get('activity_plan_id')
        if activity_plan_id:
            activity_plan_id = int(activity_plan_id)
        activity_point_id = post.get('activity_point_id')
        if activity_point_id:
            activity_point_id = int(activity_point_id)
        
        act_type_id = post.get('act_type_id', False)
        if act_type_id:
            act_type_id = int(act_type_id)
            
        sales_source_location_id = post.get('sales_source_location_id', False)
        if sales_source_location_id:
            sales_source_location_id = int(sales_source_location_id)
        
        phone = ""
        if 'phone' in post:
            phone = post['phone'].replace("-", "")
        
        sales_id_from_app = post.get('sales_id', False)
        if sales_id_from_app:
            emp = sales_id_from_app
        else:
            emp = sales_id
        
        street = post.get('street')
        rt = post.get('rt')
        rw = post.get('rw')
        state_id = post.get('state_id')
        city_id = post.get('kabupaten_id')
        district_id = post.get('kecamatan_id')
        sub_district_id = post.get('kelurahan_id')
        zip_code = post.get('kode_pos')

        identification_number = post.get('no_ktp', None)
        lead = request.env['tw.lead'].sudo().search([
            '|', 
            ('identification_number', '=', identification_number),
            ('mobile', '=', mobile),
            ('company_id', '=', company.id),
            ('state', '=', 'open')], limit=1)
        # Untuk COLD masih belum mandatory input KTP
        if lead:
            if identification_number == lead.identification_number:
                return invalid_response(400, 'lead_already_exists', f"Buku Tamu ({lead.name}) dengan Nomor KTP {identification_number} sudah ada di Dealer {company.name} dan masih dalam status open.")
            elif mobile == lead.mobile:
                return invalid_response(400, 'lead_already_exists', f"Buku Tamu ({lead.name}) dengan Nomor HP {mobile} sudah ada di Dealer {company.name} dan masih dalam status open.")
        
        current_motorcycle = post.get('current_motorcycle', False)
        motor_brand_id = False
        motor_type_id = False
        motor_ownership_id = False
        if current_motorcycle:
            if current_motorcycle == 'ada':
                motor_brand_id = post.get('motor_brand_id', False)
                motor_type_id = post.get('motor_type_id', False)
                motor_ownership_id = post.get('motor_ownership_id', False)
            elif current_motorcycle == 'tidak_ada':
                motor_brand_id = self.env.ref('tw_selection.selection_merk_mtr_blm').id
                motor_type_id = self.env.ref('tw_selection.selection_jns_mtr_blm').id
                motor_ownership_id = self.env.ref('tw_selection.selection_kepemilikan_mtr_sendiri').id
        
        selection = request.env['tw.selection']
        vals = {
            'customer_name': post['customer_name'],
            'mobile': mobile,
            'whatsapp': whatsapp,
            'phone': phone,
            'identification_number': identification_number,
            'identification_family_number': post.get('no_kk'),
            'birthplace': post.get('tempat_tgl_lahir'),
            'birthdate': post.get('tgl_lahir'),
            'company_id': company.id,
            'sales_id': emp,

            'street': street,
            'rt': rt,
            'rw': rw,
            'state_id': state_id,
            'city_id': city_id,
            'district_id': district_id,
            'sub_district_id': sub_district_id,
            'zip': zip_code,
            
            'current_motorcycle': current_motorcycle,
            'motor_brand_id': motor_brand_id,
            'motor_type_id': motor_type_id,
            'motor_ownership_id': motor_ownership_id,
            'down_payment': post.get('uang_muka'),
            'down_payment_date': post.get('tgl_uang_muka', date.today()),
            'tenor': post.get('tenor'),
            'installment': post.get('cicilan'),
            'price_otr': otr or otr_fix,
            'discount': post.get('discount'),
            'due_date': post.get('due_date'),
            
            'finco_id': finco.id,
            'product_id': product_id,
            'sales_source_location_id': sales_source_location_id,
            'act_type_id': act_type_id,
            'activity_plan_id': activity_plan_id,
            'activity_point_id': activity_point_id,
            'data_source_id': request.env.ref('tw_lead.tw_lead_data_source_apps').id,
            
            'email': post.get('email', None),
            'facebook': post.get('facebook', None),
            'instagram': post.get('instagram', None),
            'twitter': post.get('twitter', None),
            'youtube': post.get('youtube', None),
            'data_by': post.get('data_by', 'lead'),
            'version_code': post.get('version_code', None),
            'version_name': f'doodool {str(post.get("version_name", None))}',
            
            'interest_id': selection.validate_selection(post.get('interest_id'), 'Interest'),
            'gender_id': selection.validate_selection(post.get('gender_id'), 'Gender'),
            'blood_type_id': selection.validate_selection(post.get('blood_type_id'), 'BloodType'),
            'religion_id': selection.validate_selection(post.get('agama_id'), 'Religion'),
            'occupation_id': selection.validate_selection(post.get('pekerjaan_id'), 'Occupation'),
            'payment_type_id': selection.validate_selection(int(post.get('payment_type')), 'PaymentType') if post.get('payment_type') else False,
            'payment_type': selection.browse(int(post.get('payment_type'))).value if post.get('payment_type') else False,
            'sales_channel_id': selection.validate_selection(post.get('sales_channel_id'), 'SalesChannel'),
            'customer_grade_id': selection.validate_selection(post.get('customer_grade_id'), 'CustomerGrade'),
            'unit_availability_id': selection.sudo().search([('type', '=', 'UnitAvailibility'), ('value', '=', 'ready')], limit=1).id,
            'unit_availability': 'ready',
            'housing_tenure_id': selection.validate_selection(post.get('status_rumah_id'), 'HousingTenure'),
            'mobile_plan_status_id': selection.validate_selection(post.get('status_hp_id'), 'StatusMobilePhone'),
        }
        
        selection_vals = self._get_validated_selection_values(post)
        if 'status' in selection_vals and selection_vals['status'] == 0:
            return selection_vals

        vals.update(selection_vals)
        
        if post.get('followup_date') and post.get('action_follow_up_id'):
            followup_date = datetime.strptime(post.get('followup_date'), '%Y-%m-%d %H:%M:%S')
            # App mengirim followup_date dalam WIB (UTC+7).
            # Server Odoo berjalan di UTC, sehingga harus dikonversi dulu
            # sebelum dibandingkan. Nilai UTC ini juga langsung dipakai
            # untuk disimpan ke DB Odoo yang selalu menyimpan dalam UTC.
            followup_date_utc = followup_date - relativedelta(hours=7)
            if followup_date_utc < datetime.utcnow():
                return invalid_response(400, 'invalid_followup_date', f"Tanggal/jam follow-up ({followup_date.strftime('%Y-%m-%d %H:%M:%S')}) tidak boleh lebih awal dari sekarang ({(datetime.utcnow() + relativedelta(hours=7)).strftime('%Y-%m-%d %H:%M:%S')}).")
            followup_date_min_7 = str(followup_date_utc)
            vals['lead_activity_ids'] = [Command.create({
                'date': followup_date_min_7,
                'stage_id': int(post['action_follow_up_id'])
            })]

        if 'partner_stnk' in post:
            partner_data = post['partner_stnk']
            # TODO: apakah diperluka untuk pembuatan partner baru disini?
            # Karena sudah ada endpoint get_customer_stnk
            # partner_stnk_id = self._get_partner_id(partner_data)
            vals['partner_stnk_id'] = partner_data
        
        # Create Riwayat
        vals['log_ids'] = [Command.create({
            'lead_id': lead.id,
            'name': 'Create prospect',
            'date': datetime.now(),
            'category_id': request.env.ref('tw_lead.tw_lead_log_category_type_general').id,
        })]

        try:
            with request.env.cr.savepoint():
                lead = request.env['tw.lead'].sudo().create(vals)
                if lead.lead_activity_ids:
                    for activity in lead.lead_activity_ids:
                        activity.action_add_activity()
        except Warning as e:
            return invalid_response(400, 'warning', str(e.args[0]))
        except ValidationError as e:
            return invalid_response(400, 'validation_error', str(e.args[0]))
        except Exception as e:
            name = e.__class__.__name__
            module = e.__class__.__module__
            return invalid_response(500, f'{module}.{name}', str(e))
        
        if lead:
            return valid_response(200, { 'id': lead.id })
        else:
            return invalid_response(400, 'error_create_prospect', 'Not OK')

    @http.route('/api/doodool/<version>/post_prospect_edit', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_prospect_edit(self, **kwargs):
        crm_lead = request.env['tw.lead']

        post = json.loads(request.httprequest.get_data(as_text=True))
        company_ids = request.env.user.company_ids
        company = company_ids[0]
            
        if not company:
            return invalid_response(400, 'Company not found', "User does not have access to any company or the provided company code was not found!")
        
        # Check required fields in post
        required_keys = ['lead_id']  # add all required keys here
        if post.get('params'):
            post = post['params']
        is_valid, error_msg = validate_payload(post, required_keys)
        if not is_valid:
            return invalid_response(400, 'Missing mandatory fields', error_msg)
        
        lead_id = int(post['lead_id'])
        lead = crm_lead.search([('id', '=', lead_id)], limit=1)
        if not lead:
            return invalid_response(400, 'prospect_not_found', f"Prospect with Lead ID {lead_id} was not found or does not exist.")
            
        vals = {}
        state = request.env['res.country.state']
        city = request.env['res.city']
        district = request.env['res.district']
        sub_district = request.env['res.sub.district']

        street = post.get('street')
        rt = post.get('rt')
        rw = post.get('rw')
        state_id = post.get('state_id')
        city_id = post.get('kabupaten_id')
        district_id = post.get('kecamatan_id')
        sub_district_id = post.get('kelurahan_id')
        zip_code = post.get('kode_pos')
        is_same_ktp = post.get('is_sesuai_ktp')

        current_motorcycle = post.get('current_motorcycle', False)
        motor_brand_id = False
        motor_type_id = False
        motor_ownership_id = False
        if current_motorcycle:
            if current_motorcycle == 'ada':
                motor_brand_id = post.get('motor_brand_id', False)
                motor_type_id = post.get('motor_type_id', False)
                motor_ownership_id = post.get('motor_ownership_id', False)
            elif current_motorcycle == 'tidak_ada':
                motor_brand_id = self.env.ref('tw_selection.selection_merk_mtr_blm').id
                motor_type_id = self.env.ref('tw_selection.selection_jns_mtr_blm').id
                motor_ownership_id = self.env.ref('tw_selection.selection_kepemilikan_mtr_sendiri').id

        if current_motorcycle:
            vals['current_motorcycle'] = current_motorcycle
            vals['motor_brand_id'] = motor_brand_id
            vals['motor_type_id'] = motor_type_id
            vals['motor_ownership_id'] = motor_ownership_id
        
        if street:
            vals['street'] = street
        if rt:
            vals['rt'] = str(rt)
        if rw:
            vals['rw'] = str(rw)
        if state_id:
            vals['state_id'] = int(state_id) if state_id else False
        if city_id:
            vals['city_id'] = int(city_id) if city_id else False
        if district_id:
            vals['district_id'] = int(district_id) if district_id else False
        if sub_district_id:
            vals['sub_district_id'] = int(sub_district_id) if sub_district_id else False
        if zip_code:
            vals['zip'] = str(zip_code)
        if is_same_ktp is not None:
            vals['is_same_ktp'] = is_same_ktp
            if street:
                vals['street_domicile'] = street
            if rt:
                vals['rt_domicile'] = str(rt)
            if rw:
                vals['rw_domicile'] = str(rw)
            if state_id:
                vals['state_domicile_id'] = int(state_id) if state_id else False
            if city_id:
                vals['city_domicile_id'] = int(city_id) if city_id else False
            if district_id:
                vals['district_domicile_id'] = int(district_id) if district_id else False
            if sub_district_id:
                vals['sub_district_domicile_id'] = int(sub_district_id) if sub_district_id else False
            if zip_code:
                vals['zip_domicile'] = str(zip_code)
        else:
            if 'street_domisili' in post:
                vals['street_domicile'] = post['street_domisili']
            if 'rt_domisili' in post:
                vals['rt_domicile'] = str(post['rt_domisili'])
            if 'rw_domisili' in post:
                vals['rw_domicile'] = str(post['rw_domisili'])
            if 'provinsi_domisili_id' in post:
                vals['state_domicile_id'] = int(post['provinsi_domisili_id']) if post['provinsi_domisili_id'] else False
            if 'kabupaten_domisili_id' in post:
                vals['city_domicile_id'] = int(post['kabupaten_domisili_id']) if post['kabupaten_domisili_id'] else False
            if 'kecamatan_domisili_id' in post:
                vals['district_domicile_id'] = int(post['kecamatan_domisili_id']) if post['kecamatan_domisili_id'] else False
            if 'kelurahan_domisili_id' in post:
                vals['sub_district_domicile_id'] = int(post['kelurahan_domisili_id']) if post['kelurahan_domisili_id'] else False
            if 'kode_pos_domisili' in post:
                vals['zip_domicile'] = str(post['kode_pos_domisili'])
            
        if post.get('finco_id'):
            vals['finco_id'] = int(post['finco_id'])

        if 'sales_coordinator_id' in post:
            vals['sales_coordinator_id'] = post['sales_coordinator_id']
        if 'relative_phone_number' in post:
            vals['relative_phone_number'] = post['relative_phone_number']
        if 'name_customer' in post:
            vals['customer_name'] = post['name_customer']
        if 'mobile' in post:
            mobile = post['mobile'].replace('-', '')
            vals['mobile'] = mobile
        if 'whatsapp' in post:
            whatsapp = post['whatsapp'].replace("-", "")
            vals['whatsapp'] = whatsapp
        if 'no_ktp' in post:
            vals['identification_number'] = post['no_ktp']
        if 'no_kk' in post:
            vals['identification_family_number'] = post['no_kk']
        if 'tempat_tgl_lahir' in post:
            vals['birthplace'] = post['tempat_tgl_lahir']
        if 'tgl_lahir' in post:
            vals['birthdate'] = post['tgl_lahir']
        if 'position' in post:
            vals['position'] = post['position']

        selection_vals = self._get_validated_selection_values(post)
        if 'status' in selection_vals and selection_vals['status'] == 0:
            return selection_vals
        vals.update(selection_vals)
        
        if 'product_id' in post:
            product_id = int(post['product_id'])
            vals['product_id'] = product_id
            product = request.env['product.product'].sudo().browse(product_id)
            if product:
                pricelist = company.branch_setting_id.pricelist_sale_unit_id
                # TODO: create branch settings for link pricelist bbn to its branch
                # pricelist_bbn_hitam = branch.branch_setting_id.pricelist_jual_unit_bbn_hitam_id
                plate = request.env['tw.selection'].search([('value', '=', 'H'), ('type', '=', 'PlateType')])
                pricelist_bbn_hitam = request.env['product.pricelist']._get_bbn_sales_pricelist(company, plate)
                try:
                    unit_price = pricelist._price_get(product.product_tmpl_id, 1)[pricelist.id]
                    price_bbn = pricelist_bbn_hitam._price_get(product.product_tmpl_id, 1)[pricelist_bbn_hitam.id]
                except (RedirectWarning, Warning, ValidationError) as e:
                    return invalid_response(400, 'warning', str(e.args[0]))

                price = unit_price
                tax = False
                otrnya = False
                taxes = product.product_tmpl_id.taxes_id.compute_all(price,None, 1 ,product,None)
                if taxes.get('taxes', False):
                    tax = taxes['taxes'][0].get('amount', '')
                otrnya = taxes.get('total_excluded', 0)
                otr_fix = otrnya + price_bbn + tax

        if 'ethnicity' in post:
            vals['ethnicity'] = post['ethnicity']
        # Support both app key 'current_motorcycle_status' and model key 'current_motorcycle'
        if 'current_motorcycle_status' in post:
            vals['current_motorcycle'] = post['current_motorcycle_status']
        elif 'current_motorcycle' in post:
            vals['current_motorcycle'] = post['current_motorcycle']
        if 'phone' in post:
            phone = post['phone'].replace('-', '')
            vals['phone'] = phone
            
        if 'finco_id' in post:
            vals['finco_id'] = int(post['finco_id']) if post['finco_id'] else False
        # Support both app key 'uang_muka' and model key 'down_payment'
        if 'uang_muka' in post:
            vals['down_payment'] = post['uang_muka']
        elif 'down_payment' in post:
            vals['down_payment'] = post['down_payment']
        if 'tgl_uang_muka' in post:
            vals['down_payment_date'] = post.get('tgl_uang_muka', date.today())
        if 'tenor' in post:
            vals['tenor'] = post['tenor']
        # Support both app key 'cicilan' and model key 'installment'
        if 'cicilan' in post:
            vals['installment'] = post['cicilan']
        elif 'installment' in post:
            vals['installment'] = post['installment']
        # Support both app key 'otr' and model key 'price_otr'
        if 'otr' in post:
            vals['price_otr'] = post['otr'] or otr_fix
        elif 'price_otr' in post:
            vals['price_otr'] = post['price_otr'] or otr_fix
        # Support both app key 'diskon' and model key 'discount'
        if 'diskon' in post:
            vals['discount'] = post['diskon']
        elif 'discount' in post:
            vals['discount'] = post['discount']

        if 'warna' in post:
            # Removed incorrect mapping to 'color' field which is an Integer in crm.lead
            pass

        # Handle is_sesuai_ktp (app sends list ["Benar"] or null)
        if 'is_sesuai_ktp' in post:
            is_same = post['is_sesuai_ktp']
            vals['is_same_ktp'] = isinstance(is_same, list) and 'Benar' in is_same

        # # Domicile address fields
        # if 'street_domisili' in post:
        #     vals['street_domicile'] = post['street_domisili']
        # if 'rt_domisili' in post:
        #     vals['rt_domicile'] = str(post['rt_domisili'])
        # if 'rw_domisili' in post:
        #     vals['rw_domicile'] = str(post['rw_domisili'])
        # if 'state_domisili_id' in post:
        #     vals['state_domicile_id'] = post['state_domisili_id']
        # if 'kabupaten_domisili_id' in post:
        #     vals['city_domicile_id'] = post['kabupaten_domisili_id']
        # if 'kecamatan_domisili_id' in post:
        #     vals['district_domicile_id'] = post['kecamatan_domisili_id']
        # if 'kelurahan_domisili_id' in post:
        #     vals['sub_district_domicile_id'] = post['kelurahan_domisili_id']
        # if 'kode_pos_domisili' in post:
        #     vals['zip_domicile'] = str(post['kode_pos_domisili'])
        # Support atas_nama_stnk
        
        if 'email' in post:
            vals['email'] = post['email']
        if 'facebook' in post:
            vals['facebook'] = post['facebook']
        if 'instagram' in post:
            vals['instagram'] = post['instagram']
        if 'twitter' in post:
            vals['twitter'] = post['twitter']
        if 'youtube' in post:
            vals['youtube'] = post['youtube']

        if 'due_date' in post:
            vals['due_date'] = post['due_date']

        if 'act_type_id' in post:
            act_type_id = int(post['act_type_id']) if post['act_type_id'] else False
            vals['act_type_id'] = act_type_id
        if 'activity_plan_id' in post:
            activity_plan_id = int(post['activity_plan_id']) if post['activity_plan_id'] else False
            vals['activity_plan_id'] = activity_plan_id
        if 'activity_point_id' in post:
            activity_point_id = int(post['activity_point_id']) if post['activity_point_id'] else False
            vals['activity_point_id'] = activity_point_id
        if 'sales_source_location_id' in post:
            sales_source_location_id = int(post['sales_source_location_id']) if post['sales_source_location_id'] else False
            vals['sales_source_location_id'] = sales_source_location_id

        followup_date = post.get('followup_date')
        action_follow_id = post.get('action_follow_up_id')
        if followup_date and action_follow_id:
            if not lead.next_activity_id.activity_result_id:
                return invalid_response(400, 'error_create_activity', 'Follow up masih ada yang outstanding, tidak bisa create activity baru !')
            followup_date_min_7 = str(datetime.strptime(post.get('followup_date'), '%Y-%m-%d %H:%M:%S') - relativedelta(hours=7))
            vals['lead_activity_ids'] = [Command.create({
                'date': followup_date_min_7,
                'name': int(action_follow_id),
            })]
        
        if 'partner_stnk' in post:
            partner_data = post['partner_stnk']
            # TODO: apakah diperluka untuk pembuatan partner baru disini?
            # Karena sudah ada endpoint get_customer_stnk
            # partner_stnk_id = self._get_partner_id(partner_data)
            vals['partner_stnk_id'] = partner_data

        # Log the changes
        vals['log_ids'] = [Command.create({
            'name': 'Updating prospect data',
            'date': datetime.now(),
            'category_id': request.env.ref('tw_lead.tw_lead_log_category_type_general').id
        })]

        try:
            with request.env.cr.savepoint():
                lead.sudo().write(vals)
                request.env.flush_all()
        except (Warning, ValidationError) as e:
            error_msg = e.args[0] if hasattr(e, 'args') and e.args else str(e)
            return invalid_response(400, e.__class__.__name__, error_msg)
        except Exception as e:
            _logger.error(traceback.format_exc())
            error_msg = e.args[0] if hasattr(e, 'args') and e.args else str(e)
            return invalid_response(500, e.__class__.__name__, error_msg)
                
        if post.get('is_deal'):
            # Iterate through all activities as per the standard CRM UI flow
            if lead.lead_activity_ids:
                for activity in lead.lead_activity_ids:
                    if not activity.activity_result_id:
                        return invalid_response(
                            400, 
                            'error_deal', 
                            f"Please fill in the Follow-Up Result for the date {activity.date}, the data is still empty"
                        )
            lead.sudo().action_deal()

        message = 'Success Edit Prospect' if not post.get('is_deal') else 'Success dealing prospect'
        return valid_response(200, {'id': lead.id}, message)
    
    @http.route('/api/doodool/<version>/post_propose_prospect', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_propose_prospect(self, **kwargs):
        uid = request.session.uid
        crm_lead = request.env['tw.lead']
        selection = request.env['tw.selection']

        post = json.loads(request.httprequest.get_data(as_text=True))
        company_ids = request.env.user.company_ids
        company = company_ids[0]

        if not company:
            return invalid_response(400, 'Company not found', "User does not have access to any company or the provided company code was not found!")
        # Check required fields in post
        required_keys = ['lead_id']  # add all required keys here
        is_valid, error_msg = validate_payload(post, required_keys)
        if not is_valid:
            return invalid_response(400, 'Missing mandatory fields', error_msg)
    
        lead_id = int(post['lead_id'])
        lead = crm_lead.search([('id', '=', lead_id)], limit=1)
        vals = {}
        if not lead:
            return invalid_response(400, 'prospect_not_found', f"Prospect with Lead ID {lead_id} was not found or does not exist.")

        if lead.state != 'dealt':
            vals = {}

        if 'partner_stnk' in post:
            partner_data = post['partner_stnk']
            # TODO: apakah diperluka untuk pembuatan partner baru disini?
            # Karena sudah ada endpoint get_customer_stnk
            # partner_stnk_id = self._get_partner_id(partner_data)
            vals['partner_stnk_id'] = partner_data
            
        # TODO: activate if any mediator module is already developed
        # if 'is_hc' in post:
        #     vals['is_hc'] = post['is_hc']
        # if 'discount_hc' in post:
        #     vals['discount_hc'] = post['discount_hc']
        current_motorcycle = post.get('current_motorcycle', False)
        if current_motorcycle:
            if current_motorcycle == 'ada':
                motor_brand_id = post.get('motor_brand_id', False)
                motor_type_id = post.get('motor_type_id', False)
                motor_ownership_id = post.get('motor_ownership_id', False)
            elif current_motorcycle == 'tidak_ada':
                motor_brand_id = self.env.ref('tw_selection.selection_merk_mtr_blm').id
                motor_type_id = self.env.ref('tw_selection.selection_jns_mtr_blm').id
                motor_ownership_id = self.env.ref('tw_selection.selection_kepemilikan_mtr_sendiri').id
        
        if current_motorcycle:
            vals['current_motorcycle'] = current_motorcycle
            vals['motor_brand_id'] = motor_brand_id
            vals['motor_type_id'] = motor_type_id
            vals['motor_ownership_id'] = motor_ownership_id

        if 'down_payment' in post:
            vals['down_payment'] = post['down_payment']
        elif 'uang_muka' in post:
            vals['down_payment'] = post['uang_muka']
        if 'discount' in post:
            vals['discount'] = post['discount']
        # if 'no_po' in post:
        #     vals['no_po'] = post['no_po']
        if 'unit_availability_id' in post:
            vals['unit_availability_id'] = selection.validate_selection(post.get('unit_availability_id'), 'UnitAvailibility'),
        else:
            if not lead.unit_availability_id:
                vals['unit_availability_id'] = request.env.ref('tw_lead.tw_lead_unit_availability_ready').id
                
        if 'no_kk' in post:
            vals['identification_family_number'] = post['no_kk']
        if 'sales_coordinator_id' in post:
            vals['sales_coordinator_id'] = post['sales_coordinator_id']
        if 'motor_ownership_id' in post:
            vals['motor_ownership_id'] = selection.validate_selection(int(post['motor_ownership_id']), 'MotorOwnership')


        try:
            with request.env.cr.savepoint():
                lead.write(vals)
                lead.sudo().action_propose()
                request.env.flush_all()
        except (Warning, ValidationError) as e:
            error_msg = e.args[0] if hasattr(e, 'args') and e.args else str(e)
            return invalid_response(400, e.__class__.__name__, error_msg)
        except Exception as e:
            _logger.error(traceback.format_exc())
            error_msg = e.args[0] if hasattr(e, 'args') and e.args else str(e)
            return invalid_response(500, e.__class__.__name__, error_msg)

        return valid_response(200, {'id': lead.id}, 'Success')

    @http.route('/api/doodool/<version>/post_proposed_prospect_reject', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_proposed_prospect_reject(self, **post):
        crm_lead = request.env['tw.lead']

        post = json.loads(request.httprequest.get_data(as_text=True))
        company_ids = request.env.user.company_ids
        company = company_ids[0]

        if not company:
            return invalid_response(401, 'company_not_found', 'User does not have access to any company or the provided company code was not found!')
        # Check required fields in post
        required_keys = ['lead_id']  # add all required keys here
        is_valid, error_msg = validate_payload(post, required_keys)
        if not is_valid:
            return invalid_response(400, 'Missing mandatory fields', error_msg)
    
        lead_id = int(post['lead_id'])
        lead = crm_lead.search([('id', '=', lead_id)], limit=1)
        if not lead:
            return invalid_response(404, 'prospect_not_found', f"Prospect with Lead ID {lead_id} was not found or does not exist.")
        
        try:
            with request.env.cr.savepoint():
                lead.with_context(rejection_reason=rejection_reason).action_reject()
                request.env.flush_all()
        except (Warning, ValidationError) as e:
            error_msg = e.args[0] if hasattr(e, 'args') and e.args else str(e)
            return invalid_response(400, e.__class__.__name__, error_msg)
        except Exception as e:
            _logger.error(traceback.format_exc())
            error_msg = e.args[0] if hasattr(e, 'args') and e.args else str(e)
            return invalid_response(500, e.__class__.__name__, error_msg)

        data = { 'id': lead.id }
        return valid_response(200, 'Data has been successfully rejected', data)

    @http.route('/api/doodool/<version>/post_document_prospect', methods=['POST'], type='http', auth='none', csrf=False)
    @check_valid_token
    def post_document_prospect(self, **kwargs):
        crm_lead = request.env['tw.lead']

        post = request.params
        company_ids = request.env.user.company_ids
        company = company_ids[0]

        if not company:
            error = 'company_not_found'
            message = "User does not have access to any company or the provided company code was not found!"
            return invalid_response(400, error, message)
        # Check required fields in post
        required_keys = ['lead_id', 'documents']  # add all required keys here
        is_valid, error_msg = validate_payload(post, required_keys)
        if not is_valid:
            return invalid_response(400, 'Missing mandatory fields', error_msg)

    
        lead_id = int(post['lead_id'])
        lead = crm_lead.sudo().search([('id', '=', lead_id)], limit=1)
        if not lead:
            error = 'prospect_not_found'
            message = f"Prospect with Lead ID {lead_id} was not found or does not exist."
            return invalid_response(400, error, message)
        
        document_ids = []
        documents = request.httprequest.files.getlist('documents')

        MAX_FILE_SIZE_BYTES = 500 * 1024  # 500KB

        for document in documents:
            document_file = document  # This is a FileStorage object
            document_type = document.filename.split('.')[0]

            # Preemptive file size check (500KB limit)
            file_data = document_file.read()
            if len(file_data) > MAX_FILE_SIZE_BYTES:
                file_size_kb = len(file_data) / 1024
                error = 'file_too_large'
                message = (
                    f"File '{document_file.filename}' berukuran {file_size_kb:.1f} KB, "
                    f"melebihi batas maksimal 500 KB. Silakan kompres atau gunakan file yang lebih kecil."
                )
                return invalid_response(400, error, message)
            document_file.seek(0)  # Reset pointer after read

            document_type_id = request.env['tw.selection'].search([
                ('value', '=', document_type), ('type', '=', 'DocumentType')], limit=1)

            if not document_type_id:
                error = 'document_type_missing'
                message = f'Document Type {document_type} is not found. Please Contact Support.'
                return invalid_response(400, error, message)

            doc_vals = {
                'document_filename': document_file.filename,
                'document_file': base64.b64encode(document_file.read()),
                'document_type_id': document_type_id.id
            }

            # update or create
            lead_document = lead.document_ids.filtered(lambda x: x.document_type_id.id == document_type_id.id)
            if lead_document:
                document_ids.append(Command.update(lead_document.id, doc_vals))
            else:
                document_ids.append(Command.create(doc_vals))

        if document_ids:
            try:
                lead.sudo().write({'document_ids': document_ids})
            except (Warning, ValidationError) as e:
                return invalid_response(400, 'document_validation_error', str(e.args[0]))
            except Exception as e:
                error = 'document_write_error'
                message = f'Failed to write document for Lead ID {lead_id}. Please Contact Support.'
                return invalid_response(400, error, message)

        return valid_response(200, { 'id': lead.id })

    @http.route('/api/doodool/<version>/new_order/add', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def lead_new_order(self, **post):
        """
        Create Lead from Doodool (Buku Tamu).
        Migrated from Odoo 8 rest_api endpoint.
        
        Expected payload:
        {
            "lead": { ... lead data ... },
            "activity": [ ... activity list ... ]
        }
        """
        post = json.loads(request.httprequest.get_data(as_text=True))
        errors = []
        data_lead = post.get('lead', {})
        data_activity = post.get('activity', [])
        
        if not data_lead:
            return invalid_response(400, 'missing_lead_data', 'Lead data is required body request')
        
        # ================================
        # VALIDATE BRANCH
        # ================================
        branch_code = data_lead.get('branch_code')
        company = request.env['res.company'].sudo().search([('code', '=', branch_code)], limit=1)
        if not company:
            errors.append(f"Branch Code {branch_code} not found")
        
        # ================================
        # VALIDATE PRODUCT
        # ================================
        prod_code = data_lead.get('prod_code')
        warna_code = data_lead.get('warna_code')
        product = False
        gp_total = 0
        
        if prod_code and warna_code:
            # Use existing method from product.product model
            product_model = request.env['product.product'].sudo()
            product_id = product_model._get_unit_product_id(prod_code, warna_code)
            
            if product_id:
                product = product_model.browse(product_id)
            else:
                errors.append(f"Product Code {prod_code} & Warna Code {warna_code} not found")
        
        # ================================
        # VALIDATE SALESMAN
        # ================================
        tunas_id = data_lead.get('tunas_id')
        nip_sales = data_lead.get('nip_sales')
        identification_id = data_lead.get('identification_id')
        nama_sales = data_lead.get('nama_sales')
        employee = False
        
        if not identification_id and not tunas_id and not nip_sales:
            errors.append("Data Salesman belum di setting (Tunas ID, No KTP, NIP)!")
        else:
            emp_domain = [('working_end_date', '=', False)]
            if tunas_id:
                emp_domain.append(('atpm_id', '=', tunas_id))
            elif identification_id:
                emp_domain.append(('identification_id', '=', identification_id))
            elif nip_sales:
                emp_domain.append(('registry_number', '=', nip_sales))
            
            employee = request.env['hr.employee'].sudo().search(emp_domain, limit=1)
            if not employee:
                errors.append(f"Sales A/n {nama_sales} belum di mapping di system!")
            elif not employee.user_id:
                errors.append(f"Sales A/n {nama_sales} tidak memiliki Data User di system!")
        
        # ================================
        # VALIDATE SALES COORDINATOR (Optional)
        # ================================
        sco_tunas_id = data_lead.get('sco_tunas_id')
        sco_nip = data_lead.get('sco_nip')
        sco_identification_id = data_lead.get('sco_identification')
        nama_sco = data_lead.get('nama_sco')
        sales_coordinator = False
        
        if sco_tunas_id or sco_nip or sco_identification_id:
            sco_domain = [('working_end_date', '=', False)]
            if sco_tunas_id:
                sco_domain.append(('atpm_id', '=', sco_tunas_id))
            elif sco_identification_id:
                sco_domain.append(('identification_id', '=', sco_identification_id))
            elif sco_nip:
                sco_domain.append(('nip', '=', sco_nip))
            
            sales_coordinator = request.env['hr.employee'].sudo().search(sco_domain, limit=1)
            if not sales_coordinator:
                errors.append(f"Sales Koordinator A/n {nama_sco} belum di mapping di system!")
        
        # ================================
        # VALIDATE FINCO (Optional)
        # ================================
        finco = False
        finco_code = data_lead.get('finco')
        if finco_code:
            finco = request.env['res.partner'].sudo().search([
                ('code', '=', finco_code),
                ('company_type','=','company'),
                ('category_id.name','=','Finance Company')
            ], limit=1)
        
        # ================================
        # Return errors if any
        # ================================
        if errors:
            return invalid_response(400, 'validation_error', '\n'.join(errors))
        
        # ================================
        # PREPARE ADDRESS DATA
        # ================================
        sub_district_model = request.env['res.sub.district'].sudo()
        district_model = request.env['res.district'].sudo()
        city_model = request.env['res.city'].sudo()
        state_model = request.env['res.country.state'].sudo()
        
        def get_address_ids(kel_code, kec_code, city_code, state_code):
            """Helper to resolve address hierarchy from codes"""
            state_id = city_id = district_id = sub_district_id = False
            
            if kel_code:
                sub_district = sub_district_model.search([('code', '=', kel_code)], limit=1)
                if sub_district:
                    sub_district_id = sub_district.id
                    district_id = sub_district.district_id.id
                    city_id = sub_district.district_id.city_id.id
                    state_id = sub_district.district_id.city_id.state_id.id
            
            if not district_id and kec_code:
                district = district_model.search([('code', '=', kec_code)], limit=1)
                if district:
                    district_id = district.id
                    city_id = district.city_id.id
                    state_id = district.city_id.state_id.id
            
            if not city_id and city_code:
                city = city_model.search([('code', '=', city_code)], limit=1)
                if city:
                    city_id = city.id
                    state_id = city.state_id.id
            
            if not state_id and state_code:
                state = state_model.search([('code', '=', state_code)], limit=1)
                if state:
                    state_id = state.id
            
            return state_id, city_id, district_id, sub_district_id
        
        # Get KTP Address
        state_id, city_id, district_id, sub_district_id = get_address_ids(
            data_lead.get('kel_code'),
            data_lead.get('kec_code'),
            data_lead.get('city_code'),
            data_lead.get('state_code')
        )
        
        # Get Domisili Address (if different)
        state_domisili_id = city_domisili_id = district_domisili_id = sub_district_domisili_id = False
        if not data_lead.get('is_sesuai_ktp'):
            state_domisili_id, city_domisili_id, district_domisili_id, sub_district_domisili_id = get_address_ids(
                data_lead.get('kel_code_domisili'),
                data_lead.get('kec_code_domisili'),
                data_lead.get('city_code_domisili'),
                data_lead.get('state_code_domisili')
            )
        
        # ================================
        # PREPARE SELECTION VALUES
        # ================================
        selection_model = request.env['tw.selection'].sudo()
        
        def get_selection_id(sel_type, value):
            """Helper to get selection ID"""
            if not value:
                return False
            sel = selection_model.search([('type', '=', sel_type), ('value', '=', value)], limit=1)
            return sel.id if sel else False
        
        gender_id = get_selection_id('Gender', data_lead.get('jk'))
        religion_id = get_selection_id('Religion', data_lead.get('agama'))
        blood_type_id = get_selection_id('BloodType', data_lead.get('gol_darah'))
        occupation_id = get_selection_id('Occupation', data_lead.get('pekerjaan'))
        expense_id = get_selection_id('Expense', data_lead.get('pengeluaran'))
        education_id = get_selection_id('Education', data_lead.get('pendidikan'))
        motor_brand_id = get_selection_id('MotorBrand', data_lead.get('merkmotor'))
        motor_type_id = get_selection_id('MotorType', data_lead.get('jenismotor'))
        unit_usage_id = get_selection_id('MotorUtilization', data_lead.get('penggunaan'))
        unit_operator_id = get_selection_id('MotorUser', data_lead.get('pengguna'))
        hobby_id = get_selection_id('Hobby', data_lead.get('hobi'))
        mobile_plan_status_id = get_selection_id('StatusMobilePhone', data_lead.get('status_hp'))
        housing_tenure_id = get_selection_id('HousingTenure', data_lead.get('status_rumah'))
        
        # ================================
        # PREPARE LEAD VALUES
        # ================================
        lead_vals = {
            'company_id': company.id,
            'customer_name': data_lead.get('name_customer'),
            'interest': data_lead.get('minat'),
            'product_id': product.id if product else False,
            'identification_number': data_lead.get('no_ktp'),
            'mobile': data_lead.get('mobile'),
            'phone': data_lead.get('kontak_tambahan'),
            'sales_id': employee.id if employee else False,
            'unique_code': data_lead.get('unique_code', False),
            'source_document': data_lead.get('source_document'),
            
            # Address KTP
            'street': data_lead.get('street'),
            'rt': data_lead.get('rt'),
            'rw': data_lead.get('rw'),
            
            # Domisili
            'is_same_ktp': data_lead.get('is_sesuai_ktp', False),
            
            # Personal Info
            'birthplace': data_lead.get('tempat_tgl_lahir'),
            'birthdate': data_lead.get('tgl_lahir'),
            'identification_family_number': data_lead.get('no_kk'),
            
            # Payment
            'payment_type': data_lead.get('payment_type'),
            'finco_id': finco.id if finco else False,
            'down_payment': data_lead.get('uang_muka'),
            'down_payment_date': data_lead.get('tgl_uang_muka', date.today()),
            'due_date': data_lead.get('date_jatuh_tempo'),
            'tenor': data_lead.get('tenor'),
            'installment': data_lead.get('cicilan'),
            'price_otr': data_lead.get('otr'),
            'discount': data_lead.get('diskon'),
            
            # Social Media
            'email': data_lead.get('email'),
            'facebook': data_lead.get('facebook'),
            'instagram': data_lead.get('instagram'),
            'twitter': data_lead.get('twitter'),
            'youtube': data_lead.get('youtube'),
            'whatsapp': data_lead.get('no_wa'),
            
            # Questionnaire / Selections
            'gender_id': gender_id,
            'religion_id': religion_id,
            'blood_type_id': blood_type_id,
            'occupation_id': occupation_id,
            'expense_id': expense_id,
            'education_id': education_id,
            'motor_brand_id': motor_brand_id,
            'motor_type_id': motor_type_id,
            'unit_usage_id': unit_usage_id,
            'unit_operator_id': unit_operator_id,
            'hobby_id': hobby_id,
            'mobile_plan_status_id': mobile_plan_status_id,
            'housing_tenure_id': housing_tenure_id,
            
            # Sales Coordinator
            'sales_coordinator_id': sales_coordinator.id if sales_coordinator else False,
            
            # Additional fields
            'version_code': data_lead.get('version_code'),
            'version_name': data_lead.get('version_name'),
            'data_by': 'lead',
        }
        
        # ================================
        # CHECK EXISTING LEAD
        # ================================
        lead_model = request.env['tw.lead'].sudo()
        existing_lead = lead_model.search([
            ('company_id', '=', company.id),
            ('identification_number', '=', data_lead.get('no_ktp')),
            ('product_id', '=', product.id if product else False),
            ('state', '!=', 'cancel')
        ], limit=1)
        
        if existing_lead:
            lead = existing_lead
        else:
            try:
                with request.env.cr.savepoint():
                    lead = lead_model.create(lead_vals)
                    # Auto deal if branch allows
                    if company.is_allow_lead:
                        lead.action_deal()
                    request.env.flush_all()
            except (Warning, ValidationError) as e:
                error_msg = e.args[0] if hasattr(e, 'args') and e.args else str(e)
                return invalid_response(400, e.__class__.__name__, error_msg)
            except Exception as e:
                _logger.error(traceback.format_exc())
                return invalid_response(500, e.__class__.__name__, str(e))
        
        # ================================
        # CREATE ACTIVITY FOLLOWUP
        # ================================
        lead_activity_model = request.env['tw.lead.activity'].sudo()
        stage_model = request.env['crm.stage'].sudo()
        activity_result_model = request.env['tw.lead.activity.result'].sudo()
        
        for act in data_activity:
            stage = stage_model.search([('name', 'ilike', act.get('stage'))], limit=1)
            result = activity_result_model.search([('name', 'ilike', act.get('result'))], limit=1)
            
            try:
                with request.env.cr.savepoint():
                    lead_activity_model.create({
                        'lead_id': lead.id,
                        'stage_id': stage.id if stage else False,
                        'activity_result_id': result.id if result else False,
                        'date': act.get('date'),
                        'remark': act.get('remark'),
                        'interest': act.get('minat'),
                    })
                    request.env.flush_all()
            except (Warning, ValidationError) as e:
                error_msg = e.args[0] if hasattr(e, 'args') and e.args else str(e)
                return invalid_response(400, e.__class__.__name__, error_msg)
            except Exception as e:
                _logger.error(traceback.format_exc())
                return invalid_response(500, e.__class__.__name__, str(e))
        
        # ================================
        # RETURN SUCCESS
        # ================================
        data = {
            'lead_id': lead.id,
            'name': lead.name,
            'gp_total': gp_total
        }
        return valid_response(200, data, 'Lead created successfully')