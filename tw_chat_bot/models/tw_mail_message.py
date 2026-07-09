# -*- coding: utf-8 -*-

# 1: imports of python lib
import time
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib
from markupsafe import Markup

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
import requests
import json

import logging
_logger = logging.getLogger(__name__)


class TwMailMessage(models.Model):
    _inherit = "mail.message"

    chatbot_message_id = fields.Char(string='Chatbot Message ID')
    chatbot_conversation_id = fields.Char(string='Chatbot Conversation ID')
    chatbot_space_id = fields.Char(string='Chatbot space ID')

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        msgs = super().create(vals_list)
        for msg in msgs:
            sender = msg.author_id
            if msg.model == 'discuss.channel':
                try:
                    channel = self.env[msg.model].browse(msg.res_id)
                    participants = channel.channel_partner_ids  # all partners in that DM
                    receivers = participants - sender
                    for partner in receivers:
                        if partner.name in ('AI - Data KPB'):
                            msg.get_reply_from_ai(partner)
                except Exception as e:
                    _logger.error("Cant get reply from AI! %s" %(str(e)))
        return msgs
    
    def get_reply_from_ai(self,partner):
        if self.record_name.split(',')[0] =='AI - Data KPB':
            space_id = '01f0347ef5ed1d8bab6d739bdeeee2f0'
        else: 
            return False
        base_url = "https://adb-2343663971966163.3.azuredatabricks.net"
        token = self.get_databricks_token()

        # search conversation_id
        # TODO : Activate search by date schema, or we can apply spesific comand to reset the conversation
        yesterday = fields.Date.today() - relativedelta(days=1)
        last_conversation = self.search([
            ('chatbot_conversation_id', '!=', False),
            ('res_id', '=', self.res_id),
            ('model', '=', self.model),
            # ('create_date', '>', yesterday),
            ],order='id desc', limit=1)
        if last_conversation:
            reply,conversation_id,message_id = self.reply_conversation(base_url, token, space_id, last_conversation.chatbot_conversation_id)
        else:
            # start conversation
            reply,conversation_id,message_id = self.start_conversation(base_url, token, space_id)

        # 2) find the actual record this message belongs to
        #    `self.model` is the string name of the model,
        #    `self.res_id` is the record’s ID
        target = self.env[self.model].browse(self.res_id)

        # 3) post the reply to that record’s chatter
        #    you can limit notifications to the original author if you like:
        partner_ids = [self.author_id.id] if self.author_id else None

        # TODO : Fix error concurrent update when posting message
        target.message_post(
            body=Markup(reply),
            author_id=partner.id,
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
            partner_ids=partner_ids,
            parent_id=self.id,
            chatbot_message_id=message_id,
            chatbot_conversation_id=conversation_id, 
            chatbot_space_id=space_id
        )

    def start_conversation(self,base_url, token, space_id):
        payload = json.dumps({
            "content": self.preview
        })
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+token
        }
        url = f"{base_url}/api/2.0/genie/spaces/{space_id}/start-conversation"
        response = requests.request("POST", url, headers=headers, data=payload)
        response = response.json()
        conversation_id = response.get('conversation_id')
        message_id = response.get('message_id')
        message = self.get_response_message(base_url, token, space_id, conversation_id, message_id)
        return message,conversation_id,message_id
    
    def reply_conversation(self,base_url, token, space_id, conversation_id):
        payload = json.dumps({
            "content": self.preview
        })
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+token
        }
        url = f"{base_url}/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages"

        response = requests.request("POST", url, headers=headers, data=payload)
        response = response.json()
        conversation_id = response.get('conversation_id')
        message_id = response.get('message_id')
        message,conversation_id,message_id = self.get_response_message(base_url, token, space_id, conversation_id, message_id)
        return message,conversation_id,message_id

    def get_response_message(self,base_url, token, space_id, conversation_id, message_id):
        payload = json.dumps({})
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+token
        }
        url = f"{base_url}/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}"
        print('url response_message:', url)
        response = requests.request("GET", url, headers=headers, data=payload)
        response = response.json()
        status = response.get('status')
        print('Status :', status)
        while status in ('FETCHING_METADATA','FILTERING_CONTEXT','ASKING_AI','PENDING_WAREHOUSE','EXECUTING_QUERY'):
            time.sleep(3)
            response = requests.request("GET", url, headers=headers, data=payload)
            response = response.json()
            status = response.get('status')
            print('Status :', status)
        
        if status != 'COMPLETED':
            return "Error: "+response.get('error') +'\n please try again.'
        
        message_id = response.get('message_id')
        attachments = response.get('attachments')
        msg = ''
        for attachment in attachments:
            attachment_id = attachment.get('attachment_id')
            text = attachment.get('text')
            query = attachment.get('query')
            if text:
                msg += text.get('content')
                msg += '<br/>'

            if query:
                table_of_content = self.get_response_data(base_url, token, space_id, conversation_id, message_id, attachment_id)
                msg += query.get('description')
                msg += '<br/>'
                msg += table_of_content
            elif attachment_id:
                table_of_content = self.get_response_data(base_url, token, space_id, conversation_id, message_id, attachment_id)
                msg += '<br/>'
                msg += table_of_content
        msg = msg.replace('\n','<br/>')
        return msg,conversation_id,message_id
    
    def get_response_data(self,base_url, token, space_id, conversation_id, message_id, attachment_id):
        payload = json.dumps({})
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer '+token
        }
        url = f"{base_url}/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}"
        print('url:', url)
        response = requests.request("GET", url, headers=headers, data=payload)
        response = response.json()
        return self.format_table_from_response(response)

    def format_table_from_response(self, response):
        if not response:
            return ""
        data = response.get('statement_response')
        schema = data.get('manifest', {}).get('schema', {})
        columns = schema.get('columns', [])
        rows = data.get('result', {}).get('data_array', [])

        # 2. Build the HTML table
        #   a) headers
        header_html = ''.join('<th>%s</th>' % col['name'] for col in columns)
        #   b) rows
        body_html = ''
        for row in rows:
            # if you need to format the timestamp:
            cells = []
            for i, cell in enumerate(row):
                if columns[i]['type_name'] == 'TIMESTAMP':
                    # parse and re-format to readable date
                    dt = datetime.fromisoformat(cell.replace('Z',''))
                    cells.append('<td>%s</td>' % dt.strftime('%Y-%m-%d'))
                else:
                    cells.append('<td>%s</td>' % cell)
            body_html += '<tr>%s</tr>' % ''.join(cells)

        table_html = """
        <table border="1" cellspacing="0" cellpadding="4">
          <thead><tr>%s</tr></thead>
          <tbody>%s</tbody>
        </table>
        <br/>
        """ % (header_html, body_html)
        return table_html

    def get_databricks_token(self):
        response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 200:
            data = response.json()
            return data.get('token_value')
        else:
            raise Warning(_("Error getting token from Databricks API: %s") % response.text)