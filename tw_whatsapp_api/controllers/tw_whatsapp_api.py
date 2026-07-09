import odoo.http as http
import requests
from odoo.http import Response,request
from odoo import models, fields, api
from odoo.addons.rest_api.controllers.main import *
from datetime import date,timedelta,datetime,date
import logging
import os
_logger = logging.getLogger(__name__)
try:
    import simplejson as json
except ImportError:
    import json


class FileController(http.Controller):
    @http.route('/api/whatsapp/invoice_download', methods=['GET'], type='http', auth='public')
    def download_file(self, **params):
        config_files = request.env['tw.config.files'].search([('code','=','file_whatsapp')],limit=1)
        if not config_files:
            return 'Config Download File Belum Tersedia.'
        
        filename = params.get('filename')
        if filename:
            file_path = '{path}/{filename}'.format(path=config_files.local_path,filename=filename)
        else:
            return 'File Belum Tersedia'
        
        if os.path.exists(file_path):
            return http.send_file(
                file_path,
                filename=os.path.basename(file_path),
                as_attachment=True,
                mimetype='application/octet-stream'
            )
        else:
            return 'File Belum Tersedia'


class WhatsappApi(http.Controller):
    @http.route('/api/whatsapp/receive_whatsapp_webhook', methods=['POST'], auth="public", type="json", csrf=False)
    def receive_whatsapp_webhook(self, **params):
        try:
            for data in params['statuses']:
                status = data['status']
                alasan_failed = False
                if status == 'read':
                    wa_id = data['id']
                elif status == 'delivered':
                    wa_id = data['conversation']['id']
                    status = 'delivered'
                elif status == 'failed':
                    wa_id = data['id']
                    alasan_failed = data['errors'][0]['title']
                    
                wa_outbox_obj = request.env['tw.whatsapp.message'].search([('whatsapp_id','=',wa_id),('message_type','=','outbox')])
                wa_outbox_obj.write({
                    'state':status,
                    'note':alasan_failed,
                })
                
                result = {
                    'description': 'Success',
                    'detail': 'Succes Executed Record WA with whatsapp_id = ' + wa_outbox_obj.whatsapp_id,
                    'status': 1,
                    'status_code': 200
                }
        except Exception as err:
            _logger.error('There\'s an error while executing code!\n\
                {}'.format(str(err)))
            result = {
                'description': 'There\'s an error while executing code!',
                'detail': str(err),
                'status': 0,
                'status_code': 400
            }
        return result