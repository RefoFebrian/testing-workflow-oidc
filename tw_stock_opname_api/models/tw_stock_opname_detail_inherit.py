#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class StockOpnameDetailInherit(models.Model):

    _inherit = "tw.stock.opname.detail"

    is_notification_firebase = fields.Boolean(string="Is Notification Firebase", default=False)

    # 13: private methods
    def android_firebase_notif_history_photo(self):
        history_photo = self.env['tw.stock.opname.detail'].sudo().search(
            [
                ('state','!=','open'),
                ('filename_upload','=',False),
                ('opname_id.division','=','Unit'),
                ('opname_id.state','=','in_progress'),
                ('is_notification_firebase','=',False)
            ],limit=1)
        if history_photo :
            for var in history_photo :
                template = self.env['tw.firebase.content.template'].search([('name','=','Stock Opname Outstanding Photo')],limit=1)
                if not template:
                    raise Warning("Template pesan 'Stock Opname Outstanding Photo' tidak ditemukan")
                pesan = template.content
                pesan = pesan.replace("%penerima%",var.employee_id.name)
                pesan = pesan.replace("%transaction_number%",var.opname_id.name)
                pesan = pesan.replace("%engine_number%",var.lot_id.name)
                messages = {
                        'name':'Stock Opname Outstanding Photo',
                        'company_id':var.employee_id.company_id.id,
                        'message':pesan,
                        'employee_receiver_id':var.employee_id.id,
                        'category_id':self.env['tw.firebase.notification.category'].sudo().search([('name','=','Notification Stock Opname Outstanding Photo')],limit=1).id,
                    }   
                
                create_message_data= self.env['tw.firebase.notification'].sudo().create(messages)
                if create_message_data :
                    var.write({'is_notification_firebase':True})
                    obj_token=self.env['tw.firebase.user'].search([('user_id','=',var.employee_id.user_id.id),('active','=',True)])
                    if obj_token :
                        for token in obj_token :
                            message_title = 'Stock Opname Outstanding Photo'
                            message_body  = 'Nomor Stock Opname %s'  % (var.opname_id.name)
                            data = {
                                    "priority" : "normal",
                                    "notification" : {
                                    "id" : create_message_data.id,
                                    "body" : "%s"%(message_body),
                                    "title" : "%s"%(message_title),
                                    "icon" : "logo_sahabat_tunas",
                                    "model" : "tw.firebase.message",
                                },
                                "data" : {
                                    "text" : " "
                                }
                            }

                    obj_firebase_user = self.env['tw.firebase.user'].search([('user_id','=',create_message_data.employee_receiver_id.user_id.id),('active','=',True)])
                    if obj_firebase_user :
                        for token in obj_firebase_user :
                            send = obj_firebase_user.notify_single_device(token.firebase_token, data,'So-Unit')
                            create_message_data.write({'send_date':self._get_default_datetime(),'state':'unread'})
