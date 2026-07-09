import functools
import odoo
from odoo import http
from odoo.http import request
from odoo.http import Response
from odoo.addons.tw_api.controllers.main import valid_response, invalid_response, check_sensitive_value
from odoo.addons.rest_api.controllers.main import check_valid_token, validate_payload
import werkzeug.wrappers
try:
    import simplejson as json
except ImportError:
    import json
import logging
_logger = logging.getLogger(__name__)
from datetime import timedelta,datetime,date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
import base64
import os

def _get_bulan():
    return str(date.today().month)

class ControllerREST(http.Controller):
    @http.route('/api/doodool/<version>/action_token_firebase', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def token_firebase(self, version, **post):
        uid = request.session.uid
        post = json.loads(request.httprequest.get_data(as_text=True))
        vals = {
            'firebase_token':post['firebase_token'],
            'firebase_id':post['firebase_id'],
            'device_id':post['device_id'],
            'name':post['device_name'],
            'version_code':post['version_code'],
            'version_name':post['version_name'],
            'access_token':post['access_token'],
            'active':True,
            'user_id':uid,
        }
        # Deactive all firebase users with this phone and this user
        firebase_users = request.env['tw.firebase.user'].sudo().search([
            ('active','=',True),
            '|', ('user_id','=',uid),
            ('device_id','=',post['device_id']),])
        if firebase_users:
            for firebase_user in firebase_users:
                firebase_user.write({'active':False})
        
        # Check if there is already similar firebase user
        check_similar_firebase_user = request.env['tw.firebase.user'].sudo().search([
            ('user_id','=',uid),
            ('device_id','=',post['device_id']),
            ],limit=1)
        # Create if not
        if not check_similar_firebase_user :
            firebase_user = request.env['tw.firebase.user'].sudo().create(vals)
            if firebase_user:
                result = {
                    'id':firebase_user.id
                }
                return valid_response(200, result, 'Success')
        # Update active state & token if any
        else :
            check_similar_firebase_user.write({
                'active': True,
                'access_token': post['access_token'],
                'firebase_token': post['firebase_token'],
                })
            result = {
                'id':check_similar_firebase_user.id
            }
            return valid_response(200, result, 'Success')


    @http.route('/api/doodool/<version>/update_token_firebase', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def update_token_firebase(self, version, **post):
        uid = request.session.uid
        post = json.loads(request.httprequest.get_data(as_text=True))
        firebase_token_update = post.get('firebase_token_update',False)
        check_firebase_user = request.env['tw.firebase.user'].sudo().search([
            ('active', '=', True), ('user_id', '=', uid)], limit=1)
        
        if check_firebase_user:
            check_firebase_user.sudo().write({'firebase_token':firebase_token_update})
            return valid_response(200, 'Success')

        else :
            vals = {
                'firebase_token':firebase_token_update,
                'device_id':post['device_id'],
                'name':post['device_name'],
                'version_code':post['version_code'],
                'version_name':post['version_name'],
                'access_token':post['access_token'],
                'active':True,
                'user_id':uid,
            }
            firebase_user = request.env['tw.firebase.user'].sudo().create(vals)
            if firebase_user :
                return valid_response(200, 'Success')

    
    @http.route('/api/doodool/<version>/notifications_firebase', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def notifications_firebase(self, version, **post):
        uid = request.session.uid
        sort_parameter = False
        filters = False 
        ORDER = " ORDER BY fn.create_date desc"
        limit = 10
        offset = 0
        tipe = False


        WHERE = "WHERE 1=1 AND fn.state in ('draft', 'send', 'unread', 'read') "
        
        if 'sort_parameter' in post:
            if post['sort_parameter'] == 'tanggal notification':
                ORDER += " , fn.send_date + INTERVAL '7 hours' ASC"
            if post['sort_parameter'] == 'overdue':
               ORDER += " , fn.overdue ASC"

        if 'tipe' in post:
            if post['tipe'] == 'read':
                WHERE += " AND fn.state= 'read' "
            if post['tipe'] == 'unread':
              WHERE += " AND fn.state = 'unread' "
            if post['tipe'] == 'all':
                 WHERE += "  "
            
        if 'limit' in post:
            limit = int(post['limit'])
        
        if 'offset' in post:
            offset = int(post['offset'])


        notification = """
            SELECT
                fnc.jenis_reminder as jenis_riminder
                , fn.id as fm_id
                , (fn.create_date + INTERVAL '7 hours')::VARCHAR as tgl_kirim_notification
                , l.id as lead_id
                , COALESCE(l.customer_name,fn.customer_name) as nama_customer
                , l.mobile as no_hp_konsumen
                , l.date::VARCHAR as tgl_lead
                , ts_interest.name as minat
                , s.name as follow_up_by
                , (fn.followup_date + INTERVAL '7 hours')::VARCHAR as tgl_janji_followup
                , fn.state AS  status_baca_notification
                , 'Overdue '|| fn.overdue|| ' Hari' as overdue 
                , hr.id as employee_id
                , hr.name as employee_name
                , job.name as jabatan
                , hr.mobile_phone as no_hp_sales
                , CASE WHEN (fnc.title is not null and fnc.title != '') THEN fnc.title ELSE fnc.name END as tipe
            FROM tw_firebase_notification as fn
                LEFT JOIN tw_firebase_notification_category as fnc on fnc.id = fn.category_id
                LEFT JOIN tw_lead_activity la ON la.id = fn.lead_activity_id
                LEFT JOIN tw_lead as l on l.id= la.lead_id
                LEFT JOIN crm_stage s ON la.stage_id = s.id
                LEFT JOIN hr_employee hr ON hr.id = l.sales_id

                LEFT JOIN hr_employee hr_receiver ON hr_receiver.id = fn.employee_receiver_id
                LEFT JOIN resource_resource r ON r.id = hr_receiver.resource_id 
                LEFT JOIN res_users as usr ON usr.id=r.user_id
                LEFT JOIN hr_job as job on job.id=hr.job_id
                LEFT JOIN tw_selection ts_interest on ts_interest.id = l.interest_id 
                
            %s
            AND usr.id = %s
            %s
            LIMIT %d
            OFFSET %d
        """ %(WHERE, uid, ORDER, limit,offset)
        request._cr.execute (notification)
        ress =  request._cr.dictfetchall()

        return valid_response(200, ress, 'Success')

    @http.route('/api/stock_opname/<version>/notifications_firebase', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def notifications_firebase(self, version, **post):
        uid = request.session.uid
        sort_parameter = False
        filters = False 
        ORDER = " ORDER BY fn.create_date desc"
        limit = 10
        offset = 0
        tipe = False

        WHERE = "WHERE 1=1 AND fn.state in ('draft', 'send', 'unread', 'read') "
        
        if 'sort_parameter' in post:
            if post['sort_parameter'] == 'tanggal notification':
                ORDER += " , fn.send_date + INTERVAL '7 hours' ASC"
            if post['sort_parameter'] == 'overdue':
               ORDER += " , fn.overdue ASC"

        if 'tipe' in post:
            if post['tipe'] == 'read':
                WHERE += " AND fn.state= 'read' "
            if post['tipe'] == 'unread':
              WHERE += " AND fn.state = 'unread' "
            if post['tipe'] == 'all':
                 WHERE += "  "
            
        if 'limit' in post:
            limit = int(post['limit'])
        
        if 'offset' in post:
            offset = int(post['offset'])

        notification = """
            SELECT
                fn.id as fm_id
                , (fn.create_date + INTERVAL '7 hours')::VARCHAR as tgl_kirim_notification
                , fn.state AS  status_baca_notification
                , 'Overdue '|| fn.overdue|| ' Hari' as overdue 
                , hr_receiver.id as employee_id
                , hr_receiver.name as employee_name
                , job.name as jabatan
                , CASE WHEN (fnc.title is not null and fnc.title != '') THEN fnc.title ELSE fnc.name END as tipe
            FROM tw_firebase_notification as fn
                LEFT JOIN tw_firebase_notification_category as fnc on fnc.id = fn.category_id
                LEFT JOIN hr_employee hr_receiver ON hr_receiver.id = fn.employee_receiver_id
                LEFT JOIN resource_resource r ON r.id = hr_receiver.resource_id 
                LEFT JOIN res_users as usr ON usr.id=r.user_id
                LEFT JOIN hr_job as job on job.id=hr_receiver.job_id
                
            %s
            AND usr.id = %s
            AND fnc.name = 'Notification Stock Opname Outstanding Photo'
            %s
            LIMIT %d
            OFFSET %d
        """ %(WHERE, uid, ORDER, limit,offset)
        request._cr.execute (notification)
        ress =  request._cr.dictfetchall()

        return valid_response(200, ress, 'Success')
    
    @http.route('/api/doodool/<version>/detail_notifications_firebase', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def notifications_firebase_detail(self, version, **post):
        uid = request.session.uid
        fn_id = post.get('id',False)
        if not fn_id:
            return invalid_response(400, 'Bad Request', 'lead_id_not_found')
            
        fn_id = int(fn_id)
        if fn_id :
            fm=request.env['tw.firebase.notification'].sudo().search([('id','=',fn_id)])
            if fm :
                fm.sudo().write({'state':'read'})
        data = {}
        deals = """
            SELECT 
                fn.id as fm_id
                , fn.message as pesan
                , (fn.send_date)::VARCHAR as tgl_kirim_notification
                , l.id as lead_id
                , l.customer_name as nama_customer
                , l.mobile as no_hp_konsumen
                , (l.date)::VARCHAR as tgl_lead
                , ts_interest.name as minat
                , s.name as follow_up_by
                , (la.date + INTERVAL '7 hours')::VARCHAR as tgl_janji_followup
                , 'Overdue '|| fn.overdue|| ' Hari' as overdue 
                , hr.id as employee_id
                , hr.name as employee_name
                , job.name as jabatan
                , fn.state AS status_baca_notification
                , hr.mobile_phone as no_hp_sales
                , CASE WHEN (fnc.title is not null and fnc.title != '') THEN fnc.title ELSE fnc.name END as tipe
                , fnc.jenis_reminder as jenis_riminder
            FROM tw_firebase_notification as fn
                LEFT JOIN tw_firebase_notification_category as fnc on fnc.id = fn.category_id
                LEFT JOIN tw_lead_activity la ON la.id = fn.lead_activity_id
                LEFT JOIN tw_lead as l on l.id= la.lead_id
                LEFT JOIN crm_stage s ON la.stage_id = s.id
                LEFT JOIN hr_employee hr ON hr.id = l.sales_id
                LEFT JOIN resource_resource r ON r.id = hr.resource_id 
                LEFT JOIN res_users as usr ON usr.id=r.user_id
                LEFT JOIN hr_job as job on job.id=hr.job_id
                LEFT JOIN tw_selection ts_interest on ts_interest.id = l.interest_id 
            WHERE fn.id = %d
        """ %(fn_id)
        request._cr.execute(deals)
        ress =  request._cr.dictfetchall()
        ress[0]['uid'] =uid

        return valid_response(200, ress, 'Success')

    @http.route('/api/doodool/<version>/jumlah_notifications', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def jumlah_notifications(self, version, **post):
        jumlah_message=0
        jumlah_notif=0
        uid = request.session.uid
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',uid)],limit=1).id
        query_notif = """
            SELECT  
            COUNT(id) as jumlah_notif
            FROM tw_firebase_notification 
            WHERE state = 'unread'
            AND employee_receiver_id = %d
        """ %(employee_id)
        request._cr.execute (query_notif)
        ress =  request._cr.dictfetchall()
        if ress:
            ress = ress[0]
        jumlah_notif=ress['jumlah_notif']


        query_message = """
            SELECT 
            COUNT(mfl.id) as jumlah_message 
            FROM tw_firebase_message as mf
            LEFT JOIN tw_firebase_message_line as mfl ON mfl.firebase_message_id = mf.id
            WHERE 1=1 AND mfl.state = 'unread'
            AND mfl.employee_receiver_id = %d
        """ %(employee_id)
        request._cr.execute (query_message)
        ress_message =  request._cr.dictfetchall()
        if ress_message:
            ress_message = ress_message[0]
    
        jumlah_message=ress_message['jumlah_message']
        jumlah_inbox=jumlah_notif+jumlah_message
        inbox={
            'jumlah': jumlah_inbox
            }
        return valid_response(200, inbox, 'Success')
    

    @http.route('/api/doodool/<version>/send_mesaage', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def send_mesaage(self, version, **post):
        uid = request.session.uid
        post = json.loads(request.httprequest.get_data(as_text=True))
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',uid)],limit=1).id
        
        req_post = [
            'pesan',
            'send_to_messages_employee_id',
        ]
        
        list_not_req = []
        for req in req_post:
            if req not in post:
                list_not_req.append(req)

        if len(list_not_req) > 0:
            return invalid_response(400, 'Bad Request', f'{list_not_req} is required field')
        
        ids = []
        ids.append([0,False,{
            'employee_receiver_id':post['send_to_messages_employee_id']
        }])
        create = request.env['tw.firebase.message'].sudo().create({
            'name': post['pesan'],
            'message':post['pesan'],
            'employee_sender_id': employee_id,
            'firebase_message_line_ids': ids
        })
        if create:
            return valid_response(200, {'id':create.id}, 'Success')

        return invalid_response(400, 'Bad Request', 'Pesan Gagal Terkirim')

    @http.route('/api/doodool/<version>/messages_firebase', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def messages_firebase(self, version, **post):
        uid = request.session.uid
        employee_id = request.env['hr.employee'].sudo().search([('user_id','=',uid)],limit=1)
        sort_parameter = False
        filters = False 
        ORDER = ""
        limit = 10
        offset = 0
        tipe = False
        ORDER = " ORDER BY mf.id desc"

        WHERE = "WHERE 1=1 and mfl.state in ('send','unread','read') and mfl.employee_receiver_id = %d" % (employee_id)
        if 'sort_parameter' in post:
            tipe = post['sort_parameter']
            if post['sort_parameter'] == 'Tanggal Notification':
                ORDER = " ORDER BY mf.create_date + INTERVAL '7' ASC"
    
        if 'tipe' in post:
            if post['tipe'] == 'read':
                WHERE += " AND mfl.state = 'read' "
            if post['tipe'] == 'unread':
              WHERE += " AND mfl.state = 'unread' "
            if post['tipe'] == 'all':
                 WHERE += "  "            

        if 'limit' in post:
            limit = int(post['limit'])

        if 'offset' in post:
            offset = int(post['offset'])

        messages = """ 
            SELECT
                mfl.id
                ,mf.name as subject
                ,mf.message as messages
                ,mf.employee_sender_id as from_employee_id
                ,hr_from.name as from_employee_name
                ,mfl.employee_receiver_id as to_employee_id
                ,hr_to.name as to_employee_name
                ,mfl.send_date + INTERVAL '7 hours' as tgl_kirim_messages
                ,mfl.state
            FROM tw_firebase_message as mf
                LEFT JOIN tw_firebase_message_line as mfl ON mfl.firebase_message_id = mf.id
                LEFT JOIN hr_employee as hr_from on hr_from.id = mf.employee_sender_id
                LEFT JOIN hr_employee as hr_to on hr_to.id = mfl.employee_receiver_id
            %s
            %s
            LIMIT %d
            OFFSET %d
        """ %(WHERE,ORDER,limit,offset)
        request._cr.execute (messages)
        ress =  request._cr.dictfetchall()
        return valid_response(200, ress, 'Success')

    
    @http.route('/api/doodool/<version>/detail_messages_firebase', methods=['GET'], type='http', auth='none', csrf=False)
    @check_valid_token
    def detail_messages_firebase(self, version, **post):
        uid = request.session.uid
        
        m_id = post.get('id',False)
        if not m_id:
            return invalid_response(400, 'Bad Request', 'id Not Found')

        m_id = int(m_id)
        if m_id :
            fm=request.env['tw.firebase.message.line'].sudo().search([('id','=',m_id)])
            if fm :
                fm.sudo().write({'state':'read'})
        data = {}
        detail_messages = """
            SELECT
                mfl.id
                ,mf.name as subject
                ,mf.message as messages
                ,mf.employee_sender_id as from_employee_id
                ,hr_from.name as from_employee_name
                ,mfl.employee_receiver_id as to_employee_id
                ,hr_to.name as to_employee_name
                ,mfl.send_date + INTERVAL '7 hours' as tgl_kirim_messages
                ,mfl.state
            FROM tw_firebase_message as mf
                LEFT JOIN tw_firebase_message_line as mfl ON mfl.firebase_message_id = mf.id
                LEFT JOIN hr_employee as hr_from on hr_from.id = mf.employee_sender_id
                LEFT JOIN hr_employee as hr_to on hr_to.id = mfl.employee_receiver_id
            WHERE 1=1
            and  mfl.id= %d
        """ %(m_id)
        request._cr.execute (detail_messages)
        ress =  request._cr.dictfetchall()
        return valid_response(200, ress, 'Success')
    

    @http.route('/api/doodool/<version>/hapus_messages_firebase', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def hapus_messages_firebase(self, version, **post):
        uid = request.session.uid
        m_id = post.get('id',False)
        if m_id :
            fml = request.env['tw.firebase.message.line'].sudo().search([('id','=',m_id)])
            fm = fml.firebase_message_id
            if fml :
                delete = fml.sudo().unlink()
                if delete:
                    # check apakah header dari line masih mempunya line
                    if len(fm.firebase_message_line_ids) == 0:
                        fm.sudo().unlink()
                    return valid_response(200, '', 'Success')

        return invalid_response(400, 'Bad Request', 'Failed to delete message')
        

    @http.route('/api/doodool/<version>/replay_message', methods=['POST'], type='json', auth='none', csrf=False)
    @check_valid_token
    def replay_message(self, version, **post):
        uid = request.session.uid
        firebase_message_line_ids=[]
        message = {
            'message':post.get('messages',False),
            'employee_sender_id':post.get('from_employee_id',False),
            'name':post.get('subject',False),
        } 
        firebase_message_line_ids.append([0,0,{
            'employee_receiver_id':post.get('to_employee_id',False),
        }])
        message['firebase_message_line_ids']=firebase_message_line_ids
        create = request.env['tw.firebase.message'].suspend_security().create(message)
        create.action_send()
        if create :
            return valid_response(200, {'id':create.id}, 'Success')
    