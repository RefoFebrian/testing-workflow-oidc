#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
import json
import requests

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib

class WebTelegramUser(models.Model):
    _inherit = "res.users"
    
    telegram_user = fields.Char(string='User Telegram')
    telegram_chat_id = fields.Char(string='Chat ID')
    telegram_is_delete_after_action = fields.Boolean(string='Delete Chat after Action?')
    notification_type = fields.Selection(selection_add=[('telegram', 'Handle by Telegram')],ondelete={'telegram': 'set default'})
    telegram_is_send_notif_to_sender = fields.Boolean(string='Sender Receive Notification?')

    def get_config(self):
        config = self.env['tw.api.configuration']

        config_obj = config.suspend_security().search([
            ('api_type_id.value','=','Telegram'),
            ('name','=','Apolon Bot')
        ],limit=1)
        if not config_obj:
            config_obj = config.suspend_security().search([
                ('api_type_id.value','=','Telegram')
            ],limit=1)
            
        return config_obj
    
    def get_token(self):
        config = self.get_config()
        bot_token = config.api_secret
        return bot_token

    def get_user_chat_id(self):
        bot_config = self.get_config()
        bot_token = bot_config.api_secret
        if not bot_token:
            raise UserError(_("Bot token is not set, please create a new bot called 'Apolon Bot' on API Configuration"))
        if not self.telegram_user:
            raise UserError(_(f"Telegram user on {self.name} is not set, please set the username on 'User Telegram' field"))
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
        response = requests.get(url)
        if response.status_code == 200:
            content = json.loads(response.content)
            result = content.get('result')
            for data in result:
                message = data.get('message')
                chat = message.get('chat')
                user_name = chat.get('username')
                chat_id = chat.get('id')
                if user_name == self.telegram_user:
                    self.sudo().write(
                        {"telegram_chat_id" : chat_id}
                    )
                    return True
            raise UserError(_(f"[{self.name}] Chat not found, make sure you have send a message to the bot. \n 1. Open telegram and search @{bot_config.client_id} \n 2. Click Start"))

    def send_telegram_message(self, message, bot_token=False, button_params=False, client_id=False):
        if not bot_token:
            bot_token = self.get_token()
        if not bot_token:
            raise UserError(_("Please enter bot token, or create a new bot called 'Apolon Bot' on API Configuration"))
        if not self.telegram_chat_id:
            self.get_user_chat_id()

        # Preceding some Characters
        # https://core.telegram.org/bots/api#formatting-options
        char_list = ['_', '*', '~', '`', '>', '|']
        for char in char_list:
            replacer = "\\" + char
            message = message.replace(char,replacer)
        
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

        payload = {
            "text": message,
            "parse_mode": "markdown",
            "disable_web_page_preview": False,
            "disable_notification": False,
            "reply_to_message_id": None,
            "chat_id": self.telegram_chat_id
        }

        # Jika ada Client ID (Group Support) maka update payload
        if client_id:
            payload['chat_id'] = client_id

        if button_params:
            # This is the example of button_params
            # [[{
            #    "text" : "Open link",
            #    "url" : "http://example.com"
            # }]]
            payload["reply_markup"] = {"inline_keyboard" : button_params}
        headers = {
            "accept": "application/json",
            "User-Agent": "Telegram Bot SDK - (https://github.com/irazasyed/telegram-bot-sdk)",
            "content-type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            content = json.loads(response.content)
            result = content.get('result')
            message_id = result.get('message_id')
            return message_id        
        return False
    
    def delete_user_telegram_message(self, message_id, bot_token=False, check_is_delete=False):
        # Cek dulu, mau di hapus atau tidak.
        if check_is_delete:
            if not self.telegram_is_delete_after_action:
                return True
            
        if not bot_token:
            bot_token = self.get_token()
        if not bot_token:
            raise UserError(_("Please enter bot token, or create a new bot called 'Apolon Bot' on API Configuration"))
        if not self.telegram_chat_id:
            self.get_user_chat_id()

        self.delete_telegram_message(message_id, self.telegram_chat_id,bot_token,check_is_delete)
    
    def delete_telegram_message(self, message_id, chat_id, bot_token=False, check_is_delete=False):
        # Cek dulu, mau di hapus atau tidak.
        if check_is_delete:
            user_id = self.env['res.users'].sudo().search([('telegram_chat_id','=',chat_id)],limit=1)
            if not user_id.telegram_is_delete_after_action:
                return True
            
        if not bot_token:
            bot_token = user_id.get_token()
        if not bot_token:
            raise UserError(_("Please enter bot token, or create a new bot called 'Apolon Bot' on API Configuration"))

        url = f'https://api.telegram.org/bot{bot_token}/deleteMessage'

        payload = {
            "parse_mode": "markdown",
            "disable_web_page_preview": False,
            "disable_notification": False,
            "reply_to_message_id": None,
            "chat_id": chat_id,
            "message_id": message_id,
        }
        headers = {
            "accept": "application/json",
            "User-Agent": "Telegram Bot SDK - (https://github.com/irazasyed/telegram-bot-sdk)",
            "content-type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        print(response.text)

    def action_generate_chat_id(self):
        form_id = self.env.ref('tw_telegram.view_profile_telegram_wizard_view_form').id
        return {
            'name': ('Generate Chat ID'),
            'res_model': 'res.users',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(form_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'view_type': 'form',
            'res_id': self.id,
            'context':{
                'default_is_generate': True,
            },
        }  

