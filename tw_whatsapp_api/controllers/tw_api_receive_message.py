from datetime import datetime
from dateutil.relativedelta import relativedelta
# from ..models.tw_whatsapp_error_log import response_json
try:
    import simplejson as json
except ImportError:
    import json
import logging
_logger = logging.getLogger(__name__)
from odoo import http
from odoo.http import request


class ControllerREST(http.Controller):
    @http.route('/api/wa/receive_message', methods=['POST'], auth="public", type="http", csrf=False)
    def api_wablas_receive_message(self, **post):
        try:
            inbox_vals = {
                'whatsapp_id': post.get('id', False),
                'phone_number': post.get('phone', False),
                'sender_name': post.get('pushName', False),
                'sender_number': str(post['receiver']) if post.get('receiver', False) else False,
                'message': post.get('message', False),
                'message_received_date': post.get('timestamp', False),
                'group_id': post.get('groupId', False),
                'group_name': post.get('groupSubject', False),
                'category': post.get('category', False),
                'attachment_url': post.get('url', False),
                'address': post.get('address', False),
                'location': post.get('location', False),
                'latitude': post.get('latitude', False),
                'longitude': post.get('longitude', False),
                'accuracy': post.get('accuracy', False),
                'message_type': 'outbox'
            }
            if inbox_vals['category'] == 'image':
                inbox_vals.update({'attachment_name': post.get('image', False)})
            else:
                inbox_vals.update({'attachment_name': post.get('file', False)})
            try:
                request.env['tw.whatsapp.message'].sudo().create(inbox_vals)
            except Exception as e:
                error_obj = request.env['tw.whatsapp.error.log'].sudo().search([
                    ('name','=','WABLAS API RECEIVE MESSAGE'),
                    ('description','=',e),
                    ('data','=',json.dumps(post))
                ])
                if not error_obj:
                    error_obj.sudo().create({
                        'name': 'WABLAS API RECEIVE MESSAGE',
                        'description': e,
                        'data': json.dumps(post)
                    })
                # Response
                response = response_json(response_code=200, data_in=json.dumps(post), message=None, status=True, is_api_log=False, data_count=1)
                return response
            # Response
            response = response_json(response_code=200, data_in=json.dumps(post), message=None, status=True, data_count=1)
            return response
        except Exception as e:
            # Response
            message = {"message": "Something went wrong, please contact system administrator!"}
            response = response_json(response_code=400, data_in=json.dumps(post), message=message, status=False, error_description=e, data_count=1)
            return response

    @http.route('/api/ext/wa/receive_message_status', methods=['POST'], auth="public", type="json", csrf=False)
    def api_wablas_receive_message_status(self, **post):
        try:
            message_id = post.get('id')
            status = post.get('status')
            phone = post.get('phone')
            try:
                msg_obj = request.env['tw.whatsapp.message'].sudo().search([
                    ('whatsapp_id','=',message_id),
                    ('state','in',('pending','received')),
                    ('message_type','=','outbox')
                ],order='create_date DESC',limit=1)
                if not msg_obj:
                    if phone.startswith('08'):
                        phone_number = tuple([phone, phone.replace(phone[0:2],'628')])
                    elif phone.startswith('62'):
                        phone_number = tuple([phone, phone.replace(phone[0:2],'0')])
                    msg_obj = request.env['tw.whatsapp.message'].sudo().search([
                        ('phone_number','in',phone_number),
                        ('date','>=',datetime.now().strftime('%Y-%m-%d')),
                        ('date','<=',(datetime.now() - relativedelta(days=30)).strftime('%Y-%m-%d')),
                        ('state','!=','read'),
                        ('message_type','=','outbox')
                    ],order='create_date DESC',limit=1)

                if msg_obj:
                    msg_vals = {'state': status}
                    if status == 'received':
                        msg_vals.update({'received_date': datetime.now()})
                    elif status == 'sent':
                        msg_vals.update({'sent_date': datetime.now()})
                    elif status == 'read':
                        msg_vals.update({'read_date': datetime.now()})
                    elif status == 'cancel':
                        msg_vals.update({'cancel_date': datetime.now()})
                    elif status == 'reject':
                        msg_vals.update({'reject_date': datetime.now()})

                    for msg in msg_obj:
                        if msg.model_name and msg.transaction_id:
                            wa_obj = request.env[msg.model_name].suspend_security().browse(msg.transaction_id)
                            if status == 'sent':
                                wa_obj.write({
                                    'state': 'follow_up',
                                    'follow_up_by': self._uid,
                                    'follow_up_on': datetime.now(),
                                    'follow_up_method': 'wa',
                                    'follow_up_status': 'contactable'
                                })
                            elif status == 'read':
                                wa_obj.write({
                                    'state': 'follow_up',
                                    'follow_up_by': self._uid,
                                    'follow_up_on': datetime.now(),
                                    'follow_up_method': 'wa',
                                    'follow_up_status': 'contactable'
                                })
                            elif status == 'cancel':
                                wa_obj.write({'state': 'next_follow_up'})
                            elif status == 'reject':
                                wa_obj.write({'state': 'next_follow_up'})
                        msg.write(msg_vals)
                else:
                    error_obj = request.env['tw.whatsapp.error.log'].sudo().search([
                        ('name','=','WABLAS API RECEIVE STATUS'),
                        ('description','=','Message tidak ditemukan di Outbox'),
                        ('data','=',str(json.dumps(post)))
                    ])
                    if not error_obj:
                        error_obj.sudo().create({
                            'name': 'WABLAS API RECEIVE STATUS',
                            'description': 'Message tidak ditemukan di Outbox',
                            'data': str(json.dumps(post))
                        })
                    # Response
                    response = response_json(response_code=200, data_in=json.dumps(post), message=None, status=True, is_api_log=False, data_count=1)
                    return response
            except Exception as e:
                error_obj = request.env['tw.whatsapp.error.log'].sudo().search([
                    ('name','=','WABLAS API RECEIVE STATUS'),
                    ('description','=',e),
                    ('data','=',str(json.dumps(post)))
                ])
                if not error_obj:
                    error_obj.sudo().create({
                        'name': 'WABLAS API RECEIVE STATUS',
                        'description': e,
                        'data': str(json.dumps(post))
                    })
                # Response
                response = response_json(response_code=200, data_in=json.dumps(post), message=None, status=True, is_api_log=False, data_count=1)
                return response
            # Response
            response = response_json(response_code=200, data_in=json.dumps(post), message=None, status=True, data_count=1)
            return response
        except Exception as e:
            # Response
            message = {"message": "Something went wrong, please contact system administrator!"}
            response = response_json(response_code=400, data_in=json.dumps(post), message=message, status=False, error_description=e, data_count=1)
            return response