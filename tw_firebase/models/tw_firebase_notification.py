#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import timedelta, datetime, date
import calendar
from dateutil.relativedelta import relativedelta
import logging

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
try:
    from pyfcm import FCMNotification
except:
    FCMNotification = None
from lxml.html import fromstring, tostring
from lxml.html import builder as E

_logger = logging.getLogger(__name__)

STATES = [('draft', 'Draft'),('send', 'Send'),('unread', 'Unread'), ('read', 'Read')]

class FirebaseNotification(models.Model):

    _name = "tw.firebase.notification"
    _description = "Firebase Notification"
    _order = "id desc"

    # 7: defaults methods
    
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()
    
    def _get_default_datetime(self):
        return self.env['res.company'].get_default_datetime()

    # 8: fields
    name = fields.Char( required=True, string="Name",  help="")
    customer_name = fields.Char(string="Customer Name",  help="")
    message = fields.Html(string='Message')    
    state = fields.Selection(selection=STATES, readonly=True, default=STATES[0][0],  string="State",  help="")
    overdue = fields.Integer( string="Overdue in",  readonly=True, help="")
    followup_date = fields.Datetime( string="Tgl followup",  readonly=True, help="")
    send_date = fields.Datetime( string="Tgl kirim",  readonly=True, help="")

    # 8: relation fields
    lead_activity_id = fields.Many2one(comodel_name="tw.lead.activity",  string="Lead activity", help="")
    company_id = fields.Many2one(comodel_name="res.company",  string="Branch",  readonly=True, help="")
    employee_receiver_id = fields.Many2one(comodel_name="hr.employee",  string="Employee receiver",  readonly=True, help="")
    category_id = fields.Many2one(comodel_name="tw.firebase.notification.category",  string="Category",  readonly=True, help="")

    # 9: constraints & sql constraints

    # 10: compute/depends & on change methods

    # 11: override methods
    # 
    # def name_get(self, context=None):
        # return super(FirebaseNotification, self).name_get(context)

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
        # return super(FirebaseNotification, self).name_search(name, args, operator, limit)

    # @api.model
    # def create(self, vals):
        # return super(FirebaseNotification, self).create(vals)

    # 
    # def write(self, vals):
        # return super(FirebaseNotification, self).write(vals)

    # 
    # def unlink(self):
        # for x in self:
            # if x.state != 'draft':
                # raise Warning('Perhatian!\nData tidak bisa dihapus.')
                # return super(FirebaseNotification, self).unlink()

    # 
    # def copy(self):
        # raise Warning('Perhatian!\nData tidak bisa diduplikasi.')
        # return super(FirebaseNotification, self).copy()


    # 12: action methods
    def action_confirm(self):
        self.state = STATES[1][0]
        self._send_notification_firebase()

    def action_done(self):
        self.state = STATES[2][0]

    def action_draft(self):
        self.state = STATES[0][0]


    # 13: private methods
    def schedule_notification_tomorrow_followup(self) :
        query = """
            SELECT
                hr.id as id_penerima
                , hr.name as nama_penerima
                , job.name as job_penerima
                , company.name as company_penerima
                , company.id as company_id
                , hr.id as sales_input_id
                , usr.id as user_sales_input_id
                , count(lead.id) as jumlah_followup
                , string_agg('(' || stage.name || ')', '<br/>') as followup_by
                , string_agg(lead.customer_name, '<br/>') as customers
                , string_agg(': <t/>' || to_char(activity.date+ INTERVAL '7 hours', 'YYYY-MM-DD HH24:MI'), '<br/>') as dates
                , (date(now()) + INTERVAL '1 days')::date as followup_date
            FROM tw_lead as lead
                LEFT JOIN tw_lead_activity as activity on activity.lead_id=lead.id
                LEFT JOIN hr_employee as hr on hr.id=lead.employee_id
                LEFT JOIN res_company as company on company.id=hr.company_id
                LEFT JOIN resource_resource as rs on rs.id=hr.resource_id
                LEFT JOIN res_users as usr ON usr.id=rs.user_id
                LEFT JOIN hr_job as job on job.id=hr.job_id
                LEFT JOIN tw_lead_stage stage ON activity.stage_id = stage.id
            WHERE 1=1
                AND activity.date is NOT NULL
                AND activity.stage_id is NULL 
                AND lead.state ='open'
                AND date(activity.date + INTERVAL '7 hours')::date = (date(now()) + INTERVAL '1 days')::date
            GROUP BY hr.id,job.id,usr.id,company.id
            """
        self._cr.execute(query)
        ress =  self._cr.dictfetchall()
        if ress :
            category = self.env['tw.firebase.notification.category'].suspend_security().search([('name','=','Reminder Followup Tomorrow')],limit=1)
            template = category.content_template_id
            if not template:
                raise Warning("Template pesan 'Reminder Followup Tomorrow' tidak ditemukan")                
            for res in ress:
                tgl_fu = res['followup_date']
                nama_penerima = res['nama_penerima']
                job_penerima = res['job_penerima']
                company_penerima = res['company_penerima']
                customers = res['customers']
                dates = res['dates']
                followup_by = res['followup_by']
                jumlah_followup = str(res['jumlah_followup'])
                pesan = template.content
                pesan = pesan.replace("%penerima%",nama_penerima)
                pesan = pesan.replace("%jumlah_followup%", jumlah_followup)
                pesan = pesan.replace("%customers%",customers)
                pesan = pesan.replace("%dates%",dates)
                pesan = pesan.replace("%tgl_followup%",tgl_fu)
                pesan = pesan.replace("%followup_by%",followup_by)
    
                message_data = {
                    'name' : template.name + "["+nama_penerima+"]",
                    'message' : pesan,
                    'company_id' : res['company_id'],
                    'employee_receiver_id': res['sales_input_id'],
                    'followup_date': res['followup_date'],
                    'category_id' : category.id,  
                }
                create_message_data= self.env['tw.firebase.notification'].sudo().create(message_data)
                if create_message_data :
                    message_title = "Followup di tgl %s" %(tgl_fu)
                    message_body  = "Terdapat %s Followup" % (jumlah_followup)
                    data = {
                        "priority" : "normal",
                        "notification" : {
                            "id" : create_message_data.id,
                            "body" : "%s"%(message_body),
                            "title" : "%s"%(message_title),
                            "icon" : "logo_sahabat_tunas",
                            "model" : "tw.firebase.notification",
                            "click_action": "com.matra.dwipa.tunas.hoking.firebase.page.DetailsNotifications"
                        },
                        "data" : {
                            "text" : "new Symulti update !"
                        }
                    }

                    obj_firebase_user = self.env['tw.firebase.user'].search([('user_id','=',create_message_data.employee_receiver_id.user_id.id),('active','=',True)])
                    if obj_firebase_user :
                        for token in obj_firebase_user :
                            send = obj_firebase_user.notify_single_device(token.firebase_token, data)
                            create_message_data.write({'send_date':self._get_default_date(),'state':'unread'})

    def schedule_notification_followup(self) : #Digenerate 1 jam sebelum janji followup
        query = """
            SELECT
                lead.id as lead_id
                , company.id as company_id
                , lead.customer_name as customer_name
                , hr.id as sales_input_id
                , hr.name as nama_sales
                , job.id as job_sales_input_id
                , usr.id as user_sales_input_id
                , job.name as nama_job_sales_input
                , activity.id as lead_activity_id
                , activity.date+ INTERVAL '7 hours' as followup_date
                , activity.stage_id as stage_fu
                , lead.street as alamat
                , stage.name as followup_by
                , lead.minat
                , lead.mobile
                , COALESCE(lead.note,'-') as note
                , COALESCE(CASE WHEN lead.payment_type = '1' THEN 'Cash' ELSE CASE WHEN lead.payment_type = '2' THEN 'Credit' ELSE '-' END END,'-') as payment_type
                , CASE WHEN product.id is not null THEN '[' || product.default_code || '] ' || tmpl.name ELSE '-' END as product_name 
            FROM tw_lead as lead
                LEFT JOIN tw_lead_activity as activity on activity.lead_id = lead.id
                LEFT JOIN res_company as company on company.id = lead.company_id
                LEFT JOIN hr_employee as hr on hr.id = lead.employee_id
                LEFT JOIN resource_resource as rs on rs.id=hr.resource_id
                LEFT JOIN res_users as usr ON usr.id = rs.user_id
                LEFT JOIN hr_job as job on job.id = hr.job_id
                LEFT JOIN tw_lead_stage stage ON activity.stage_id = stage.id
                LEFT JOIN product_product as product on product.id = lead.product_id
                LEFT JOIN product_template as tmpl on tmpl.id = product.product_tmpl_id 
            WHERE 1=1
                AND activity.date is NOT NULL
                AND activity.stage_id is NULL 
                AND lead.state ='open'
                AND date(activity.date + INTERVAL '7 hours')=date(now())
                AND extract(hour from (activity.date + INTERVAL '7 hours')) = extract(hour from (now() + INTERVAL '1 hours'))
            """
        self._cr.execute(query)
        ress =  self._cr.dictfetchall()
        if ress :
            category = self.env['tw.firebase.notification.category'].suspend_security().search([('name','=','Reminder Followup an Hour Before')],limit=1)
            template = category.content_template_id
            if not template:
                raise Warning("Template pesan 'Reminder Followup an Hour Before' tidak ditemukan")                
            for res in ress:
                obj_empl=self.env['hr.employee'].search([('id','=',res['sales_input_id'])])
                if obj_empl :
                    dtgl_fu = datetime.strptime( res['followup_date'], '%Y-%m-%d %H:%M:%S')
                    tgl_fu = date.strftime(dtgl_fu, "%d %b %Y %I:%M:%S %p")
                    name = res['customer_name']
                    mobile = res['mobile']
                    minat = res['minat']
                    followup_by = res['followup_by']
                    name = res['customer_name']
                    product_name = res['product_name']
                    payment_type = res['payment_type']
                    prospek_note = res['note']
                    pesan = template.content
                    pesan = pesan.replace("%penerima%",obj_empl.name)
                    pesan = pesan.replace("%jabatan%",obj_empl.job_id.name)
                    pesan = pesan.replace("%dealer%",obj_empl.company_id.name)
                    pesan = pesan.replace("%prospek_name%",name)
                    pesan = pesan.replace("%prospek_no_hp%",mobile)
                    pesan = pesan.replace("%prospek_minat%",minat)
                    pesan = pesan.replace("%prospek_followup_by%",followup_by)
                    pesan = pesan.replace("%tgl_followup%",tgl_fu)
                    pesan = pesan.replace("%prospek_product%",product_name)
                    pesan = pesan.replace("%prospek_payment_type%",payment_type)
                    pesan = pesan.replace("%prospek_note%",prospek_note)
        
                    message_data = {
                        'name' : template.name + "["+obj_empl.name+"]",
                        'message' : pesan,
                        'customer_name' : name,
                        'company_id' : res['company_id'],
                        'lead_id' : res['lead_id'],
                        'followup_date': res['followup_date'],
                        'lead_activity_id':res['lead_activity_id'],
                        'employee_receiver_id': res['sales_input_id'],
                        'category_id' : category.id,  
                    }
                    create_message_data= self.env['tw.firebase.notification'].sudo().create(message_data)
                    if create_message_data :
                        message_title = "Follow-up "+create_message_data.lead_activity_id.lead_id.customer_name
                        message_body  = "Tgl %s By %s " % (tgl_fu,res['followup_by'])
                        data = {
                            "priority" : "normal",
                            "notification" : {
                                "id" : create_message_data.id,
                                "body" : "%s"%(message_body),
                                "title" : "%s"%(message_title),
                                "icon" : "logo_sahabat_tunas",
                                "model" : "tw.firebase.notification",
                                "click_action": "com.matra.dwipa.tunas.hoking.firebase.page.DetailsNotifications"
                            },
                            "data" : {
                                "text" : "new Symulti update !"
                            }
                        }

                        obj_firebase_user = self.env['tw.firebase.user'].search([('user_id','=',create_message_data.employee_receiver_id.user_id.id),('active','=',True)])
                        if obj_firebase_user :
                            for token in obj_firebase_user :
                                send = obj_firebase_user.notify_single_device(token.firebase_token, data)
                                create_message_data.write({'send_date':self._get_default_date(),'state':'unread'})

    def schedule_notification_overdue(self) :
        query = """
            SELECT
                lead.id as lead_id
                , company.id as company_id
                , lead.customer_name as customer_name
                , hr.id as sales_input_id
                , hr.name as nama_sales
                , job.id as job_sales_input_id
                , usr.id as user_sales_input_id
                , job.name as nama_job_sales_input
                , activity.id as lead_activity_id
                , activity.date+ INTERVAL '7 hours' as followup_date
                , extract(hour from (activity.date + INTERVAL '9 hours'))::int overdue_date
                , activity.stage_id as stage_fu
                , DATE_PART('hour', now() - (activity.date + INTERVAL '7 hours')) as overdue
                , lead.mobile
                , lead.minat
                , stage.name as followup_by
                , COALESCE(lead.note,'-') as note
                , COALESCE(CASE WHEN lead.payment_type = '1' THEN 'Cash' ELSE CASE WHEN lead.payment_type = '2' THEN 'Credit' ELSE '-' END END,'-') as payment_type
                , CASE WHEN product.id is not null THEN '[' || product.default_code || '] ' || tmpl.name ELSE '-' END as product_name 
            FROM  tw_lead as lead
                LEFT JOIN tw_lead_activity as activity on activity.lead_id = lead.id
                LEFT JOIN res_company as company on company.id = lead.company_id
                LEFT JOIN hr_employee as hr on hr.id = lead.employee_id
                LEFT JOIN resource_resource as rs on rs.id = hr.resource_id
                LEFT JOIN res_users as usr ON usr.id = rs.user_id
                LEFT JOIN hr_job as job on job.id = hr.job_id
                LEFT JOIN tw_lead_stage stage ON activity.stage_id = stage.id
                LEFT JOIN product_product as product on product.id = lead.product_id
                LEFT JOIN product_template as tmpl on tmpl.id = product.product_tmpl_id 
            WHERE 1=1
                AND activity.date is NOT NULL
                AND activity.stage_id is NULL 
                AND lead.state ='open'
                AND date(activity.date + INTERVAL '7 hours')=date(now())
                AND extract(hour from (activity.date + INTERVAL '7 hours')) = extract(hour from (now() - INTERVAL '1 hours'))
        """
        self._cr.execute(query)
        ress =  self._cr.dictfetchall()
        if ress :
            category = self.env['tw.firebase.notification.category'].suspend_security().search([('name','=','Reminder Followup Overdue')],limit=1)
            template = category.content_template_id
            if not template:
                raise Warning("Template pesan 'Reminder Followup Overdue' tidak ditemukan")                
            for res in ress:
                obj_empl=self.env['hr.employee'].search([('id','=',res['sales_input_id'])])
                if obj_empl :
                    dtgl_fu = datetime.strptime( res['followup_date'], '%Y-%m-%d %H:%M:%S')
                    tgl_fu = date.strftime(dtgl_fu, "%d %b %Y %I:%M:%S %p")
                    name = res['customer_name']
                    mobile = res['mobile']
                    minat = res['minat']
                    followup_by = res['followup_by']
                    product_name = res['product_name']
                    payment_type = res['payment_type']
                    prospek_note = res['note']
                    overdue = str(res['overdue_date']) + ':00'
                    pesan = template.content
                    pesan = pesan.replace("%penerima%",obj_empl.name)
                    pesan = pesan.replace("%jabatan%",obj_empl.job_id.name)
                    pesan = pesan.replace("%dealer%",obj_empl.company_id.name)
                    pesan = pesan.replace("%prospek_name%",name)
                    pesan = pesan.replace("%prospek_no_hp%",mobile)
                    pesan = pesan.replace("%prospek_minat%",minat)
                    pesan = pesan.replace("%prospek_followup_by%",followup_by)
                    pesan = pesan.replace("%prospek_followup_date%",tgl_fu)
                    pesan = pesan.replace("%deadline%",overdue)
                    pesan = pesan.replace("%prospek_product%",product_name)
                    pesan = pesan.replace("%prospek_payment_type%",payment_type)
                    pesan = pesan.replace("%prospek_note%",prospek_note)
        
                    message_data = {
                        'name' : template.name + "["+obj_empl.name+"]",
                        'message' : pesan,
                        'customer_name' : name,
                        'company_id' : res['company_id'],
                        'lead_id' : res['lead_id'],
                        'followup_date': res['followup_date'],
                        'lead_activity_id':res['lead_activity_id'],
                        'employee_receiver_id': res['sales_input_id'],
                        'category_id' : category.id,  
                    }
                    create_message_data= self.env['tw.firebase.notification'].sudo().create(message_data)
                    if create_message_data :
                        message_title = "Overdue Follow-up "+create_message_data.lead_activity_id.lead_id.customer_name
                        message_body  = "Tgl %s By %s " % (tgl_fu,res['followup_by'])
                        data = {
                            "priority" : "normal",
                            "notification" : {
                                "id" : create_message_data.id,
                                "body" : "%s"%(message_body),
                                "title" : "%s"%(message_title),
                                "icon" : "logo_sahabat_tunas",
                                "model" : "tw.firebase.notification",
                                "click_action": "com.matra.dwipa.tunas.hoking.firebase.page.DetailsNotifications"
                            },
                            "data" : {
                                "text" : "new Symulti update !"
                            }
                        }

                        obj_firebase_user = self.env['tw.firebase.user'].search([('user_id','=',create_message_data.employee_receiver_id.user_id.id),('active','=',True)])
                        if obj_firebase_user :
                            for token in obj_firebase_user :
                                send = obj_firebase_user.notify_single_device(token.firebase_token, data)
                                create_message_data.write({'send_date':self._get_default_date(),'state':'unread'})

    def schedule_notification_overdue_renjang(self):
        # 1 jam sekali sampai jam 8 malam, selanjutnya akan dikirim besok pagi.
        # Kacab
        category = self.env['tw.firebase.notification.category'].suspend_security().search([('active','=',True),('jenis_reminder','=','overdue'),('job_id','=',self.env.ref('tw_employee.job_sale_operation_head').id)],order='id desc',limit=1)
        if category and category.content_template_id:
            self.notification_overdue_renjang('every_hour','kacab_id',category)
        # Kawil
        category = self.env['tw.firebase.notification.category'].suspend_security().search([('active','=',True),('jenis_reminder','=','overdue'),('job_id','=',self.env.ref('tw_employee.job_manager_area').id)],order='id desc',limit=1)
        if category and category.content_template_id:
            self.notification_overdue_renjang('every_hour','kawil_id',category)
        # Owner
        category = self.env['tw.firebase.notification.category'].suspend_security().search([('active','=',True),('jenis_reminder','=','overdue'),('job_id','=',self.env.ref('tw_employee.job_owner').id)],order='id desc',limit=1)
        if category and category.content_template_id:
            self.notification_overdue_renjang('every_hour','owner_id',category)
    
    def schedule_notification_overdue_renjang_daily(self):
        # pengiriman di pagi hari, followup diatas jam 7 malam yg overdue.
        # Kacab
        category = self.env['tw.firebase.notification.category'].suspend_security().search([('active','=',True),('jenis_reminder','=','overdue'),('job_id','=',self.env.ref('tw_employee.job_sale_operation_head').id)],order='id desc',limit=1)
        if category and category.content_template_id:
            self.notification_overdue_renjang('daily','kacab_id',category)
        # Kawil
        category = self.env['tw.firebase.notification.category'].suspend_security().search([('active','=',True),('jenis_reminder','=','overdue'),('job_id','=',self.env.ref('tw_employee.job_manager_area').id)],order='id desc',limit=1)
        if category and category.content_template_id:
            self.notification_overdue_renjang('daily','kawil_id',category)
        # Owner
        category = self.env['tw.firebase.notification.category'].suspend_security().search([('active','=',True),('jenis_reminder','=','overdue'),('job_id','=',self.env.ref('tw_employee.job_owner').id)],order='id desc',limit=1)
        if category and category.content_template_id:
            self.notification_overdue_renjang('daily','owner_id',category)

    def notification_overdue_renjang(self,where_type,job,category):
        today = date.today()
        if where_type == 'every_hour':
            WHERE = """
                AND (EXTRACT(EPOCH from (now() - (activity.date + INTERVAL '7 hours')))::INT/3600) = %(max_jam)s
                AND extract(hour from (activity.date + INTERVAL '7 hours' + INTERVAL '%(max_jam)s hours')) <= 20 --Maksimal reminder jam 8 malam
                AND extract(hour from (activity.date + INTERVAL '7 hours' + INTERVAL '%(max_jam)s hours')) >= 7 --Min jam 7 Pagi karena jam 7 kebawah akan di reminder di reminder daily
            """ % {'max_jam' : category.max_jam}
        elif where_type == 'daily':
            WHERE = """
                AND (EXTRACT(EPOCH from (now() - (activity.date + INTERVAL '7 hours')))::INT/3600) > %(max_jam)s
                AND activity.date + INTERVAL '7 hours' + INTERVAL '%(max_jam)s hours' >= CONCAT(date(now() - INTERVAL '1 days'), ' ','21:00:00')::TIMESTAMP --Jam 8 masuk di reminder per-jam, daily dari jam 9
                AND activity.date + INTERVAL '7 hours' + INTERVAL '%(max_jam)s hours' < CONCAT(date(now()), ' ','07:00:00')::TIMESTAMP --lewat dari jam 7 masuk di daily
            """ % {'max_jam' : category.max_jam}
        
        else:
            raise Warning("Tipe tidak ada")
        query = """
                SELECT
                lead.id as lead_id
                , company.id as company_id
                , lead.customer_name as customer_name
                , hr.id as sales_input_id
                , hr.name as nama_sales
                , renjang.id as renjang_id
                , renjang.name as renjang_name
                , job.id as job_sales_input_id
                , usr.id as user_sales_input_id
                , job.name as nama_job_sales_input
                , activity.id as lead_activity_id
                , activity.date+ INTERVAL '7 hours' as followup_date
                , extract(hour from (activity.date + INTERVAL '9 hours'))::int overdue_date
                , activity.stage_id as stage_fu
                , DATE_PART('hour', now() - (activity.date + INTERVAL '7 hours')) as overdue
                , lead.mobile
                , lead.minat
                , stage.name as followup_by
                , COALESCE(lead.note,'-') as note
                , COALESCE(CASE WHEN lead.payment_type = '1' THEN 'Cash' ELSE CASE WHEN lead.payment_type = '2' THEN 'Credit' ELSE '-' END END,'-') as payment_type
                , CASE WHEN product.id is not null THEN '[' || product.default_code || '] ' || tmpl.name ELSE '-' END as product_name 
            FROM  tw_lead as lead
                LEFT JOIN tw_lead_activity as activity on activity.lead_id=lead.id
                LEFT JOIN res_company as company on company.id = lead.company_id
                LEFT JOIN hr_employee as hr on hr.id = lead.employee_id
                LEFT JOIN resource_resource as rs on rs.id = hr.resource_id
                LEFT JOIN res_users as usr ON usr.id = rs.user_id
                LEFT JOIN hr_job as job on job.id = hr.job_id
                LEFT JOIN tw_lead_stage stage ON activity.stage_id = stage.id
                LEFT JOIN product_product as product on product.id = lead.product_id
                LEFT JOIN product_template as tmpl on tmpl.id = product.product_tmpl_id 
                JOIN hr_employee as renjang on renjang.id = company.%s

            WHERE 1=1
                AND activity.date is NOT NULL
                AND activity.stage_id is NULL 
                AND lead.state ='open'
                %s
        """ % (job,WHERE)
        self._cr.execute(query)
        ress =  self._cr.dictfetchall()
        if ress :
            for res in ress:
                template = category.content_template_id
                obj_empl = self.env['hr.employee'].search([('id','=',res['renjang_id'])])            
                if obj_empl:
                    dtgl_fu = datetime.strptime( res['followup_date'], '%Y-%m-%d %H:%M:%S')
                    tgl_fu = date.strftime(dtgl_fu, "%d %b %Y %I:%M:%S %p")
                    mobile = res['mobile']
                    minat = res['minat']
                    followup_date = res['followup_date']
                    followup_by = res['followup_by']
                    product_name = res['product_name']
                    payment_type = res['payment_type']
                    prospek_note = res['note']
                    name = res['customer_name']
                    company_id = res['company_id']
                    lead_id = res['lead_id']
                    lead_activity_id = res['lead_activity_id']
                    nama_sales = res['nama_sales']
                    renjang_id = res['renjang_id']
                    overdue = str(res['overdue_date']) + ':00'
                    pesan = template.content
                    pesan = pesan.replace("%penerima%",obj_empl.name)
                    pesan = pesan.replace("%salesman_name%",nama_sales)
                    pesan = pesan.replace("%jabatan%",obj_empl.job_id.name)
                    pesan = pesan.replace("%dealer%",obj_empl.company_id.name)
                    pesan = pesan.replace("%prospek_name%",name)
                    pesan = pesan.replace("%prospek_no_hp%",mobile)
                    pesan = pesan.replace("%prospek_minat%",minat)
                    pesan = pesan.replace("%prospek_followup_by%",followup_by)
                    pesan = pesan.replace("%prospek_followup_date%",tgl_fu)
                    pesan = pesan.replace("%prospek_product%",product_name)
                    pesan = pesan.replace("%deadline%",overdue)
                    pesan = pesan.replace("%prospek_payment_type%",payment_type)
                    pesan = pesan.replace("%prospek_note%",prospek_note)
        
                    message_data = {
                        'name' : template.name + "["+obj_empl.name+"]",
                        'message' : pesan,
                        'customer_name' : name,
                        'company_id' : company_id,
                        'lead_id' : lead_id,
                        'followup_date': followup_date,
                        'lead_activity_id':lead_activity_id,
                        'employee_receiver_id': renjang_id,
                        'category_id' : category.id,  
                    }
                    create_message_data= self.env['tw.firebase.notification'].sudo().create(message_data)
                    if create_message_data :
                        message_title = "Overdue Follow-up "+create_message_data.lead_activity_id.lead_id.customer_name
                        message_body  = "Tgl %s By %s " % (tgl_fu,followup_by)
                        data = {
                            "priority" : "normal",
                            "notification" : {
                                "id" : create_message_data.id,
                                "body" : "%s"%(message_body),
                                "title" : "%s"%(message_title),
                                "icon" : "logo_sahabat_tunas",
                                "model" : "tw.firebase.notification",
                                "click_action": "com.matra.dwipa.tunas.hoking.firebase.page.DetailsNotifications"
                            },
                            "data" : {
                                "text" : "new Symulti update !"
                            }
                        }

                        obj_firebase_user = self.env['tw.firebase.user'].search([('user_id','=',create_message_data.employee_receiver_id.user_id.id),('active','=',True)])
                        if obj_firebase_user :
                            for token in obj_firebase_user :
                                send = obj_firebase_user.notify_single_device(token.firebase_token, data)
                                create_message_data.write({'send_date':self._get_default_date(),'state':'unread'})
    
    # TODO: still need to check if there a need for adjustment
    def schedule_notification_approval_pbt(self):
        today = date.today()
        if today.day == 4:
            first_day = today.replace(day=1)
            last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
            category = self.env.ref('tw_firebase.firebase_notification_approval_pbt_to_am_and_gm')
            template = category.content_template_id
            if not template:
                raise Warning("Template pesan 'Notification Approval PBT' tidak ditemukan")

            sisa_margin = self.env['tw.profit.before.tax'].sudo().search([
                ('state','=', 'draft'),
                ('start_date','=',first_day),
                ('end_date','=',last_day)])
            if sisa_margin:
                line_state = [x.state for x in sisa_margin.input_sisa_margin_line_ids if x.state == 'draft']
                if not len(line_state):
                    obj_job = self.env['hr.job'].search([('name','ilike','Operation After Sales General Manager')])
                    obj_empl = self.env['hr.employee'].search([('job_id','=',obj_job.id)])
                if len(line_state):
                    obj_empl = self.env['hr.employee'].search([('id','=',sisa_margin.area_manager_id.id)])
                    
                if obj_empl :
                    pesan = template.content
                    pesan = pesan.replace("%name%",obj_empl.name)
                    pesan = pesan.replace("%branch%",obj_empl.company_id.name)
                    message_data = {
                        'name' : template.name + "["+obj_empl.name+"]",
                        'customer_name' : obj_empl.name,
                        'message' : pesan,
                        'company_id' : obj_empl.company_id.id,
                        'lot_id' : sisa_margin.lot_id,
                        'followup_date':today,
                        'employee_receiver_id': obj_empl.id,
                        'category_id' : category.id,  
                    }
                    create_message_data= self.env['tw.firebase.notification'].sudo().create(message_data)
                    if create_message_data :
                        message_title = "Approval PBT "+obj_empl.name
                        message_body  = "Tgl %s" % (today)
                        data = {
                            "priority" : "normal",
                            "notification" : {
                                "id" : create_message_data.id,
                                "body" : "%s"%(message_body),
                                "title" : "%s"%(message_title),
                                "icon" : "logo_sahabat_tunas",
                                "model" : "tw.firebase.notification",
                                "click_action": "com.matra.dwipa.tunas.hoking.firebase.page.DetailsNotifications"
                            },
                            "data" : {
                                "text" : "new Symulti update !"
                            }
                        }
                        obj_firebase_user = self.env['tw.firebase.user'].search([
                            ('user_id','=',create_message_data.employee_receiver_id.user_id.id),
                            ('active','=',True)])
                        if obj_firebase_user :
                            for token in obj_firebase_user :
                                send = obj_firebase_user.notify_single_device(token.firebase_token, data)
                                create_message_data.write({'send_date':self._get_default_date(),'state':'unread'})

    # TODO: still need to check if there a need for adjustment
    def schedule_notification_reminder_input_pbt(self):
        today = date.today()
        if today.day == 27:
            first_day = today.replace(day=1)
            last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])
            category = self.env.ref('tw_firebase.firebase_notification_reminder_input_pbt_to_soh')
            template = category.content_template_id
            if not template:
                raise Warning("Template pesan 'Notification Approval PBT' tidak ditemukan")
            registered_branches = self.env['tw.profit.before.tax'].sudo().search([
                ('start_date','=',first_day),
                ('end_date','=',last_day)]).mapped('company_id')
            unregistered_branches = self.env['res.company'].search([('id', 'not in', registered_branches.ids)])
            if unregistered_branches:
                for branch in unregistered_branches:
                    obj_empl = self.env['hr.employee'].search([
                        ('company_id','=',branch.id),
                        ('job_id.name','=','Branch Head')
                    ], limit=1)
                    if obj_empl :
                        pesan = template.content
                        pesan = pesan.replace("%name%",obj_empl.name)
                        message_data = {
                            'name' : template.name + "["+obj_empl.name+"]",
                            'customer_name' : obj_empl.name,
                            'message' : pesan,
                            'company_id' : obj_empl.company_id.id,
                            'followup_date':today,
                            'employee_receiver_id': obj_empl.id,
                            'category_id' : category.id,  
                        }
                        create_message_data= self.env['tw.firebase.notification'].sudo().create(message_data)
                        if create_message_data :
                            message_title = "Reminder Input PBT "+obj_empl.name
                            message_body  = "Tgl %s" % (today)
                            data = {
                                "priority" : "normal",
                                "notification" : {
                                    "id" : create_message_data.id,
                                    "body" : "%s"%(message_body),
                                    "title" : "%s"%(message_title),
                                    "icon" : "logo_sahabat_tunas",
                                    "model" : "tw.firebase.notification",
                                    "click_action": "com.matra.dwipa.tunas.hoking.firebase.page.DetailsNotifications"
                                },
                                "data" : {
                                    "text" : "new Symulti update !"
                                }
                            }
                            obj_firebase_user = self.env['tw.firebase.user'].search([
                                ('user_id','=',create_message_data.employee_receiver_id.user_id.id),
                                ('active','=',True)])
                            if obj_firebase_user :
                                for token in obj_firebase_user :
                                    send = obj_firebase_user.notify_single_device(token.firebase_token, data)
                                    create_message_data.write({'send_date':self._get_default_date(),'state':'unread'})

    def schedule_notification_followup_stnk_bpkb(self, doc_type):
        """Base method for scheduling followup notifications STNK and BPKB.
        
        Args:
            doc_type (str): Either 'stnk' or 'bpkb' to determine which document type to process
            
        Returns:
            bool: True if notifications were sent successfully, False otherwise
        """
        self.ensure_one()
        
        # Validate document type
        if doc_type not in ('stnk', 'bpkb'):
            _logger.error("Invalid document type: %s", doc_type)
            return False
            
        # Map document types to their respective fields and names
        doc_config = {
            'stnk': {
                'category_name': 'Reminder Followup STNK',
                'title_prefix': 'STNK',
                'query_select': 'lot.vehicle_registration_receipt_date as receipt_date',
                'query_where': ' AND lot.vehicle_registration_receipt_date = %s',
                'date_placeholder': 'tgl_stnk'
            },
            'bpkb': {
                'category_name': 'Reminder Followup BPKB',
                'title_prefix': 'BPKB',
                'query_select': 'lot.vehicle_ownership_receipt_date as receipt_date',
                'query_where': ' AND lot.vehicle_ownership_receipt_date = %s',
                'date_placeholder': 'tgl_bpkb'
            }
        }
        
        config = doc_config[doc_type]
        yesterday = (date.today() - relativedelta(days=1)).strftime("%Y-%m-%d")
        
        try:
            # Use parameterized query to prevent SQL injection
            query = """
                SELECT
                    cdb.company_id, 
                    lot.id as lot_id,
                    lot.name as no_engine,
                    {query_select}
                    cdb.name as customer_name,
                    cdb.identification_number as no_ktp,
                    cdb.employee_id as employee_receiver_id,
                    cdb.mobile as mobile
                FROM tw_partner_cdb cdb
                JOIN stock_lot lot ON cdb.id = lot.cdb_partner_id
                WHERE lot.dealer_sale_order_id IS NOT NULL
                    AND lot.document_state NOT IN ('document_request')
                    AND lot.cddb_state = 'cddb'
                    {query_where}
                ORDER BY cdb.company_id
            """.format(query_select=config['query_select'], query_where=config['query_where'])
            
            self._cr.execute(query, (yesterday,))
            results = self._cr.dictfetchall()
            
            if not results:
                return True  # No records to process
                
            # Get the notification category
            category = self.env['tw.firebase.notification.category'].search([
                ('name', '=', config['category_name']),
                ('sumber_data', '=', 'proactive'),
                ('jenis_reminder', '=', 'reminder')
            ], limit=1)
            
            if not category or not category.content_template_id:
                _logger.error("Notification category or template not found for %s", doc_type)
                return False
                
            # Process each record
            for record in results:
                self._process_notification_record(record, category, config)
                
            return True
            
        except Exception as e:
            _logger.error("Error in _schedule_notification_followup (%s): %s", doc_type, str(e), exc_info=True)
            return False
        
    def _process_notification_record(self, record, category, config):
        """Process a single notification record.
        
        Args:
            record (dict): The record data from the database
            category: The notification category record
            config (dict): Configuration for the document type
        """
        # TODO: active again if need to check notification exisiting
        # # Check if notification already exists
        # existing = self.env['tw.firebase.notification'].search([
        #     ('lot_id', '=', record['lot_id']),
        #     ('category_id', '=', category.id)
        # ])
        
        # if existing:
        #     return  # Skip if notification already exists
            
        employee = self.env['hr.employee'].browse(record['employee_receiver_id'])
        if not employee:
            return  # Skip if no employee found
            
        # Format dates
        receipt_date = datetime.strptime(record['receipt_date'], '%Y-%m-%d')
        formatted_date = date.strftime(receipt_date, "%d %b %Y")
        
        # Prepare message with template
        message = category.content_template_id.content
        replacements = {
            "%penerima%": employee.name,
            "%jabatan%": employee.job_id.name or '',
            "%dealer%": employee.company_id.name,
            "%faktur_name%": record['customer_name'],
            "%faktur_no_engine%": record['no_engine'],
            "%faktur_no_ktp%": record['no_ktp'] or '',
            "%faktur_no_hp%": record['mobile'] or '',
            config['date_placeholder']: formatted_date
        }
        
        for placeholder, value in replacements.items():
            message = message.replace(placeholder, str(value))
            
        # Create notification record
        notification = self.env['tw.firebase.notification'].sudo().create({
            'name': f"{category.name} [{employee.name}]",
            'customer_name': record['customer_name'],
            'message': message,
            'company_id': record['company_id'],
            'lot_id': record['lot_id'],
            'followup_date': record['receipt_date'],
            'employee_receiver_id': record['employee_receiver_id'],
            'category_id': category.id,
        })
        
        if not notification:
            return
            
        # Prepare notification data for Firebase
        message_title = f"{config['title_prefix']} {record['customer_name']}"
        message_body = f"Tgl {formatted_date}"
        
        data = {
            "priority": "normal",
            "notification": {
                "id": notification.id,
                "body": message_body,
                "title": message_title,
                "icon": "logo_sahabat_tunas",
                "model": "tw.firebase.notification",
                "click_action": "com.matra.dwipa.tunas.hoking.firebase.page.DetailsNotifications"
            },
            "data": {"text": "new Symulti update !"}
        }
        
        # Send notification to Firebase
        firebase_user = self.env['tw.firebase.user'].search([
            ('user_id', '=', employee.user_id.id),
            ('active', '=', True)
        ])
        
        if firebase_user:
            for token in firebase_user:
                try:
                    firebase_user.notify_single_device(token.firebase_token, data)
                    notification.write({
                        'send_date': self._get_default_date(),
                        'state': 'unread'
                    })
                except Exception as e:
                    _logger.error("Error sending Firebase notification: %s", str(e))

    def _send_notification_firebase(self, message_title="",message_body=""):
        if not self.employee_receiver_id:
            raise Warning("Employee receiver is required to send notification.")

        title = message_title or self.name
        body = message_body or self.message
        data = {
            "priority" : "normal",
            "notification" : {
                "id" : self.id,
                "body" : "%s"%(body),
                "title" : "%s"%(title),
                "icon" : "logo_sahabat_tunas",
                "model" : "tw.firebase.notification",
                "click_action": "com.matra.dwipa.tunas.hoking.firebase.page.DetailsNotifications"
            },
            "data" : {
                "text" : "new Symulti update !"
            }
        }
        obj_firebase_user = self.env['tw.firebase.user'].search([
            ('user_id', '=', self.employee_receiver_id.user_id.id),
            ('active', '=', True)])
        if obj_firebase_user :
            for token in obj_firebase_user :
                send = obj_firebase_user.notify_single_device(token.firebase_token, data)
                self.write({'send_date': self._get_default_date(), 'state': 'unread'})

