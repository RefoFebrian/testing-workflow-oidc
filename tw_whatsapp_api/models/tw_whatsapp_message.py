# -*- coding: utf-8 -*-
from datetime import datetime, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

import logging
import uuid
import requests
import json

_logger = logging.getLogger(__name__)

class WhatsappMessage(models.Model):
    _name = "tw.whatsapp.message"
    _description = "Whatsapp Integration"

    def _get_default_date(self):
        return date.today()
    
    @api.depends('filename')
    def compute_attachment(self):
        for record in self:
            if record.filename:
                attachment_file = self.env['tw.config.files'].suspend_security().get_file('file_whatsapp',record.filename)
                record.file = attachment_file
            else:
                record.file = False

    whatsapp_id = fields.Char(string="ID Whatsapp")
    name = fields.Char(string="Nama Penerima")
    phone_number = fields.Char(string="Nomor Telepon")
    filename = fields.Char(string="Nama File")
    file_type = fields.Char(string="Tipe berkas")
    origin = fields.Char(string="Origin")
    sender_name = fields.Char("Nama Pengirim")
    sender_number = fields.Char("Nomor Pengirim")
    attachment_name = fields.Char("Nama Berkas")
    attachment_url = fields.Char("URL Berkas")
    note = fields.Char(string="Keterangan")

    message = fields.Text(string="Pesan")

    is_official_whatsapp = fields.Boolean('Is Sending by Official Config?', compute="_compute_is_official_whatsapp", store=True)

    file = fields.Binary(string="Upload Berkas", compute="compute_attachment")

    state = fields.Selection(selection=[
        ("draft", "Draft"),
        ("sent","Sent"), # Received by Wablas server
        ("cancel","Cancel"),
        ("failed","Failed"),
        ("delivered","Delivered"), # Sent to recipient
        ("read","Read")
    ], readonly=True, string="Status", default="draft")
    message_type = fields.Selection([
        ('outbox', 'Outbox'),
        ('inbox', 'Inbox')
    ], string="Message Type")

    date = fields.Date(string="Tanggal", default=_get_default_date)
    scheduled_date = fields.Datetime(string="Jadwal Kirim") # UTC
    received_date = fields.Datetime(string="Tanggal Diterima")
    sent_date = fields.Datetime(string="Tanggal Kirim")
    read_date = fields.Datetime(string="Tanggal Dibaca")
    cancel_date = fields.Datetime(string="Tanggal Cancel")
    failed_date = fields.Datetime(string="Tanggal Gagal Kirim")
    message_received_date = fields.Datetime(string="Tanggal Pesan Diterima")

    cancel_uid = fields.Many2one('res.users',string="Cancelled by")
    template_id = fields.Many2one('tw.whatsapp.content.template', string='Template')
    company_id = fields.Many2one("res.company", string="Branch", ondelete="restrict", domain="[('parent_id', '!=', False)]")
    whatsapp_detail_ids = fields.One2many('tw.whatsapp.message.detail','whatsapp_id')

    def _check_phone_number(self, phone_number):
        if not phone_number:
            raise Warning('Nomor Telepon tidak boleh kosong!')
        if phone_number[:3] != '628':
            if phone_number[:4] != '0721':
                if phone_number[0] not in ('+','0'):
                    raise Warning('No HP harus diawali dengan +62 atau 08')
                elif phone_number[0] == '+' or phone_number[0] == '0':
                    if phone_number[:3] == '+62':
                        phone_number = phone_number.replace(phone_number,phone_number[1:])
                    elif phone_number[0] == '0':
                        phone_number = phone_number.replace(phone_number, '62' + phone_number[1:])
            else:
                raise Warning ('Silahkan gunakan nomor Whatsapp handphone Anda !')
        return phone_number
        
    def _check_type(self, ext):
        types = ['jpg','jpeg','png','gif','doc','docx','pdf','odt','csv','ppt','pptx','xls','xlsx','mp3','ogg']
        if ext not in types:
            raise Warning('Tipe berkas %s tidak didukung oleh sistem!' % (str(ext).upper()))
        if ext in ['jpg','jpeg','png','gif']:
            return 'image'
        elif ext in ['doc','docx','pdf','odt','csv','ppt','pptx','xls','xlsx','mp3','ogg']:
            return 'docs'
    
    @api.depends('name','phone_number')
    def _compute_display_name(self):
        for record in self:
            if record.name:
                name = f"[{record.phone_number}] {record.name} "
            else:
                name = f"[{record.phone_number}]"
            record.display_name = name

    @api.depends('template_id')
    def _compute_is_official_whatsapp(self):
        for record in self:
            record.is_official_whatsapp = record.template_id.is_official

    @api.model_create_multi
    def create(self,vals_list):
        file_list = []
        for vals in vals_list:
            if vals['message_type'] == 'outbox':
                vals['phone_number'] = self._check_phone_number(vals['phone_number'])

                # Avoid spam
                duplicate_outbox = self.suspend_security().search([
                    ('phone_number','=',vals['phone_number']),
                    ('template_id','=',vals['template_id']),
                    ('origin','=',vals['origin']),
                    ('date','=',date.today()),
                    ('state','not in',('cancel','failed'))
                ],limit=1)
                if duplicate_outbox:
                    return duplicate_outbox

                if vals.get('file'):
                    if vals.get('filename'):
                        filename_upload_tokens = str(vals.get('filename')).split('.')
                        vals['file_type'] = self._check_type(filename_upload_tokens[len(filename_upload_tokens) - 1])
                    vals['file'] = False
                file_list.append(vals.get('file',False))
        ids = super(WhatsappMessage, self).create(vals_list)
        for object_id, create in enumerate(ids):
            if file_list[object_id] :
                self.env['tw.config.files'].suspend_security().upload_file('file_whatsapp',create.filename, file_list[object_id])            
        return ids
    
    def write(self, vals):
        if vals.get('name'):
            vals['name'] = str(vals['name']).strip().upper()

        if vals.get('file'):
            if not vals.get('filename'):
                vals['file_type'] = False
            else:
                filename_upload_tokens = str(vals.get('filename')).split('.')
                vals['file_type'] = self._check_type(filename_upload_tokens[len(filename_upload_tokens) - 1])
            file_upload = vals['file']
            vals['file'] = False
        else:
            file_upload = False

        if file_upload:
            self.env['tw.config.files'].suspend_security().upload_file('file_whatsapp',vals.get('filename'), file_upload)
            vals['filename'] = vals.get('filename')
        return super(WhatsappMessage, self).write(vals)

    def action_cancel_whatsapp(self):
        self.write({
            'cancel_uid': self._uid,
            'state': 'cancel',
            'cancel_date': datetime.now()
        })

    def schedule_send_whatsapp_outbox(self,limit=10):
        query = """
            SELECT id 
            FROM tw_whatsapp_message
            WHERE state = 'draft' 
            AND message_type = 'outbox'
            ORDER BY create_date ASC 
            LIMIT %d; 
        """ %(limit)
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        for data_outbox in ress:
            outbox_obj = self.browse(data_outbox.get('id'))
            outbox_obj.action_send()

    def get_whatsapp_api_config(self):
        """
        Generate WhatsApp API configuration based on branch settings and template type.
        
        :return: Dictionary containing API configuration (url, headers, subject, etc.)
        """
        self.ensure_one()
        payload = {}
        
        # Step 1: Retrieve branch setting for the current company_id
        company_id = self.company_id.id or self.env.company.id
        branch_setting = self.env['tw.branch.setting'].sudo().search([
            ('company_id', '=', company_id)
        ], limit=1)
        
        if not branch_setting:
            raise Warning('Branch setting not found for company %s.' % (self.company_id.name))
        
        # Step 2: Check template_id.is_official
        is_official = self.template_id.is_official if self.template_id else False
        
        # Step 3: Load the corresponding tw.api.configuration from branch setting
        if is_official:
            config = branch_setting.official_wa_config_id
        else:
            config = branch_setting.unofficial_wa_config_id
        
        if not config:
            config_type = "Official" if is_official else "Un-Official"
            raise Warning('Configuration API WhatsApp (%s) belum dipilih di Branch Setting untuk branch %s.' % (config_type, branch_setting.name))
        
        # Step 4: Generate the request payload based on the selected configuration
        payload['headers'] = {
            'Authorization': config.api_key,
            'Content-Type': 'application/json'
        }
        
        # ---- Endpoint handling ----
        if is_official:
            subject = self.template_id.subject if self.template_id else config.name
            payload.update({
                'url': f"{config.base_url}/api/v1/send-message",
                'subject': subject,
                'is_official': True,
            })
        else:
            payload.update({
                'url': f"{config.base_url}/api/send-message",
                'is_official': False,
            })
        
        # Add config reference for debugging/logging
        payload['config_id'] = config.id
        payload['config_name'] = config.name
        
        return payload

    def create_log_api(self, vals, url, headers, status_code, description, status, response):
        """Create API log for WhatsApp message sending.

        :param response: requests.Response object or fallback value (str, None, False)
        """
        if isinstance(response, requests.Response):
            response_body = json.dumps(response.json())
            response_code = str(response.status_code)
            log_status = 'success' if response.status_code == 200 else 'error'
        else:
            response_body = json.dumps({'error': str(response)}) if response else json.dumps({})
            response_code = str(status_code)
            log_status = 'error'

        self.env['tw.api.log'].suspend_security().create_api_log(
                name=f"WhatsApp API - {self.origin} - {self.name}",
                url=url,
                description=f"API Call: {url}",
                ip_address=url,
                response=response_body,
                payload=json.dumps(vals),
                header=json.dumps(headers),
                response_code=response_code,
                status_code=log_status,
            )

    def action_send(self):
        config = self.get_whatsapp_api_config()
        is_official = config.get('is_official')
        message = str(self.message).replace('\\n', '\n')
        data = {
            'phone': self.phone_number,
            'message': message,
        }

        if is_official:
            data = {
                'id': str(uuid.uuid4()),
                'subject': config.get('subject'),
                'address': str(self.phone_number),
                'imType': 'whatsapp',
                'contentType': 'text',
                'text': message,
            }

        try:
            url = config.get('url')
            headers = config.get('headers')
            response = requests.post(url=url, json=data, headers=headers)
            content = json.loads(response.content)
            if response.status_code == 200:
                whatsapp_id = content.get('id') or content['data']['messages'][0]['id']
                self.write({
                    'whatsapp_id': whatsapp_id,
                    'state': 'sent',
                    'sent_date': datetime.now()
                })

            else:
                error_message = str(content.get('message')) if content and content.get('message') else f"Error Send Message Whatsapp untuk transaksi { self.origin }"
                self.write({
                    'note': error_message,
                    'state': 'failed',
                    'failed_date': datetime.now()
                })
                self.create_log_api(data, url, headers, response.status_code, error_message, False, response)
                _logger.error(error_message)
                return False

        except Exception as err:
            error_message = f"Error Send Message Whatsapp ({self.id}): {err}"
            self.create_log_api(data, url, headers, 400, error_message, False, error_message)
            _logger.error(error_message)
            return False
    
    def _prepare_create_whatsapp_message(self, params=[]):
        """
        Global method to prepare and create tw.whatsapp.message records.
        
        :param params: List of dictionaries containing message data
        :return: List of dictionaries containing validated vals for record creation
        
        Required fields: name, origin, company_id, phone_number, template_id, message
        """
        if not params:
            _logger.warning("Parameter 'params' is empty or not provided.")
            return []
        
        # Get all available fields in the model
        model_fields = self._fields.keys()
        result = []
        
        for record in params:
            if not isinstance(record, dict):
                _logger.warning(f"Record is not a dictionary, skipping: {record}")
                continue
            
            # Required fields with default values
            vals = {
                'name': record.get('name'),
                'origin': record.get('origin'),
                'company_id': record.get('company_id'),
                'phone_number': record.get('phone_number'),
                'template_id': record.get('template_id'),
                'message': record.get('message'),
                'message_type': 'outbox'
            }
            
            # Validate and add additional keys from params
            for key, value in record.items():
                if key not in model_fields:
                    _logger.warning(
                        f"Key '{key}' is not detected as a field in model 'tw.whatsapp.message'. "
                        f"This key will be ignored."
                    )
                elif key not in vals:
                    # Add valid key to vals if not already in required fields
                    vals[key] = value
            
            # Append dictionary to result
            result.append(vals)
        
        return result

