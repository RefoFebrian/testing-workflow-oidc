#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import timedelta, datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError as Warning

import logging
_logger = logging.getLogger(__name__)

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

STATES = [('draft','Draft'),('send','Send')]

class FirebaseMessage(models.Model):

    _name = "tw.firebase.message"
    _description = "Firebase Message"
    _order = "name desc"

    # 7: defaults methods
    
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    # 8: fields
    name = fields.Char( required=True, string="Name",  help="")
    message = fields.Html(string='Message')
    send_all_user = fields.Boolean( string="Send to all users",  readonly=True,  help="")
    transaction_id = fields.Integer( string="Transaction",  readonly=True,  help="")
    model_name = fields.Char( string="Model name",  readonly=True,  help="")
    state = fields.Selection(selection=STATES, readonly=True, default=STATES[0][0],  string="State",  help="")
    
    # 8: relation fields
    reply_to_message_id = fields.Many2one(comodel_name="tw.firebase.message",  string="Reply to message",  readonly=True,  help="")
    employee_sender_id = fields.Many2one(comodel_name="hr.employee",  string="Employee sender",  readonly=True,  help="", default=lambda self: self.env.uid)
    company_id = fields.Many2one(comodel_name="res.company",  string="Branch",  readonly=True, help="", default=lambda self: self.env.company)
    content_template_id = fields.Many2one(comodel_name="tw.firebase.content.template",  string="Template Pesan",  readonly=True,  help="")
    firebase_message_line_ids = fields.One2many(comodel_name="tw.firebase.message.line",  inverse_name="firebase_message_id",  string="Firebase message lines",  readonly=True,  help="")

    # 9: constraints & sql constraints

    # 10: compute/depends & on change methods
    @api.onchange('content_template_id')
    def _onchange_content_template_id(self):
        self.message = False
        if self.content_template_id:
            self.message = self.content_template_id.content

    # 11: override methods
    # 
    # def name_get(self, context=None):
        # return super(FirebaseMessage, self).name_get(context)

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
        # return super(FirebaseMessage, self).name_search(name, args, operator, limit)

    # @api.model
    # def create(self, vals):
        # return super(FirebaseMessage, self).create(vals)

    # 
    # def write(self, vals):
        # return super(FirebaseMessage, self).write(vals)

    # 
    # def unlink(self):
        # for x in self:
            # if x.state != 'draft':
                # raise Warning('Perhatian!\nData tidak bisa dihapus.')
                # return super(FirebaseMessage, self).unlink()

    # 
    # def copy(self):
        # raise Warning('Perhatian!\nData tidak bisa diduplikasi.')
        # return super(FirebaseMessage, self).copy()


    # 12: action methods
    def action_send(self):
        if not self.firebase_message_line_ids and not self.send_all_user :
             raise Warning('Perhatian ! \n Penerima Harus di Isi !')
        message_title = self.employee_sender_id.name,
        message_body  = self.name,
        
        if self.send_all_user :
            obj_token=self.env['tw.firebase.user'].search([('active','=',True)])
            if obj_token :
                for emp in obj_token :
                    obj_employee = self.env['hr.employee'].sudo().search([('user_id','=',emp.user_id.id)])
                    if obj_employee :
                        for employee in obj_employee :
                            message_line = {
                                'messages_firebase_id': self.id,
                                'employee_receiver_id' :employee.id,               
                            }
                            create_line = self.env['tw.firebase.message.line'].create(message_line)
                            if  create_line :
                                data = {
                                "priority" : "normal",
                                "notification" : {
                                    "id" : create_line.id,
                                    "body" : "%s"%(message_body),
                                    "title" : "%s"%(message_title),
                                    "icon" : "logo_sahabat_tunas",
                                    "model" : "tw.firebase.message",
                                },
                                "data" : {
                                    "text" : " "
                                    }
                                }
                                send=self.env['tw.firebase.user'].notify_single_device(obj_token.firebase_token, data)
                                
                                # FCM HTTP v1 API response handling
                                if 'name' in send:
                                    # SUCCESS: Extract message ID from the 'name' field
                                    message_id_firebase = send['name']
                                    create_line.write({'message_id':message_id_firebase.split(":")[-1],'send_date':self._get_default_date(),'state':'unread'})
  
        else :
            if self.firebase_message_line_ids :
                for line in self.firebase_message_line_ids  :
                    user_firebase=self.env['tw.firebase.user'].search([('user_id','=',line.employee_receiver_id.user_id.id),('active','=',True)],limit=1)
                    if user_firebase :
                        data = {
                        "priority" : "normal",
                        "notification" : {
                            "id" : line.id,
                            "body" : "%s"%(message_body),
                            "title" : "%s"%(message_title),
                            "icon" : "logo_sahabat_tunas",
                            "model" : "tw.firebase.message",
                        },
                        "data" : {
                            "text" : " "
                            }
                        }
                        send=self.env['tw.firebase.user'].notify_single_device(user_firebase.firebase_token, data)
                        
                        # FCM HTTP v1 API response handling
                        if 'name' in send:
                            # SUCCESS: Extract message ID from the 'name' field
                            message_id_firebase = send['name']
                            line.write({'message_id':message_id_firebase.split(":")[-1],'send_date':self._get_default_date(),'state':'send'})
                        
        self.write({'state':'send'})

    # 13: private methods
    def android_firebase_notif_new_order_to_fincoy(self):
        search_lead_fincoy = self.env['tw.lead'].sudo().search([('is_fif','=',True),('is_fincoy_notif_new_order','=',False),('state','=','proposed')],limit=1)
        if search_lead_fincoy :
            for var in search_lead_fincoy :
                propose_date = str(datetime.strptime(var.propose_date, '%Y-%m-%d %H:%M:%S') + relativedelta(hours=7))
                template = self.env['tw.firebase.content.template'].search([('name','=','Finco New Order')],limit=1)
                if not template:
                    raise Warning("Template pesan 'Finco New Order' tidak ditemukan")
                pesan = template.content
                pesan = pesan.replace("%prospek_branch%",var.company_id.name)
                pesan = pesan.replace("%prospek_name%",var.customer_name)
                pesan = pesan.replace("%prospek_alamat%"," %s %s KEC. %s" %(var.street,var.city_id.name,var.district_id.name))
                pesan = pesan.replace("%prospek_product%",var.product_id.name)
                pesan = pesan.replace("%prospek_dp%",str(int(var.uang_muka) if var.uang_muka else 0))
                pesan = pesan.replace("%prospek_cicilan%",str(int(var.cicilan) if var.cicilan else 0))
                pesan = pesan.replace("%prospek_tenor%",str(int(var.tenor) if var.tenor else 0))
                pesan = pesan.replace("%prospek_tgl_pengajuan%",propose_date)
                messages = {
                        'employee_sender_id':1,
                        'name':'New Order Fincoy',
                        'transaction_id':var.id,
                        'model_name':'tw.lead',
                        'message':pesan,
                        }
                
                search_empoyee_finco="""
                        SELECT 
                            firebase_user.firebase_token
                            ,hr.id as employee_id
                        FROM hr_employee AS hr
                            LEFT JOIN resource_resource r ON r.id = hr.resource_id 
                            LEFT JOIN tw_firebase_user as firebase_user ON firebase_user.user_id=r.user_id
                        WHERE hr.partner_fincoy_id is NOT NULL
                        AND firebase_user.active = True
                    """
                self._cr.execute (search_empoyee_finco)
                ress =  self._cr.dictfetchall()
                firebase_message_line_ids = []
                if ress :
                    for res in ress:
                        firebase_message_line_ids.append([0,0,{
                            'employee_receiver_id':res['employee_id'],
                        }])
                    messages['firebase_message_line_ids']=firebase_message_line_ids
                    message_id = self.env['tw.firebase.message'].suspend_security().create(messages)
                    if message_id :
                        var.write({'is_fincoy_notif_new_order':True})
                        for line in message_id.firebase_message_line_ids :
                            obj_token=self.env['tw.firebase.user'].search([('user_id','=',line.employee_receiver_id.user_id.id),('active','=',True)])
                            if obj_token :
                                for token in obj_token :
                                    message_title = 'New Order a.n %s' % (var.customer_name)
                                    message_body  = 'Dealer %s'  % (var.company_id.name)
                                    data = {
                                    "priority" : "normal",
                                    "notification" : {
                                        "id" : line.id,
                                        "body" : "%s"%(message_body),
                                        "title" : "%s"%(message_title),
                                        "icon" : "logo_sahabat_tunas",
                                        "model" : "tw.firebase.message",
                                    },
                                    "data" : {
                                        "text" : " "
                                        }
                                    }

                                    send = self.env['tw.firebase.user'].notify_single_device(token.firebase_token,data)
                                    
                                    # FCM HTTP v1 API response handling
                                    if 'name' in send:
                                        # SUCCESS: Extract message ID from the 'name' field
                                        message_id_firebase = send['name']
                                        line.write({'message_id':message_id_firebase.split(":")[-1],'send_date':self._get_default_date(),'state':'unread'})
                                    
                        message_id.write({'state':'send'})


