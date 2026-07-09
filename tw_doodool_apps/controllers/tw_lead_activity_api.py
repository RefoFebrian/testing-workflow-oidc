#-*- coding: utf-8 -*-

# 1: imports of python lib
import functools
import werkzeug.wrappers
import json
import logging
import traceback

_logger = logging.getLogger(__name__)
from datetime import timedelta,datetime as dt,date
from dateutil.relativedelta import relativedelta
# 2: import of known third party lib
from odoo.addons.tw_api.controllers.main import invalid_response, valid_response 
from odoo.addons.rest_api.controllers.main import check_valid_token, validate_payload
# 3:  imports of odoo
import odoo
from odoo import models, fields, api, _, http, Command

# 4:  imports from odoo modules
from odoo.http import request, Response
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.tools import SQL

# 5: local imports

# 6: Import of unknown third party lib


class ControllerREST(http.Controller):
    @http.route('/api/doodool/<version>/post_prospect_activity', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_prospect_activity(self, version, **kwargs):
        post = json.loads(request.httprequest.get_data(as_text=True))
        
        # Check required fields in post
        required_keys = ['date', 'lead_id', 'action_follow_id']  # add all required keys here
        list_not_req = [key for key in required_keys if key not in post]
        if len(list_not_req) > 0:
            return invalid_response(401, 'required_field', f"Missing key(s): {', '.join(list_not_req)} in the provided payload!")

        date = str(dt.strptime(post['date'], '%Y-%m-%d %H:%M:%S') - relativedelta(hours=7))
        stage_id = int(post['action_follow_id'])
        lead_id = int(post['lead_id'])

        lead = request.env['tw.lead'].sudo().browse(lead_id)
        if not lead:
            return invalid_response(404, 'prospect_not_found', f"Prospect with Lead ID {lead_id} was not found or does not exist.")
        
        try:
            with request.env.cr.savepoint():
                # IF there is next_activity_id on lead
                if lead.next_activity_id:
                    interest_id = int(post['interest_id']) if 'interest_id' in post else lead.interest_id.id
                    # IF next_activity_id already has result
                    if lead.next_activity_id.activity_result_id:
                        create = request.env['tw.lead.activity'].suspend_security().create({
                            'stage_id': stage_id,
                            'date': date,
                            'lead_id': lead_id,
                            'interest_id': interest_id,
                        })
                        lead.suspend_security().write({
                            'next_activity_id': create.id,
                            'interest_id': interest_id
                        })
                        request.env.flush_all()
                        return valid_response(200, { 'id': create.id }, message='Success')
                    
                    message = f"Cannot add follow-up, follow-up on date {lead.next_activity_id.date} is still outstanding"
                    return invalid_response(401, 'follow_up_outstanding', message)
                else:
                    create = request.env['tw.lead.activity'].suspend_security().create({
                        'stage_id': stage_id,
                        'date': date,
                        'lead_id': lead_id,
                        'interest_id': lead.interest_id.id,
                    })
                    lead.write({
                        'next_activity_id': create.id,
                        'interest_id': lead.interest_id.id,
                    })
                    request.env.flush_all()
                    return valid_response(200, { 'id': create.id })
        except (UserError, ValidationError) as e:
            error_msg = e.args[0] if hasattr(e, 'args') and e.args else str(e)
            return invalid_response(400, e.__class__.__name__, error_msg)
        except Exception as e:
            _logger.error(traceback.format_exc())
            error_msg = e.args[0] if hasattr(e, 'args') and e.args else str(e)
            return invalid_response(500, e.__class__.__name__, error_msg)


    @http.route('/api/doodool/<version>/get_action_follow_up', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_action_follow_up(self, version, **post):
        limit = post.get('limit', 10)
        offset = post.get('offset', 0)
        
        request.env.cr.execute("""
            SELECT id, name->>'en_US' as name 
            FROM crm_stage 
            LIMIT %s OFFSET %s
        """, (limit, offset))
        ress = request.env.cr.dictfetchall()

        return valid_response(200, ress)

    @http.route('/api/doodool/<version>/get_detail_prospect_activity', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_detail_prospect_activity(self, version, **kwargs):
        uid = request.session.uid
        
        required_keys = ['id']  # add all required keys here
        list_not_req = [key for key in required_keys if key not in kwargs]
        if len(list_not_req) > 0:
            return invalid_response(401, 'required_field', f"Missing key(s): {', '.join(list_not_req)} in the provided payload!")

        lead_id = int(kwargs['id'])
        limit = kwargs.get('limit', 10)
        offset = kwargs.get('offset', 0)
        
        request.env.cr.execute(SQL("""
            SELECT 
                lead.id as lead_id
                , activity.id as activity_id
                , TO_CHAR(activity.date + INTERVAL '7 hours', 'YYYY-MM-DD HH24:MI:SS') as activity_date
                , result.id as activity_result_id
                , result.name as activity_result_name
                , stage.id as stage_id
                , stage.name->>'en_US' as stage_name
                , activity.remark as remark
                , activity.interest_id as interest_id
            FROM tw_lead as lead
            INNER JOIN tw_lead_activity AS activity ON activity.lead_id = lead.id
            LEFT JOIN crm_stage AS stage ON activity.stage_id = stage.id
            LEFT JOIN tw_lead_activity_result AS result ON result.id = activity.activity_result_id
            LEFT JOIN hr_employee AS hr ON hr.id = lead.sales_id
            LEFT JOIN resource_resource AS resource ON resource.id = hr.resource_id 
            WHERE resource.user_id = %s
            AND lead.id = %s
            ORDER BY activity.date DESC
            LIMIT %s OFFSET %s
        """, uid, lead_id, limit, offset))
        ress = request.env.cr.dictfetchall()

        return valid_response(200, ress)
        
    @http.route('/api/doodool/<version>/follow_up', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def follow_up(self, version, **post):
        uid = request.session.uid
        today = dt.now() + timedelta(hours=7)
        last_week = today - timedelta(days=7)
        last_week_min_7 = last_week - timedelta(hours=7)
        
        limit = post.get('limit', 10)
        offset = post.get('offset', 0)
        
        request.env.cr.execute(SQL("""
            SELECT 
                lead.id AS lead_id
                , lead_activity.id AS lead_act_id
                , lead.customer_name AS nama_customer
                , (lead_activity.date + INTERVAL '7 hours')::varchar AS tgl_follow_up
                , stage.name->>'en_US' AS action_follow_up
                , stage.id AS action_follow_up_id
                , lead_activity.remark AS remark
                , lead_activity.interest_id AS interest_id
                , count(lead_activity.id) AS follow_up_count
                , CASE
                    WHEN lead.state IN ('approved', 'reciept', 'dealt', 'spk') THEN 'Deal'
                    WHEN lead.state = 'open' THEN 'prospect'
                    END AS state
                , CASE 
                    WHEN (lead_activity.date + interval '7 hours') < NOW() + INTERVAL '1 hour' THEN 'php'
                    WHEN lead.follow_up_count = 1 THEN 'pdkt'
                    WHEN lead.follow_up_count = 2 THEN 'kencan'
                    WHEN lead.follow_up_count >= 3 THEN 'jadian'
                    END AS category
            FROM tw_lead lead
            LEFT JOIN tw_lead_activity lead_activity ON lead_activity.id = lead.next_activity_id
            LEFT JOIN tw_lead_activity_result result ON result.id = lead_activity.activity_result_id
            LEFT JOIN crm_stage stage ON stage.id = lead_activity.stage_id 
            INNER JOIN hr_employee hr ON hr.id = lead.sales_id
            INNER JOIN resource_resource resource ON resource.id = hr.resource_id 
            JOIN tw_lead_activity act on act.lead_id = lead.id 
            WHERE lead_activity.activity_result_id IS NULL 
            AND lead.state = 'open'
            AND lead_activity.date >= %s
            AND date_part('year', lead_activity.date + interval '7 hours') = date_part('year', CURRENT_DATE)
            AND resource.user_id = %s
            group by lead.id,lead_activity.id,stage.id
            ORDER BY lead_activity.date ASC
            LIMIT %s OFFSET %s
        """, last_week_min_7, uid, limit, offset))
        ress = request.env.cr.dictfetchall()
        
        return valid_response(200,ress)

    @http.route('/api/doodool/<version>/edit_follow_up', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def edit_follow_up(self, version, **kwargs):
        post = json.loads(request.httprequest.get_data(as_text=True))
        
        # Check required fields in post
        required_keys = ['follow_up_id', 'respond_id', 'interest_id', 'exec_followup_date', 'exec_followup_id']  # add all required keys here
        is_valid, error_msg = validate_payload(post, required_keys)
        if not is_valid:
            return invalid_response(400, 'Missing mandatory fields', error_msg)

        activity = request.env['tw.lead.activity'].browse(int(post['follow_up_id']))
        if not activity:
            return invalid_response(404, 'data_not_found', f"No Follow-Up Activity found for ID {post['follow_up_id']}")
        
        lead = activity.lead_id
        exec_followup_date_min_7 = str(dt.strptime(post['exec_followup_date'], '%Y-%m-%d %H:%M:%S') - relativedelta(hours=7))
        vals_activity = {
            'remark': post.get('remark', False),
            'stage_id': int(post['exec_followup_id']),
        }
        if 'interest_id' in post:
            vals_activity['interest_id'] = int(post['interest_id'])
        if 'respond_id' in post:
            vals_activity['activity_result_id'] = int(post['respond_id'])
            vals_activity['followup_state'] = 'completed'
            vals_activity['done_date'] = dt.now()
        
        _logger.info('vals_activity BEFORE: %s <<<<<<<<<<<' % vals_activity)
        if 'no_ktp' in post:
            vals_activity['identification_number'] = post['no_ktp']
        if 'no_kk' in post:
            vals_activity['identification_family_number'] = post['no_kk']
        if 'mobile' in post:
            mobile = post['mobile'].replace("-", "") if 'mobile' in post else False
            vals_activity['mobile'] = mobile
        if 'whatsapp' in post:
            whatsapp = post['whatsapp'].replace("-", "") if 'whatsapp' in post else False
            vals_activity['whatsapp'] = whatsapp
        if 'relative_phone_number' in post:
            vals_activity['relative_phone_number'] = post['relative_phone_number']
        if 'gender_id' in post:
            vals_activity['gender_id'] = int(post['gender_id'])
        if 'agama_id' in post:
            vals_activity['religion_id'] = int(post['agama_id'])
        if 'pekerjaan_id' in post:
            vals_activity['occupation_id'] = int(post['pekerjaan_id'])
        if 'tempat_tgl_lahir' in post:
            vals_activity['birthplace'] = post['tempat_tgl_lahir']
        if 'tgl_lahir' in post:
            vals_activity['birthdate'] = post['tgl_lahir']
        if 'email' in post:
            vals_activity['email'] = post['email']
        if 'product_id' in post:
            vals_activity['product_id'] = int(post['product_id'])
        if 'discount' in post:
            vals_activity['discount'] = post['discount']
        elif 'diskon' in post:
            vals_activity['discount'] = post['diskon']

        # Add Vehicle Information
        if 'current_motorcycle_status' in post:
            vals_activity['current_motorcycle'] = post['current_motorcycle_status']
        if 'motor_brand_id' in post:
            vals_activity['motor_brand_id'] = int(post['motor_brand_id'])
        if 'motor_type_id' in post:
            vals_activity['motor_type_id'] = int(post['motor_type_id'])
        if 'penggunaan_id' in post:
            vals_activity['unit_usage_id'] = int(post['penggunaan_id'])
        if 'pengguna_id' in post:
            vals_activity['unit_operator_id'] = int(post['pengguna_id'])
        if 'motor_ownership_id' in post:
            vals_activity['motor_ownership_id'] = int(post['motor_ownership_id'])

        # Add Addresses KTP
        if 'state_id' in post:
            vals_activity['state_id'] = int(post['state_id'])
        if 'kabupaten_id' in post:
            vals_activity['city_id'] = int(post['kabupaten_id'])
        if 'kecamatan_id' in post:
            vals_activity['district_id'] = int(post['kecamatan_id'])
        if 'kelurahan_id' in post:
            vals_activity['sub_district_id'] = int(post['kelurahan_id'])
        if 'street' in post:
            vals_activity['street'] = post['street']
        if 'rt' in post:
            vals_activity['rt'] = post['rt']
        if 'rw' in post:
            vals_activity['rw'] = post['rw']
        if 'kode_pos' in post:
            vals_activity['zip'] = post['kode_pos']

        # Add Addresses Domisili
        if 'is_sesuai_ktp' in post:
            vals_activity['is_same_ktp'] = True if post['is_sesuai_ktp'] and post['is_sesuai_ktp'][0] == 'Benar' else False
        if 'state_domisili_id' in post:
            vals_activity['state_domicile_id'] = int(post['state_domisili_id'])
        if 'kabupaten_domisili_id' in post:
            vals_activity['city_domicile_id'] = int(post['kabupaten_domisili_id'])
        if 'kecamatan_domisili_id' in post:
            vals_activity['district_domicile_id'] = int(post['kecamatan_domisili_id'])
        if 'kelurahan_domisili_id' in post:
            vals_activity['sub_district_domicile_id'] = int(post['kelurahan_domisili_id'])
        if 'street_domisili' in post:
            vals_activity['street_domicile'] = post['street_domisili']
        if 'rt_domisili' in post:
            vals_activity['rt_domicile'] = post['rt_domisili']
        if 'rw_domisili' in post:
            vals_activity['rw_domicile'] = post['rw_domisili']
        if 'kode_pos_domisili' in post:
            vals_activity['zip_domicile'] = post['kode_pos_domisili']

        # Add Other Profile
        if 'pendidikan_id' in post:
            vals_activity['education_id'] = int(post['pendidikan_id'])
        if 'golongan_darah_id' in post:
            vals_activity['blood_type_id'] = int(post['golongan_darah_id'])

        if 'payment_type_id' in post:
            vals_activity['payment_type_id'] = int(post['payment_type_id'])
            if int(post['payment_type_id']) == request.env.ref('tw_selection.selection_credit').id:
                if 'finco_id' in post:
                    vals_activity['finco_id'] = int(post['finco_id'])
                if 'uang_muka' in post:
                    vals_activity['down_payment'] = post['uang_muka']
                elif 'down_payment' in post:
                    vals_activity['down_payment'] = post['down_payment']
                if 'tgl_uang_muka' in post:
                    vals_activity['down_payment_date'] = post['tgl_uang_muka']
                if 'tenor' in post:
                    vals_activity['tenor'] = post['tenor']
                if 'cicilan' in post:
                    vals_activity['installment'] = post['cicilan']
                elif 'installment' in post:
                    vals_activity['installment'] = post['installment']
                if 'due_date' in post:
                    vals_activity['due_date'] = post['due_date']
        
        # prepare leads vals to be updated
        _logger.info('vals_activity AFTER: %s <<<<<<<<<<<' % vals_activity)

        # Handle next activity creation or clearing
        lead_vals = {}
        
        # Profile Data for Lead
        if 'hobi_id' in post:
            lead_vals['hobby_id'] = int(post['hobi_id'])
        if 'status_rumah_id' in post:
            lead_vals['housing_tenure_id'] = int(post['status_rumah_id'])
        if 'status_hp_id' in post:
            lead_vals['mobile_plan_status_id'] = int(post['status_hp_id'])
        if 'marital_status_id' in post:
            lead_vals['marital_status_id'] = int(post['marital_status_id'])
        if 'name_customer' in post:
            lead_vals['customer_name'] = post['name_customer']
            
        # Fallback for next_stage_id if frontend uses action_follow_id
        if 'next_stage_id' not in post and 'action_follow_id' in post and post['action_follow_id']:
            post['next_stage_id'] = post['action_follow_id']
        if 'next_followup_date' in post and 'next_stage_id' in post:
            next_followup_date_min_7 = str(dt.strptime(post.get('next_followup_date'), '%Y-%m-%d %H:%M:%S') - relativedelta(hours=7))
            create_activity = request.env['tw.lead.activity'].create({
                'lead_id': lead.id,
                'date': next_followup_date_min_7,
                'stage_id': int(post['next_stage_id']),
            })
            if create_activity:
                lead_vals['next_activity_id'] = create_activity.id
        else:
            # Remove next activity if result is filled and no next followup 
            if post.get('respond_id', False):
                lead_vals['next_activity_id'] = False

        # Update activity DIRECTLY first (prevents stale data in action_add_activity)
        # Then sync activity data to lead via action_add_activity
        try:
            with request.env.cr.savepoint():
                activity.suspend_security().write(vals_activity)
                if lead_vals:
                    lead.suspend_security().write(lead_vals)
                activity.suspend_security().action_add_activity()
                request.env.flush_all()
        except (UserError, ValidationError) as e:
            error_msg = e.args[0] if hasattr(e, 'args') and e.args else str(e)
            return invalid_response(400, e.__class__.__name__, error_msg)
        except Exception as e:
            _logger.error(traceback.format_exc())
            error_msg = e.args[0] if hasattr(e, 'args') and e.args else str(e)
            return invalid_response(500, e.__class__.__name__, error_msg)

        return valid_response(200, [{'id': post['follow_up_id']}], "Success follow up")

    @http.route('/api/doodool/<version>/get_detail_lead_follow_up', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_detail_lead_follow_up(self, version, **params):
        if 'id' not in params:
            return invalid_response(401, 'invalid_parameter', "Parameter 'id' is missing!")
        
        lead_id = int(params['id'])

        query_limit = ""
        limit = params.get('limit', 10)
        offset = params.get('offset', 0)

        if limit:
            query_limit += f"LIMIT {limit}"

        if offset:
            query_limit += f"OFFSET {offset}"

        query = SQL(f"""
            SELECT 
                l.id as lead_id
                , la.id as lead_act_id
                , (la.date + INTERVAL '7 hours')::varchar as date
                , result.id as respond_followup_id
                , result.name as respond_followup
                , stage.id as action_follow_up_id
                , stage.name as action_followup
                , la.remark as remark
                , la.interest_id as interest_id
            FROM tw_lead l
            LEFT JOIN tw_lead_activity la ON la.lead_id = l.id
            LEFT JOIN tw_lead_activity_result result ON result.id = la.activity_result_id
            LEFT JOIN crm_stage stage ON stage.id = la.stage_id 
            LEFT JOIN hr_employee hr ON hr.id = l.sales_id
            LEFT JOIN resource_resource r ON r.id = hr.resource_id 
            WHERE 1=1
            AND l.id = {lead_id}
            ORDER BY la.date DESC
            {query_limit}
        """)

        try:
            request.env.cr.execute(query)
            ress = request.env.cr.dictfetchall()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))
        
        result = {
            'message': 'ok',
            'data': ress,
        }
        return valid_response(200,result)

    @http.route('/api/doodool/<version>/respon_activity', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def respon_activity(self, version, **params):
        if 'classification' not in params:
            return invalid_response(401, 'invalid_parameter', "Parameter 'classification' is missing!")
        
        classification = ('all', params['classification'])

        limit = params.get('limit', 10)
        offset = params.get('offset', 0)
        
        query = SQL("""
            SELECT id
                , name
                , description
                , is_end_of_process AS end_proses
            FROM tw_lead_activity_result
            WHERE interest_id IN (%s)
            ORDER BY sequence ASC
            LIMIT %s
            OFFSET %s
        """, SQL("SELECT id FROM tw_selection WHERE value IN %s AND type = 'Interest'", classification), limit, offset)
        
        try:
            request.env.cr.execute(query)
            ress =  request.env.cr.dictfetchall()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))

        return valid_response(200, ress)

    @http.route('/api/doodool/<version>/communicate', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def communicate(self, version, **params):
        result = {
            'message':'ok',
            'data': [],
        }
        return valid_response(200, result)
    
    @http.route('/api/doodool/<version>/prospect_notes', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def prospect_notes(self, version, **params):
        if 'id' not in params:
            return invalid_response(401, 'invalid_parameter', "Parameter 'id' is missing!")

        lead_id = int(params['id'])
        limit = params.get('limit', 10)
        offset = params.get('offset', 0)
        
        query = SQL("""
            SELECT 
                TO_CHAR(date, 'YYYY-MM-DD') as date
                , COALESCE(description, 'Belum ada catatan') as catatan
            FROM tw_lead
            WHERE id = %s
            LIMIT %s
            OFFSET %s
        """, lead_id, limit, offset)
        
        try:
            request.env.cr.execute(query)
            ress =  request.env.cr.dictfetchall()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))
        
        return valid_response(200,ress)

    @http.route('/api/doodool/<version>/history', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def history(self, version, **params):
        if 'id' not in params:
            return invalid_response(401, 'invalid_parameter', "Parameter 'id' is missing!")

        list_filter = []
        if 'is_followup' in params and params['is_followup'] == True:
            list_filter.append('follow_up')
        if 'is_communicate' in params and params['is_communicate'] == True:
            list_filter.append('communication')
        if 'is_general' in params and params['is_general'] == True:
            list_filter.append('general')
        
        category_query = SQL("SELECT id FROM tw_selection WHERE value = %s AND type = 'LogCategory'", list_filter)

        lead_id = int(params['id'])
        limit = params.get('limit', 10)
        offset = params.get('offset', 0)
        
        query = SQL("""
            SELECT name AS activity_name
                , TO_CHAR(date + INTERVAL '7 hours', 'YYYY-MM-DD') AS date
                , (SELECT name FROM tw_selection WHERE id = category_id) AS category
            FROM crm_lead_logs
            WHERE lead_id = %s
            AND category_id IN (%s)
            ORDER BY date DESC
            LIMIT %s
            OFFSET %s
        """, lead_id, category_query, limit, offset)

        try:
            request.env.cr.execute(query)
            ress = request.env.cr.dictfetchall()
        except Exception as e:
            return invalid_response(500, e.__class__.__name__, str(e))
                    
        return valid_response(200, ress)

