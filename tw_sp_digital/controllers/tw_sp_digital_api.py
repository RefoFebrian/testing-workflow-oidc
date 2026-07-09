# 1: imports of python lib
import json
try:
    import simplejson as json
except ImportError:
    import json
import logging
_logger = logging.getLogger(__name__)

# 2: import of known third party lib
from odoo.addons.tw_api.controllers.main import *
from odoo.addons.rest_api.controllers.main import check_valid_token

# 3:  imports of odoo
from odoo import http

# 4:  imports from odoo modules
from odoo.http import request

# 5: local imports

# 6: Import of unknown third party lib


class ControllerREST(http.Controller):
    @http.route('/api/doodool/v1/get_sp_digital', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_sp_digital(self, **post):
        uid = request.session.uid
        company_ids = request.env.user.company_ids
        WHERE = '' 
        employee = request.env['hr.employee'].sudo().search([
            ('user_id','=',uid)
        ], limit=1)

        if employee.job_id.sales_force_id.value in ('sales_operation_head', 'area_manager'):
            WHERE += ' AND sp.company_id IN {company_ids}'.format(company_ids=str(tuple(company_ids.ids)).replace(',)', ')'))
        else:
            WHERE += f' AND sp.employee_id = {employee.id}'

        limit = 10
        offset = 0
        ORDER = 'ORDER BY sp.date::VARCHAR DESC'
        string = False

        query = f"""
            SELECT
                DISTINCT sp.id
                , sp.sp_level AS sp_level
                , sp.state AS state
                , ru.id as uid
                , emp.name AS employee_name
                , sp.date::varchar AS date
                , TO_CHAR(TO_DATE (sp.month::text, 'MM'), 'Month') AS month
                , sp.year AS year
            FROM tw_sp_digital sp
            LEFT JOIN hr_employee AS emp ON emp.id = sp.employee_id
            LEFT JOIN res_users AS ru ON ru.id = emp.user_id
            LEFT JOIN hr_job AS job ON job.id = emp.job_id
            LEFT JOIN tw_sp_digital_line AS line ON line.sp_digital_id = sp.id
            LEFT JOIN res_company AS branch ON branch.id = sp.company_id
            WHERE 1=1
            AND sp.state != 'draft'
            AND job.sales_force_id IS NOT NULL
            {WHERE}
            {ORDER}
            LIMIT {limit}
            OFFSET {offset}
        """
        request._cr.execute(query)
        ress = request._cr.dictfetchall()
        return valid_response(200, ress)
    
    @http.route('/api/doodool/v1/get_detail_sp_digital', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def get_detail_sp_digital(self, **post):
        uid = request.session.uid
        company_ids = request.env.user.company_ids
        WHERE = ''
        sp_digital_id = post.get('id', False)
        url = str(request.httprequest.url).split('/api/')[0]
        if not sp_digital_id:
            return invalid_response(400, 'data_not_found', 'SP Digital ID')
        
        query = f"""
            SELECT
                sp.id
                , sp.sp_level AS sp_level
                , sp.state AS state
                , emp.name AS employee_name
                , sp.date::VARCHAR AS date
                , TRIM(TO_CHAR(TO_DATE (sp.month::text, 'MM'), 'Month')) AS month
                , sp.year AS year
                , CASE
                    WHEN COUNT(DISTINCT spa.id) > 0
                        THEN (COUNT(DISTINCT spa_approve.id)::FLOAT/COUNT(DISTINCT spa.id)::FLOAT)*100
                ELSE 0 END
                , '{url}' || '/web/content/tw.sp.digital/' || sp.id || '/file_sp' AS url_pdf
                , JSON_AGG(DISTINCT JSON_BUILD_OBJECT(
                    'id', spl.id,
                    'name', spl.name,
                    'tipe', spl.type,
                    'sp_level', spl.sp_level,
                    'keterangan', spl.keterangan
                )::JSONB) AS sp_line
                , CASE
                    WHEN COUNT(spa.id) > 1 
                	    THEN JSON_AGG(DISTINCT JSON_BUILD_OBJECT(
                            'id', spa.id,
                            'employee', emp_approval.name,
                            'groups', groups_approval.name ->> 'en_US',
                            'date', spa.tanggal::VARCHAR,
                            'state', spa.state
	                    )::JSONB)
                ELSE NULL END AS sp_approval
            FROM tw_sp_digital sp
            LEFT JOIN hr_employee AS emp ON emp.id = sp.employee_id
            LEFT JOIN tw_sp_digital_line AS spl ON spl.sp_digital_id = sp.id
            LEFT JOIN ir_model im ON im.model = 'tw.sp.digital'
            LEFT JOIN tw_approval_line spa ON spa.transaction_id = sp.id AND spa.model_id = im.id
            LEFT JOIN tw_approval_line spa_approve ON spa_approve.transaction_id = sp.id AND spa_approve.model_id = im.id AND spa_approve.state = 'approve'
            LEFT JOIN hr_employee emp_approval ON emp_approval.user_id = spa.approver_id
            LEFT JOIN res_groups AS groups_approval ON groups_approval.id = spa.group_id
            LEFT JOIN res_company AS branch ON branch.id = sp.company_id
            WHERE 1=1
            AND sp.id = {sp_digital_id}
            GROUP BY sp.id,emp.id
        """
        request._cr.execute(query)
        ress = request._cr.dictfetchall()
        return valid_response(200, ress[0] if ress else [])

    @http.route('/api/doodool/v1/post_rfa_sp_digital', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_rfa_sp_digital(self, **post):
        try:
            post = json.loads(request.httprequest.get_data(as_text=True))
            uid = request.session.uid
            company_ids = request.env.user.company_ids
            WHERE = ' WHERE 1=1' 
            sp_digital_id = post.get('transaction_id', False)
            if not sp_digital_id:
                return invalid_response(400, 'data_not_found', 'SP Digital Id is required')
            
            sp_digital_obj = request.env['tw.sp.digital'].sudo().browse(int(sp_digital_id))
            if not sp_digital_obj:
                return invalid_response(400, 'data_not_found', 'SP Digital record not found')

            employee_obj = request.env['hr.employee'].sudo().search([
                ('user_id','=',uid)
            ], limit=1)
            if not employee_obj:
                return invalid_response(400, 'employee_not_found', 'Employee does not exist')
            if not employee_obj.job_id.sales_force_id.value in ('sales_operation_head', 'area_manager'):
                return invalid_response(400, 'invalid_job', 'Hanya SOH & AM yang bisa request deviasi')
            
            try:
                sp_digital_obj.action_rfa()
            except Exception as e:
                return invalid_response(400, 'rfa_failed', e)
        except Exception as e:
            message = f'Error Exception - {str(e)}'
            _logger.info(message)
            return invalid_response(400, 'rfa_failed', e)
        
        return valid_response(200, { 'id': sp_digital_obj.id })
    
    @http.route('/api/doodool/v1/post_confirm_sp_digital', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_confirm_sp_digital(self, **post):
        try:
            post = json.loads(request.httprequest.get_data(as_text=True))
            uid = request.session.uid
            company_ids = request.env.user.company_ids
            WHERE = ' WHERE 1=1' 
            sp_digital_id = post.get('transaction_id', False)
            if not sp_digital_id:
                return invalid_response(400, 'data_not_found', 'SP Digital Id is required')
            
            sp_digital_obj = request.env['tw.sp.digital'].sudo().browse(int(sp_digital_id))
            if not sp_digital_obj:
                return invalid_response(400, 'data_not_found', 'SP Digital record not found')
            
            employee_obj = request.env['hr.employee'].sudo().search([
                ('user_id','=',uid)
            ], limit=1)
            if not employee_obj:
                return invalid_response(400, 'employee_not_found', 'Hanya SOH & AM yang bisa mengkonfirmasi SP')
            if not employee_obj.job_id.sales_force_id.value in ('sales_operation_head', 'area_manager'):
                return invalid_response(400, 'invalid_job', 'Hanya SOH & AM yang bisa mengkonfirmasi SP')
            
            try:
                sp_digital_obj.action_confirm()
            except Exception as e:
                return invalid_response(400, 'confirm_failed', e)
        except Exception as e:
            message = f'Error Exception - {str(e)}'
            _logger.info(message)
            return invalid_response(400, 'rfa_failed', e)
        
        return valid_response(200, { 'id': sp_digital_obj.id })
    
    @http.route('/api/doodool/v1/post_approve_deviasi_sp_digital', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_approve_deviasi_sp_digital(self, **post):
        try:
            post = json.loads(request.httprequest.get_data(as_text=True))
            uid = request.session.uid
            company_ids = request.env.user.company_ids
            WHERE = ' WHERE 1=1' 
            sp_digital_id = post.get('transaction_id', False)
            if not sp_digital_id:
                return invalid_response(400, 'data_not_found', 'SP Digital Id is required')
            
            sp_digital_obj = request.env['tw.sp.digital'].sudo().browse(int(sp_digital_id))
            if not sp_digital_obj:
                return invalid_response(400, 'data_not_found', 'SP Digital record not found')
            
            try:
                sp_digital_obj.action_approve()
            except Exception as e:
                return invalid_response(400, 'approve_failed', e)
        except Exception as e:
            message = f'Error Exception - {str(e)}'
            _logger.info(message)
            return invalid_response(400, 'rfa_failed', e)
        
        return valid_response(200, { 'id': sp_digital_obj.id })

    @http.route('/api/doodool/v1/post_reject_deviasi_sp_digital', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_reject_deviasi_sp_digital(self, **post):
        try:
            post = json.loads(request.httprequest.get_data(as_text=True))
            uid = request.session.uid
            company_ids = request.env.user.company_ids
            WHERE = ' WHERE 1=1' 
            sp_digital_id = post.get('transaction_id', False)
            if not sp_digital_id:
                return invalid_response(400, 'required_field', 'SP Digital id is required')
            
            alasan_reject = post.get('alasan_reject', False)
            if not alasan_reject:
                return invalid_response(400, 'required_field', 'SP Digital alasan_reject is required')
            
            sp_digital_obj = request.env['tw.sp.digital'].sudo().browse(int(sp_digital_id))
            if not sp_digital_obj:
                return invalid_response(400, 'data_not_found', 'SP Digital record not found')

            employee_obj = request.env['hr.employee'].sudo().search([
                ('user_id','=',uid)
            ], limit=1)
            
            try:
                vals = {'reason': alasan_reject}
                approval = sp_digital_obj._check_user_groups()
                approval.write(vals)
                reject_form = sp_digital_obj.with_context(vals).action_reject(reject_by_apps=True)
            except Exception as e:
                return invalid_response(400, 'reject_failed', e)
        except Exception as e:
            message = f'Error Exception - {str(e)}'
            _logger.info(message)
            return invalid_response(400, 'rfa_failed', e)
        
        return valid_response(200, { 'id': sp_digital_obj.id })
    
    @http.route('/api/doodool/v1/post_received_sp_digital', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def post_received_sp_digital(self, **post):
        try:
            post = json.loads(request.httprequest.get_data(as_text=True))
            uid = request.session.uid
            company_ids = request.env.user.company_ids
            WHERE = ' WHERE 1=1'
            sp_digital_id = post.get('transaction_id', False)
            if not sp_digital_id:
                return invalid_response(400, 'data_not_found', 'SP Digital Id is required')
            
            sp_digital_obj = request.env['tw.sp.digital'].sudo().browse(int(sp_digital_id))
            if not sp_digital_obj:
                return invalid_response(400, 'data_not_found', 'SP Digital record not found')
            
            try:
                sp_digital_obj.action_received()
            except Exception as e:
                return invalid_response(400, 'received_failed', e)
        except Exception as e:
            message = f'Error Exception - {str(e)}'
            _logger.info(message)
            return invalid_response(400, 'rfa_failed', e)
        
        return valid_response(200, { 'id': sp_digital_obj.id })