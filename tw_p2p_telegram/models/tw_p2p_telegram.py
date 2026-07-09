# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
import math

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwP2pPurchaseOrderInherit(models.Model):
    _inherit = "tw.p2p.purchase.order"
    
    # 7: defaults methods
    
    # 8: fields
    notification_last_message_id = fields.Integer(string='Last Message ID')
    notification_last_chat_id = fields.Float(string='Last Chat ID', digits=(15, 0))
    notification_start_send_date = fields.Datetime('Notified Reminder P2P on')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_send_telegram_notification_start_reminder(self):
        self.env['tw.telegram.configuration'].sudo().is_spam_on_notification(self.notification_start_send_date)
        if self.user_id:
            if self.user_id.telegram_user:
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                url = f"{base_url}/web#id={self.id}&model=tw.p2p.purchase.order&view_type=form"
                message = f"Hai {self.suspend_security().user_id.name}, terdapat outstanding Confirm P2P dengan nomor '{self.name}'.Silahkan tekan 'Open P2P' untuk lihat detail."
                button = [
                       [ 
                           {
                            "text" : "Open P2P",
                            "url" : url
                            }
                        ]
                ]
                # Delete message, supaya tidak menumpuk
                if self.notification_last_message_id:
                    self.env['res.users'].suspend_security().delete_telegram_message(self.notification_last_message_id,chat_id=self.notification_last_chat_id,check_is_delete=True)
                # Send Notification
                message_id = self.user_id.send_telegram_message(message,button_params=button)
                self.write({
                    'notification_last_message_id': message_id,
                    'notification_last_chat_id': self.user_id.telegram_chat_id,
                    'notification_start_send_date':datetime.now(),
                })
                return True
            
    # 14: private methods
    def schedule_send_telegram(self):
        from datetime import timedelta
        interval_days = int(self.env['ir.config_parameter'].sudo().get_param('Interval Days Reminder P2P', 2))
        today = fields.Date.today()
        
        # Search records waiting for verification
        records = self.search([
            ('state', '=', 'waiting_for_verification'),
            ('waiting_for_verification_date', '!=', False),
        ])
        
        # Filter by date - reminder if X days after verification request
        target_date = today - timedelta(days=interval_days)
        
        for record in records:
            if record.waiting_for_verification_date and record.waiting_for_verification_date.date() <= target_date:
                record.action_send_telegram_notification_start_reminder()