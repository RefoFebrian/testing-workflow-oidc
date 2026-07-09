# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
import logging
_logger = logging.getLogger(__name__)

class TwFirebaseNotificationInherit(models.Model):
    _inherit = "tw.firebase.notification"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def schedule_notification_followup_crm_daily(self):
        ress = self._get_followup_crm_daily_data()
        if ress:
            category = self.env['tw.firebase.notification.category'].suspend_security().search([
                ('name','=','Reminder Followup Harian')
            ], limit=1)
            template = category.content_template_id
            if not template:
                raise Warning("Template pesan 'Daily Followup Reminder' tidak ditemukan")                
            
            for res in ress:
                obj_empl = self.env['hr.employee'].search([('id','=',res.get('sales_input_id'))])
                if obj_empl:
                    dtgl_fu = res.get('followup_date')
                    tgl_fu = date.strftime(dtgl_fu, "%d %b %Y %I:%M:%S %p")
                    name = res.get('customer_name')
                    mobile = res.get('mobile')
                    minat = res.get('minat')
                    followup_by = res.get('followup_by')
                    name = res.get('customer_name')
                    product_name = res.get('product_name')
                    pesan = template.content
                    
                    pesan = pesan.replace('%penerima%', obj_empl.name)
                    pesan = pesan.replace('%jabatan%', obj_empl.job_id.name)
                    pesan = pesan.replace('%prospek_followup_by%', followup_by)
                    pesan = pesan.replace('%dealer%', obj_empl.branch_id.name)
                    pesan = pesan.replace('%prospek_name%', name)
                    pesan = pesan.replace('%prospek_no_hp%', mobile)
                    pesan = pesan.replace('%prospek_minat%', minat)
                    pesan = pesan.replace('%tgl_followup%', tgl_fu)
                    pesan = pesan.replace('%prospek_product%', product_name)
        
                    message_data = {
                        'name': template.name + '[' + obj_empl.name + ']',
                        'message': pesan,
                        'customer_name': name,
                        'company_id': res['branch_id'],
                        'followup_date': res['followup_date'],
                        'employee_receiver_id': res['sales_input_id'],
                        'category_id': category.id
                    }
                    create_message_data = self.env['tw.firebase.notification'].sudo().create(message_data)
                    
                    if create_message_data:
                        message_title = 'Follow-up ' + name
                        message_body  = 'Tgl %s By %s ' % (tgl_fu, followup_by)
                        data = {
                            'priority': 'normal',
                            'notification': {
                                'id': create_message_data.id,
                                'body': '%s' % (message_body),
                                'title': '%s' % (message_title),
                                'icon': 'logo_sahabat_tunas',
                                'model': 'tw.firebase.notification',
                                'click_action': 'com.matra.dwipa.tunas.hoking.firebase.page.DetailsNotifications'
                            },
                            'data': {
                                'text': 'new Symulti update !'
                            }
                        }

                        obj_firebase_user_obj = self.env['tw.firebase.user'].search([
                            ('user_id','=',create_message_data.employee_receiver_id.user_id.id),
                            ('active','=',True)
                        ])
                        if obj_firebase_user_obj:
                            for token in obj_firebase_user_obj:
                                try:
                                    send = obj_firebase_user_obj.notify_single_device(token.firebase_token, data)
                                    create_message_data.write({
                                        'send_date': self._get_default_date(),
                                        'state': 'unread'
                                    })
                                except Exception as e:
                                    _logger.error(e)

    # 14: private methods
    def _get_followup_crm_daily_data(self):
        query = """
            SELECT
                lead.id AS lead_id
                , branch.id AS branch_id
                , lead.customer_name AS customer_name
                , hr.id AS sales_input_id
                , hr.name AS nama_sales
                , job.id AS job_sales_input_id
                , usr.id AS user_sales_input_id
                , job.name AS nama_job_sales_input
                , activity.id AS lead_activity_id
                , activity.date+ INTERVAL '7 hours' AS followup_date
                , activity.stage_id AS stage_fu
                , lead.alamat AS alamat
                , stage.name AS followup_by
                , minat.name AS minat
                , COALESCE(lead.mobile, lead.whatsapp) AS mobile
                , CASE WHEN product.id IS NOT NULL THEN '[' || product.default_code || '] ' || tmpl.name::JSONB ->> 'en_US' ELSE '-' END AS product_name
            FROM tw_lead lead
            LEFT JOIN tw_selection minat ON lead.interest_id = minat.id AND minat.type = 'Interest'
            LEFT JOIN tw_selection data_source ON lead.data_source_id = data_source.id AND data_source.type = 'DataSource'
            LEFT JOIN tw_lead_activity activity ON activity.lead_id = lead.id
            LEFT JOIN res_company branch ON lead.company_id = branch.id
            LEFT JOIN hr_employee hr ON lead.employee_id = hr.id
            LEFT JOIN resource_resource rs ON rs.id = hr.resource_id
            LEFT JOIN res_users usr ON usr.id = rs.user_id
            LEFT JOIN hr_job job ON job.id = hr.job_id
            LEFT JOIN crm_stage stage ON activity.stage_id = stage.id
            LEFT JOIN product_product product ON product.id = lead.product_id
            LEFT JOIN product_template tmpl ON tmpl.id = product.product_tmpl_id
            WHERE 1=1
            AND activity.date IS NOT NULL
            AND activity.activity_result_id IS NULL 
            AND lead.state = 'open'
            AND data_source.value = 's3_aws'
            AND DATE(activity.date + INTERVAL '7 hours')::DATE = DATE(NOW())
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()

        return ress