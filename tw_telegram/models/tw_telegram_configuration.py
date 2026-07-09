#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import timedelta, datetime
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class twConfigurationTelegram(models.Model):
    _name = "tw.telegram.configuration"
    _description = "Configuration Telegram"

    # 7: defaults methods
    
    # 8: fields

    name = fields.Char('Name')
    telegram_username = fields.Char('Telegram Username')
    sequence = fields.Integer(default=10, help="Gives the sequence order when displaying a list of records.")

    # 9: relation fields
    company_id = fields.Many2one('res.company', "Branch")
    api_configuration_id = fields.Many2one('tw.api.configuration', 'API Configuration', domain=[('api_type_id.value','=','Telegram')])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('name','company_id')
    def _compute_display_name(self):
        for record in self:
            if record.company_id:
                name = f"[{record.company_id.name}] {record.name} "
            else:
                name = f"[{record.company_id.name}]"
            record.display_name = name

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('telegram_username'):
                if vals.get('telegram_username')[0] != '@':
                    vals['telegram_username'] = '@'+vals.get('telegram_username')
        return super(twConfigurationTelegram,self).create(vals)

    def write(self,vals):
        if vals.get('telegram_username'):
            if vals.get('telegram_username')[0] != '@':
                vals['telegram_username'] = '@'+vals.get('telegram_username')
        return super(twConfigurationTelegram,self).write(vals)
    
    def copy(self):
        raise Warning("Data Tidak dapat di duplicate.")

    def unlink(self):
        raise Warning("Maaf untuk saat ini, Tidak dapat menghapus data.")

    # 13: action methods

    # 14: private methods
    def is_spam_on_notification(self,last_notif_date,time_limit=15):
        if last_notif_date:
            notification_resend_time_limit = time_limit or self.env['ir.config_parameter'].sudo().get_param('tw_telegram.default_time_limit')
            if notification_resend_time_limit:
                time_difference = last_notif_date + timedelta(minutes=int(notification_resend_time_limit)) - datetime.now()
                minutes, seconds = divmod(time_difference.seconds, 60)
                time_difference_str = f'{minutes} menit {seconds} detik'
                if last_notif_date and last_notif_date >= datetime.now() - timedelta(minutes=int(notification_resend_time_limit)):
                    raise Warning(f'Notifikasi sudah dikirim. Mohon tunggu {time_difference_str} lagi.')