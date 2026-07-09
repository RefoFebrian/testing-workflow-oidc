#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
import json
import requests

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, AccessDenied, UserError
from bs4 import BeautifulSoup
# 5: local imports

# 6: Import of unknown third party lib


class epsMailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _notify_thread(self, message, msg_vals=False, **kwargs):
        # * Since 3 years ago, notify by email parameter is unused and deleted from odoo base, see Task-2710804 (Mail: Clean Mail.Thread API) Part-of: odoo/odoo#82167
        notify_thread = super(epsMailThread, self)._notify_thread(message, msg_vals=msg_vals, **kwargs)
        
        self._notif_by_telegram(message, notify_thread, msg_vals=msg_vals, **kwargs)
        return notify_thread

    def _notif_by_telegram(self, message, recipients_data, msg_vals=False, **kwargs):
        message_partner_ids = msg_vals.get('partner_ids')
        if message_partner_ids:
            inbox_pids = [recipient['id'] for recipient in recipients_data if recipient['notif'] == 'telegram' and recipient['id'] in message_partner_ids]
            if inbox_pids:
                author_id = message.author_id.id
                model_obj = self.env['ir.model'].sudo().search([('model','=',message.model)])
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                url = f"{base_url}/web#id={message.res_id}&model={message.model}&view_type=form"
                
                message_from = BeautifulSoup(message.email_from, 'html.parser').get_text()
                title = msg_vals['record_name']
                content_message = BeautifulSoup(message.body, 'html.parser').get_text()
                user_ids = self.env['res.users'].search([('partner_id','in',inbox_pids)])

                button = [
                        [
                            {
                                "text" : "Open",
                                "url" : url
                            }
                        ]
                    ]
                
                recipient_names = ', '.join(name.title() for name in user_ids.mapped('name'))
                message = f"""#MessageApolon\nFrom : {message_from}\nTo : {recipient_names}\nSubject : {model_obj.name} - {title}\n\n{content_message}"""
                
                for user in user_ids: 
                    user.send_telegram_message(message,button_params=button)

                #Pengirim chater akan di kirimkan juga untuk notif telegram
                user_author_id = self.env['res.users'].sudo().search([('partner_id','=',author_id)],limit=1)
                
                if user_author_id.notification_type == 'telegram' and user_author_id.telegram_is_send_notif_to_sender:
                    user_author_id.send_telegram_message(message,button_params=button)

        return True


        