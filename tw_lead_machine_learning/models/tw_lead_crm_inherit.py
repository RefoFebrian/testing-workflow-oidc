# 1: imports of python lib
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib
import boto3
import holidays
import csv

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
import logging
_logger = logging.getLogger(__name__)

class TwLeadCrmInherit(models.Model):
    _inherit = "tw.lead.crm"

    # 7: defaults methods
    def _get_default_datetime(self):
        return datetime.now()
    
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def get_crm_s3(self, limit=1):
        title = 'Get Data CRM S3'
        log_obj = self.env['tw.api.log']
        config_obj = self.env['tw.api.configuration']._get_config_aws()

        # Create a session using the provided credentials
        session = boto3.Session(
            aws_access_key_id=config_obj.get('aws_access_key'),
            aws_secret_access_key=config_obj.get('aws_secret_key'),
            region_name=config_obj.get('region')
        )
        s3_client = session.client('s3')
        bucket = config_obj.get('bucket')
        source_prefix = config_obj.get('source_prefix')
        destination_prefix = config_obj.get('destination_prefix')

        # Variabel for API LOG
        request = {'Bucket': bucket, 'Prefix': source_prefix}
        ip_address = ''
        try:
            response = s3_client.list_objects_v2(Bucket=bucket, Prefix=source_prefix, MaxKeys=limit)
            for obj in response.get('Contents', []):
                if 'LastModified' in obj:
                    obj['LastModified'] = obj.get('LastModified').isoformat()
                vals = []
                if destination_prefix not in obj.get('Key'):
                    if 'propensity_score' in obj.get('Key'):
                        object = s3_client.get_object(Bucket=bucket, Key=obj.get('Key'))
                        file = object['Body'].read().decode("utf-8").splitlines()
                        separator = ';'
                        csv_reader = csv.reader(file, delimiter=separator)
                        headers = next(csv_reader)
                        filename= obj.get('Key').split('/')[-1]
                        
                        # Iterate over the rows in the CSV file
                        for row in csv_reader:
                            identification_number = row[0] or False
                            mediator_customer = row[1] or False
                            repurchase = row[2] or False
                            purchase_frequency = row[3] or False
                            latest_date_purchase = row[4] or False
                            average_lead_time_months = row[5] or False
                            next_date_purchase = row[6] or False
                            product_type = row[7] or False
                            village = row[8] or False
                            profession = row[9] or False
                            down_payment = row[10] or False
                            down_payment_percent = row[11] or False
                            price_unit_on_road = row[12] or False
                            cash = row[13] or False
                            credit = row[14] or False
                            data_source = row[15] or False
                            branch_code = row[16] or False
                            unique_key = row[17] or False

                            if latest_date_purchase:
                                latest_date_purchase = self._convert_to_yyyy_mm_dd(latest_date_purchase)
                            if next_date_purchase:
                                next_date_purchase = self._convert_to_yyyy_mm_dd(next_date_purchase)
                            if data_source:
                                code = 'MML'
                                if data_source == 'ASP':
                                    code = 'MMA'
                                md_obj = self.env['res.company'].suspend_security().search([
                                    ('code','=',code)
                                ], limit=1)
                            if branch_code:
                                branch_obj = self.env['res.company'].suspend_security().search([
                                    ('code','=',branch_code)
                                ], limit=1)

                            data = {
                                'encryption_identification_number': identification_number,
                                'mediator_customer': True if mediator_customer == 'Yes' else False,
                                'repurchase': True if repurchase == 'Yes' else False,
                                'purchase_frequency': purchase_frequency,
                                'latest_date_purchase': latest_date_purchase,
                                'next_date_purchase': next_date_purchase,
                                'average_lead_time_months': average_lead_time_months,
                                'product_type': product_type,
                                'village': village,
                                'profession': profession,
                                'down_payment': down_payment,
                                'down_payment_percent': down_payment_percent,
                                'price_unit_on_road': price_unit_on_road,
                                'cash': cash,
                                'credit': credit,
                                'md_id': md_obj.id or None,
                                'branch_resource_id': branch_obj.id or None,
                                'unique_code': unique_key,
                                'data_source': 's3_aws',
                                'source_document': filename,
                            }
                            vals.append(data)
                        try:
                            create_crm = self.suspend_security().create(vals)
                        except Exception as err:
                            self._cr.rollback()
                            desc = 'Gagal Saat Membuat CRM S3'
                            return log_obj.suspend_security().create_api_log(title, source_prefix, desc + ' ' + str(err), ip_address, response, request, header={}, response_code=400, model_id=self.id)
                        
                        desc = 'Sukses Membuat CRM S3 ' + filename
                        log_obj.suspend_security().create_api_log(title, source_prefix, desc, ip_address, response, request, header={}, response_code=200, model_id=self.id)
                    try:
                        # move objects to Folder done
                        self.move_object(s3_client, bucket, destination_prefix, obj.get('Key'))
                    except Exception as err:
                        self._cr.rollback()
                        desc = 'Gagal Memindahkan Object S3 ' + obj.get('Key')
                        return log_obj.suspend_security().create_api_log(title, source_prefix, desc + ' ' + str(err), ip_address, response, request, header={}, response_code=400, model_id=self.id)
        
        except Exception as err:
            self._cr.rollback()
            desc = 'Gagal Saat Mengakses Client S3'
            return log_obj.suspend_security().create_api_log(title, source_prefix, desc + ' ' + str(err), ip_address, response, request, header={}, response_code=400, model_id=self.id)

    def move_object(self, s3_client, bucket, destination, object_key):
        # Copy the object to the destination bucket
        key = object_key.split('/')[-1]
        copy_source = {'Bucket': bucket, 'Key': object_key}
        destination_key = f'{destination}/{key}'  # Modify the destination key as needed
        
        s3_client.copy_object(CopySource=copy_source, Bucket=bucket, Key=destination_key)

        # Delete the original object from the source bucket
        s3_client.delete_object(Bucket=bucket, Key=object_key)

    def generate_lead_cdb(self, md='MML', limit=100):
        query = f"""
            SELECT
                encryption_identification_number
            FROM tw_lead_crm tlc
            LEFT JOIN res_company rc ON rc.id = tlc.md_id 
            WHERE 1=1
            AND tlc.state = 'draft'
            AND rc.code = '{md}'
            ORDER BY tlc.next_date_purchase DESC
            LIMIT {limit}
        """
        self._cr.execute(query)
        ress = self._cr.fetchall()
        if ress:
            data = tuple(row[0] for row in ress)
            customer_obj = self._get_cdb_crm_data(data)

    def action_create_lead(self):
        lead_obj = super().action_create_lead()
        if not lead_obj:
            stage_obj = self.env['crm.stage'].suspend_security().search([
                ('name','=','Call')
            ], limit=1)
            date_activity = (datetime.now().replace(hour=9, minute=0, second=0) + timedelta(days=2))
            sales_channel_obj = self.env['tw.selection'].get_selection('SalesChannel', 'data_predictive')
            data_source_obj = self.env['tw.selection'].get_selection('DataSource', 's3_aws')
            vals = {
                'data_by': 'crm',
                'data_source': data_source_obj.id if data_source_obj else False,
                'sales_channel_id': sales_channel_obj.id if sales_channel_obj else False,
            }
            vals_activity = {
                'name': stage_obj.name,
                'stage_id': stage_obj.id,
                'date': date_activity,
            }
            lead_obj = self.lead_id.get_lead_by_identification_number(self.identification_number)
            if lead_obj:
                if not lead_obj.next_activity_id:
                    vals_activity.update({'lead_id': lead_obj.id})
                    activity_obj = self.env['tw.lead.activity'].with_user(lead_obj.employee_id.user_id.id).suspend_security().create(vals_activity)
                    vals.update({'next_activity_id':activity_obj.id})
                
                lead_obj.suspend_security().write(vals)
                self.suspend_security().write({
                    'employee_id':lead_obj.employee_id.id,
                    'company_id':lead_obj.company_id.id,
                    'sales_coordinator_id':lead_obj.sales_coordinator_id.id,
                })
            else:
                interest_obj = self.env['tw.selection'].get_selection('Interest', 'cold')
                vals.update({
                    'customer_name': self.customer_name,
                    'company_id': self.company_id.id,
                    'interest_id': interest_obj.id if interest_obj else False,
                    'unit_availability': 'ready',
                    # 'stage_id': stage_obj.id,
                    'identification_number': self.identification_number,
                    'identification_family_number': self.identification_family_number,
                    'mobile': self.mobile or self.no_wa,
                    'no_wa': self.no_wa,
                    'employee_id': self.employee_id.id,
                    'sales_coordinator_id': self.sales_coordinator_id.id,
                    # Alamat
                    'street': self.street,
                    'rt': self.rt,
                    'rw': self.rw,
                    'state_id': self.state_id.id,
                    'city_id': self.city_id.id,
                    'district_id': self.district_id.id,
                    'sub_district_id': self.sub_district_id.id,
                    'zip_code': self.sub_district_id.zip_code,
                    # Personal Informasi
                    'birthdate': self.birthdate,
                    'gender_id': self.gender_id.id,
                    'religion_id': self.religion_id.id,
                    'blood_type_id': self.blood_type_id.id,
                    'hobby_id': self.hobby_id.id,
                    'education_id': self.education_id.id,
                    'occupation_id': self.occupation_id.id,
                    'unit_usage_id': self.unit_usage_id.id,
                    'unit_operator_id': self.unit_operator_id.id,
                    'motor_brand_id': self.motor_brand_id.id,
                    'motor_type_id': self.motor_type_id.id,
                    'mobile_plan_status_id': self.mobile_plan_status_id.id,
                    'housing_tenure_id': self.housing_tenure_id.id,
                })

                try: 
                    lead_obj = self.env['tw.lead'].suspend_security().create(vals)
                except Exception as err:
                    self.suspend_security().write({
                        'state': 'error',
                        'log_note': err
                    })     
                    return False
                
                vals_activity.update({'lead_id': lead_obj.id})
                activity_obj = self.env['tw.lead.activity'].with_user(lead_obj.employee_id.user_id.id).suspend_security().create(vals_activity)
                lead_obj.suspend_security().write({'next_activity_id': activity_obj.id})

        return lead_obj
    
    def generate_distribution_lead(self, limit=5):
        date = datetime.now()
        start_date = date.replace(day=1)
        end_date = start_date + relativedelta(months=1, days=-1)
        get_holiday = len(self._get_holidays(date.year,date.month))
        working_day = self._get_working_days(start_date, end_date) - get_holiday
        
        query = f"""
            WITH period_crm AS (
                SELECT
                    tlc.employee_id 
                    , MIN(SPLIT_PART(tlc.source_document, '_', 1)::DATE) periode
                FROM tw_lead_crm tlc  
                WHERE tlc.data_source = 's3_aws'
                AND tlc.state = 'outstanding'
                GROUP BY tlc.employee_id 
            )
            SELECT
                CASE
                    WHEN CEIL((count(tlc)::FLOAT/{working_day})) < 1 THEN 1
                    ELSE CEIL((count(tlc)::FLOAT/{working_day}))
                END AS limit_data
                , tlc.employee_id 
                , tlc.source_document
            FROM tw_lead_crm tlc
            LEFT JOIN period_crm pc ON pc.employee_id = tlc.employee_id
            WHERE 1=1
            AND tlc.data_source = 's3_aws'
            AND SPLIT_PART(tlc.source_document, '_', 1)::DATE = pc.periode
            AND NOT EXISTS (
                SELECT 1
                FROM tw_lead_crm last_crm
                WHERE 1=1
                AND last_crm.data_source = 's3_aws'
                AND (last_crm.assign_date + INTERVAL '7 hours')::DATE = CURRENT_DATE
                AND last_crm.employee_id = tlc.employee_id
            )
            AND NOT EXISTS (
                SELECT 1
                FROM tw_sp_digital sp
                JOIN hr_employee hr_sp ON hr_sp.id = sp.employee_id
                WHERE 1=1
                AND sp.state = 'confirmed'
                AND sp.date >= '2024-05-01'
                AND sp.employee_id = tlc.employee_id
                AND hr_sp.working_end_date IS NULL 
            )
            GROUP BY tlc.employee_id, tlc.source_document
            LIMIT {limit}
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        for res in ress:
            limit_data = int(res.get('limit_data'))
            if limit_data > 20:
                limit_data = 20
            crm_obj = self.suspend_security().search([
                ('state','=','outstanding'),
                ('data_source','=','s3_aws'),
                ('employee_id','=',res.get('employee_id')),
                ('source_document','=',res.get('source_document')),
                ('mobile','!=',False),
            ], limit = limit_data)
            if crm_obj:
                for crm in crm_obj:
                    if crm.identification_number and (not crm.identification_number.isdigit() or len(crm.identification_number) not in (16,17)):
                        crm.suspend_security().write({
                            'state': 'error',
                            'log_note': 'No KTP tidak 16 digit atau berisi karakter'
                        })        
                        continue
                    crm.action_assign_form()

    def generate_lead_assigment(self, limit=100):
        query = f"""
            WITH crm AS (
                SELECT
                    tlc.id crm_id
                    , COALESCE(tlc.nearest_company_id, COALESCE(tlc.last_branch_service_id, tlc.branch_resource_id)) company_id
                    , tlc.last_employee_id
                FROM tw_lead_crm tlc
                WHERE 1=1
                AND tlc.state = 'open'
                AND tlc.data_source = 's3_aws'
                LIMIT {limit}
            ),
            matrix AS (
                SELECT
                    he.id AS employee_id
                    , he.parent_id AS sco_id
                    , tlcmal.sequence
                    , rc.id AS company_id
                    , COALESCE(dl_count.lead_count, 0) AS lead_count
                    , ROW_NUMBER() OVER(PARTITION BY rc.id, tlcmal.sequence ORDER BY dl_count.lead_count ASC) AS rn
                FROM tw_lead_crm_matrix_assignment_line tlcmal 
                LEFT JOIN tw_lead_crm_matrix_assignment tlcma ON tlcma.id = tlcmal.matrix_assignment_id 
                LEFT JOIN hr_employee he ON he.job_id = tlcmal.job_id 
                LEFT JOIN res_area ra ON ra.id = he.area_id 
                LEFT JOIN res_area_company_rel rel ON rel.area_id = ra.id 
                LEFT JOIN res_company rc ON rc.id = rel.company_id 
                LEFT JOIN hr_job hj ON hj.id = he.job_id 
                LEFT JOIN (
                    SELECT
                        tl.employee_id
                        , COUNT(tl.id) AS lead_count
                    FROM crm_lead tl
                    WHERE 1=1
                    AND tl.data_source = 's3_aws'
                    GROUP BY tl.employee_id
                ) dl_count ON dl_count.employee_id = he.id
                WHERE 1=1
                AND tlcma.data_source = 's3_aws'
                AND he.working_end_date ISNULL
                AND (hj.name != 'Customer Relation Management' OR (hj.name = 'Customer Relation Management' AND he.is_cro = TRUE))
            )
            SELECT
                crm.crm_id
                , crm.company_id
                , CASE 
                    WHEN he.id NOTNULL AND (he.company_id = crm.company_id OR he.working_end_date ISNULL) THEN he.id
                    ELSE assignnment.employee_id
                END sales_id
                , CASE 
                    WHEN he.id NOTNULL AND (he.company_id = crm.company_id OR he.working_end_date ISNULL) THEN he.parent_id 
                    ELSE assignnment.sco_id
                END sco_id
            FROM crm
            LEFT JOIN hr_employee he ON he.id = crm.last_employee_id
            LEFT JOIN LATERAL (
                SELECT
                    matrix.employee_id
                    , matrix.sco_id
                    , matrix.lead_count
                    , matrix.sequence
                FROM matrix
                WHERE 1=1
                AND matrix.company_id = crm.company_id
                ORDER BY matrix.sequence DESC, matrix.lead_count ASC
                LIMIT 1
            ) assignnment ON TRUE
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        if ress: 
            for data in ress:
                crm_id = data.get('crm_id')
                company_id = data.get('company_id')
                sales_id = data.get('sales_id')
                sco_id = data.get('sco_id')
                crm_obj = self.suspend_security().browse(int(crm_id))
                crm_obj.suspend_security().write({
                    'company_id': company_id,
                    'employee_id': sales_id,
                    'sales_coordinator_id': sco_id,
                })
                crm_obj.action_outstanding()

    def reassign_sales_lead(self, limit=100, branch_code=None):
        additional_where = ''
        if branch_code:
            additional_where = f' AND branch.dealer_kode IN {branch_code}'
        query = f"""
            WITH matrix AS (
                SELECT
                    he.id AS employee_id
                    , tlcmal.sequence
                    , rc.id AS company_id
                    , COALESCE(dl_count.lead_count, 0) AS lead_count
                    , ROW_NUMBER() OVER(PARTITION BY rc.id, tlcmal.sequence ORDER BY dl_count.lead_count ASC) AS rn
                FROM tw_lead_crm_matrix_assignment_line tlcmal 
                LEFT JOIN tw_lead_crm_matrix_assignment tlcma ON tlcma.id = tlcmal.matrix_assignment_id 
                LEFT JOIN hr_employee he ON he.job_id = tlcmal.job_id 
                LEFT JOIN res_area ra ON ra.id = he.area_id 
                LEFT JOIN res_area_company_rel rel ON rel.area_id = ra.id 
                LEFT JOIN res_company rc ON rc.id = rel.company_id 
                LEFT JOIN hr_job hj ON hj.id = he.job_id 
                LEFT JOIN (
                    SELECT
                        tl.employee_id
                        , COUNT(tl.id) AS lead_count
                    FROM tw_lead tl
                    WHERE 1=1
                    AND tl.data_source = 's3_aws'
                    GROUP BY tl.employee_id
                ) dl_count ON dl_count.employee_id = he.id
                WHERE 1=1
                AND tlcma.data_source = 's3_aws'
                AND (hj.name != 'Customer Relation Management' OR (hj.name = 'Customer Relation Management' AND he.is_cro = TRUE))
            )
            SELECT
                lead.id AS lead_id
                , activity.id AS activity_id
                , assignnment.employee_id AS assign_employee_id
            FROM tw_lead AS lead
            LEFT JOIN tw_lead_activity AS activity ON activity.lead_id = lead.id
            LEFT JOIN res_company AS branch ON branch.id = lead.company_id
            LEFT JOIN (
                SELECT dll.lead_id, 
                    COALESCE(COUNT(dll), 0) AS jumlah
                FROM tw_lead_logs dll
                LEFT JOIN tw_selection ts ON dll.category_id = ts.id AND ts.type = 'LogCategory'
                WHERE 1=1
                GROUP BY dll.lead_id
            ) history ON history.lead_id = lead.id
            LEFT JOIN LATERAL (
                SELECT matrix.employee_id,
                matrix.lead_count,
                    matrix.sequence
                FROM matrix
                WHERE matrix.company_id = lead.company_id
                AND matrix.sequence >= COALESCE(history.jumlah, 0) + 1
                ORDER BY matrix.sequence DESC, matrix.lead_count ASC
                LIMIT 1
            ) assignnment ON TRUE
            WHERE 1=1
            AND activity.date IS NOT NULL
            AND activity.activity_result_id IS NULL
            AND lead.state = 'open'
            AND lead.data_source = 's3_aws'
            AND DATE(activity.date + INTERVAL '7 hours') < DATE(NOW())
            {additional_where}
            limit {limit}
        """

        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        if ress: 
            for data in ress:
                lead_id = data.get('lead_id')
                activity_id = data.get('activity_id')
                assign_employee_id = data.get('assign_employee_id')

                crm_obj = self.suspend_security().search([
                    ('lead_id','=',lead_id)
                ], limit=1)
                if crm_obj:
                    lead_obj = crm_obj.lead_id
                    previous_employee_obj = lead_obj.employee_id
                    assign_employee_obj = self.env['hr.employee'].suspend_security().browse(assign_employee_id)
                    history_vals = {
                        'date': datetime.now(),
                        'kategori': 'reassign', 
                        'lead_id': lead_obj.id, 
                    }
                    if assign_employee_obj:
                        date_activity = (datetime.now().replace(hour=9, minute=0, second=0)) + timedelta(days=2)
                        result_obj = self.env['tw.lead.activity.result'].suspend_security().search([('name','=','Overdue')], limit=1)
                        activity_obj = self.env['tw.lead.activity'].suspend_security().browse(activity_id)
                        activity_obj.with_user(lead_obj.employee_id.user_id.id).suspend_security().write({
                            'done_date': datetime.now(),
                            'activity_result_id': result_obj.id,
                        })
                        
                        outstanding_activity_obj = self.env['tw.lead.activity'].suspend_security().search([
                            ('activity_result_id','=',False),
                            ('lead_id','=',lead_obj.id)
                        ], order='id desc', limit=1)
                        if outstanding_activity_obj:
                            continue

                        stage_obj = self.env['crm.stage'].suspend_security().search([
                            ('name','=','Call')
                        ], limit=1)
                        vals_activity = [[0, 0, {
                            'name': stage_obj.name,
                            'stage_id': stage_obj.id,
                            'date': date_activity,
                        }]]
                        history_vals.update({
                            'name': f'Reassign Sales Person Karena tidak dilakukan FU dalam 1 Hari ({previous_employee_obj.name} => {assign_employee_obj.name})'
                        })
                        lead_obj.with_user(assign_employee_obj.user_id.id).suspend_security().write({
                            'employee_id': assign_employee_obj.id,
                            'lead_activity_ids': vals_activity
                        })
                        crm_obj.suspend_security().write({
                            'employee_id': assign_employee_obj.id
                        })
                        
                        # Mengirim ke PIC sebelumnya
                        self.send_reassign_notif_firebase(lead_obj, previous_employee_obj, previous_employee_obj)
                        # Mengirim ke PIC Selanjutnya
                        self.send_reassign_notif_firebase(lead_obj, previous_employee_obj, assign_employee_obj)
                    else:
                        history_vals.update({
                            'name': f'Buku Tamu Menjadi Cancel Karena tidak dilakukan FU' 
                        })
                        lead_obj.suspend_security().write({
                            'state': 'cancel'
                        })
                        crm_obj.suspend_security().write({
                            'state': 'unused'
                        })
                    riwayat = self.env['tw.lead.logs'].suspend_security().create(history_vals)

    def send_reassign_notif_firebase(self, lead_obj, previous_employee_obj, receiver):
        category = self.env['tw.firebase.notification.category'].suspend_security().search([('name','=','Reassign CRM Notification')], limit=1)
        template = category.content_template_id
        if template:
            activity_obj = lead_obj.next_activity_id
            dtgl_fu = activity_obj.date
            tgl_fu = date.strftime(dtgl_fu, "%d %b %Y %I:%M:%S %p")
            name = lead_obj.customer_name
            mobile = lead_obj.mobile or lead_obj.whatsapp
            minat = lead_obj.interest_id.name if lead_obj.interest_id else False
            followup_by = activity_obj.stage_id.name
            pesan = template.content
            
            pesan = pesan.replace('%no_leads%', lead_obj.name)
            pesan = pesan.replace('%sales_sebelum%', previous_employee_obj.name)
            pesan = pesan.replace('%sales_sesudah%', lead_obj.employee_id.name)
            pesan = pesan.replace('%prospek_name%', name)
            pesan = pesan.replace('%prospek_mobile%', mobile)
            pesan = pesan.replace('%prospek_minat%', minat)
            pesan = pesan.replace('%prospek_followup_date%', tgl_fu)

            message_data = {
                'name' : template.name + '[' + receiver.name + ']',
                'message' : pesan,
                'customer_name' : name,
                'company_id' : lead_obj.company_id.id,
                'followup_date': dtgl_fu,
                'employee_receiver_id': receiver.id,
                'category_id' : category.id
            }
            create_message_data= self.env['tw.firebase.notification'].sudo().create(message_data)
            
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
                            obj_firebase_user_obj.notify_single_device(token.firebase_token, data)
                            create_message_data.write({
                                'send_date': self._get_default_date(),
                                'state': 'unread'
                            })
                        except Exception as e:
                            _logger.error(e)

    def reopen_lead_crm(self, limit=100):
        query= f"""
            SELECT
                tlc.id
            FROM tw_lead_crm tlc  
            LEFT JOIN hr_employee he ON he.id = tlc.employee_id
            WHERE 1=1
            AND tlc.data_source = 's3_aws'
            AND tlc.state = 'outstanding'
            AND he.working_end_date NOTNULL
            LIMIT {limit}
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        for res in ress:
            crm_obj = self.suspend_security().search([
                ('id','=',res.get('id')),
            ])
            crm_obj.suspend_security().write({
                'state': 'open',
                'open_uid': False,
                'open_date': False,
                'employee_id': False,
                'sales_coordinator_id': False,
            })

    # 14: private methods
    def _convert_to_yyyy_mm_dd(self, date_string, output_format="%Y-%m-%d"):   
        supported_formats = [
            "%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%d-%m-%Y"
        ]
        for input_format in supported_formats:
            try:
                # Try to parse the input date string using the current format
                parsed_date = datetime.strptime(date_string, input_format)
                
                # Convert the parsed date to the desired output format
                formatted_date = parsed_date.strftime(output_format)
                
                return formatted_date
            except ValueError:
                # Continue to the next format if the current one fails
                pass
        
        # Return None if no valid date is found
        return None
    
    def _get_cdb_crm_data(self, data):
        query = f"""
            SELECT DISTINCT ON (rp.identification_number)
                rp.name customer_name
                , MD5(rp.identification_number) encryption_identification_number
                , rp.identification_number
                , rp.identification_family_number
                , COALESCE(rc.code, last_dso.branch_code) branch_code
                , rp.birthdate tgl_lahir
                , kode_customer.name kode_customer
                , hobi.name hobi
                , rp.ethnic_group suku
                , gol_darah.name gol_darah
                , agama.name agama
                , pendidikan.name pendidikan
                , pekerjaan.name pekerjaan
                , rp.another_job jabatan
                , pengeluaran.name pengeluaran
                , status_hp.name status_hp
                , status_rumah.name status_rumah
                , penggunaan.name penggunaan
                , pengguna.name pengguna
                , jenis_motor.name jenis_motor
                , merk_motor.name merk_motor
                , jenis_kelamin.name jenis_kelamin
                , rp.mobile no_wa
                , COALESCE(last_wo.mobile, rp.mobile) mobile
                , rp.street
                , rp.rt
                , rp.rw
                , rcs.code province_code
                , city.code city_code
                , rd.code kecamatan_code
                , rsd.code kelurahan_code
                , rp.no_npwp pkp
                , rp.tgl_pengukuhan
                , rp.no_npwp npwp
                , rp.alamat_npwp alamat_pkp
                , rp.email
                , last_wo.branch_code last_wo_branch
                , last_dso.last_date_order
                , last_dso.dp_sistem
                , rc3.code nearest_branch
                , last_dso.last_sales_ktp
            FROM res_partner rp
            LEFT JOIN res_company rc ON rc.id = rp.company_id
            LEFT JOIN tw_selection hobi ON hobi.id = rp.hobby_id
            LEFT JOIN tw_selection gol_darah ON gol_darah.id = rp.blood_type_id
            LEFT JOIN tw_selection agama ON agama.id = rp.religion_id
            LEFT JOIN tw_selection pendidikan ON pendidikan.id = rp.education_id
            LEFT JOIN tw_selection pekerjaan ON pekerjaan.id = rp.occupation_id
            LEFT JOIN tw_selection pengeluaran ON pengeluaran.id = rp.expense_id
            LEFT JOIN tw_selection status_hp ON status_hp.id = rp.mobile_plan_status_id
            LEFT JOIN tw_selection status_rumah ON status_rumah.id = rp.house_ownership_id
            LEFT JOIN tw_selection penggunaan ON penggunaan.id = rp.penggunaan_id
            LEFT JOIN tw_selection pengguna ON pengguna.id = rp.pengguna_id
            LEFT JOIN tw_selection jenis_motor ON jenis_motor.id = rp.jenis_motor_id
            LEFT JOIN tw_selection merk_motor ON merk_motor.id = rp.motorcycle_id
            LEFT JOIN tw_selection jenis_kelamin ON jenis_kelamin.id = rp.gender_id
            LEFT JOIN tw_selection kode_customer ON kode_customer.id = rp.customer_code_id
            LEFT JOIN res_country_state rcs ON rcs.id = rp.state_id
            LEFT JOIN res_city city ON city.id = rp.city_id
            LEFT JOIN res_district rd ON rd.id = rp.district_id
            LEFT JOIN res_sub_district rsd ON rsd.id = rp.sub_district_id
            LEFT JOIN res_company rc3 ON rc3.district_id = rp.district_id
            LEFT JOIN LATERAL (
                SELECT
                    rc2.code branch_code
                    , wwo.mobile
                FROM tw_work_order wwo
                LEFT JOIN res_company rc2 ON wwo.company_id = rc2.id
                WHERE 1=1
                AND wwo.customer_id = rp.id
                GROUP BY rc2.code, wwo.mobile
                ORDER BY COUNT(wwo) DESC
                LIMIT 1
            ) last_wo ON TRUE
            LEFT JOIN LATERAL (
                SELECT
                    tso.date_order last_date_order
                    , dsol.discount_regular + tso.amount_discount + dsol_disc.amount_dealer + dsol_disc.amount_ahm + dsol_disc.amount_md + dsol_disc.amount_finco dp_sistem
                    , he.identification_id last_sales_ktp
                    , rc4.code branch_code
                FROM tw_dealer_sale_order tso 
                LEFT JOIN tw_dealer_sale_order_line dsol ON tso.id = dsol.order_id
                LEFT JOIN hr_employee he ON tso.sales_id = he.id
                LEFT JOIN res_company rc4 ON tso.company_id = rc4.id
                LEFT JOIN ( 
                    SELECT
                        order_line_id
                        , SUM(amount_ahm) AS amount_ahm
                        , SUM(amount_md) AS amount_md
                        , SUM(amount_dealer) AS amount_dealer
                        , SUM(amount_finco) AS amount_finco
                    FROM tw_dealer_sale_order_line_program
                    GROUP BY order_line_id
                ) dsol_disc ON dsol_disc.order_line_id = dsol.id
                WHERE 1=1
                AND tso.partner_id = rp.id
                ORDER BY tso.date_order DESC
                LIMIT 1
            ) last_dso ON TRUE
            WHERE MD5(rp.identification_number) IN {str(data).replace(',)', ')')}
        """

        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        if ress:
            for cdb in ress:
                crm_obj = self.suspend_security().search([
                    ('encryption_identification_number','=',str(cdb.get('encryption_identification_number'))),
                    ('state','=','draft'),
                ], limit=1)
                
                try:
                    self._update_cdb_crm(crm_obj, cdb)
                except Exception as err:
                    self._cr.rollback()
                    crm_obj.suspend_security().write({
                        'state': 'error',
                        'log_note': err
                    })
        
    def _update_cdb_crm(self, crm_obj, cdb):
        if crm_obj:
            quest_obj = self.env['tw.selection']
            dp_sistem_percent = 0.0

            vals = {
                'state': 'open',
                'open_uid': self._uid,
                'open_date': self._get_default_datetime(),
                'customer_name': cdb.get('customer_name'),
                'identification_number': cdb.get('identification_number'),
                'identification_family_number': cdb.get('identification_family_number'),
                'mobile': cdb.get('mobile'),
                'no_wa': cdb.get('no_wa'),
                'email': cdb.get('email'),
                'last_date_order': cdb.get('last_date_order'),
                'down_payment_sistem': cdb.get('dp_sistem'),
                # Alamat
                'street': cdb.get('street'),
                'rt': cdb.get('rt'),
                'rw': cdb.get('rw'),
                # Personal Informasi
                'birthdate': cdb.get('tgl_lahir'),
            }

            if cdb.get('dp_sistem'):
                dp_sistem_percent = (float(cdb.get('dp_sistem'))/crm_obj.price_unit_on_road)*100
                vals.update({
                    'down_payment_sistem_percent': dp_sistem_percent,
                })
            
            if cdb.get('province_code'):
                provinsi_obj = self.env['res.country.state'].suspend_security().search([
                    ('code','=',str(cdb.get('province_code')))
                ], limit=1)
                vals.update({
                    'state_id': provinsi_obj.id
                })
            if cdb.get('city_code'):
                city_obj = self.env['res.city'].suspend_security().search([
                    ('code','=',str(cdb.get('city_code')))
                ], limit=1)
                vals.update({
                    'city_id': city_obj.id
                })
            if cdb.get('kecamatan_code'):
                kecamatan_obj = self.env['res.district'].suspend_security().search([
                    ('code','=',str(cdb.get('kecamatan_code')))
                ], limit=1)
                vals.update({
                    'district_id': kecamatan_obj.id
                })
            if cdb.get('kelurahan_code'):
                sub_district_obj = self.env['res.sub.district'].suspend_security().search([
                    ('code','=',str(cdb.get('kelurahan_code')))
                ], limit=1)
                vals.update({
                    'sub_district_id': sub_district_obj.id,
                    'zip_code': sub_district_obj.zip_code
                })

            if cdb.get('jenis_kelamin'):
                gender_obj = quest_obj.get_selection('Gender', str(cdb.get('jenis_kelamin')))
                if gender_obj:
                    vals.update({
                        'gender_id': gender_obj.id
                    })

            if cdb.get('agama'):
                religion_obj = quest_obj.get_selection('Religion', str(cdb.get('agama')))
                if religion_obj:
                    vals.update({
                        'religion_id': religion_obj.id
                    })

            if cdb.get('gol_darah'):
                gol_darah_obj = quest_obj.get_selection('BloodType', str(cdb.get('gol_darah')))
                if gol_darah_obj:
                    vals.update({
                        'blood_type_id': gol_darah_obj.id
                    })

            if cdb.get('hobi'):
                hobi_obj = quest_obj.get_selection('Hobby', str(cdb.get('hobi')))
                if hobi_obj :
                    vals.update({
                        'hobby_id': hobi_obj.id
                    })
                    
            if cdb.get('pendidikan'):
                pendidikan_obj = quest_obj.get_selection('Education', str(cdb.get('pendidikan')))
                if pendidikan_obj:
                    vals.update({
                        'education_id': pendidikan_obj.id
                    })
                    
            if cdb.get('pekerjaan'):
                pekerjaan_obj = quest_obj.get_selection('Occupation', str(cdb.get('pekerjaan')))
                if pekerjaan_obj:
                    vals.update({
                        'occupation_id': pekerjaan_obj.id
                    })

            if cdb.get('penggunaan'):
                penggunaan_obj = quest_obj.get_selection('MotorUtilization', str(cdb.get('penggunaan')))
                if pendidikan_obj:
                    vals.update({
                        'unit_usage_id': penggunaan_obj.id
                    })
                    
            if cdb.get('pengguna'):
                pengguna_obj = quest_obj.get_selection('MotorUser', str(cdb.get('pengguna')))
                if pengguna_obj : 
                    vals.update({
                        'unit_operator_id': pengguna_obj.id
                    })
                    
            if cdb.get('pengeluaran'):
                pengeluaran_obj = quest_obj.get_selection('Expense', str(cdb.get('pengeluaran')))
                if pengeluaran_obj:
                    vals.update({
                        'expense_id': pengeluaran_obj.id
                    })
                    
            if cdb.get('merk_motor'):
                merk_motor_obj = quest_obj.get_selection('MotorBrand', str(cdb.get('merk_motor')))
                if merk_motor_obj:
                    vals.update({
                        'motor_brand_id': merk_motor_obj.id
                    })

            if cdb.get('jenis_motor'):
                jenis_motor_obj = quest_obj.get_selection('MotorType', str(cdb.get('jenis_motor')))
                if gender_obj:
                    vals.update({
                        'motor_type_id': jenis_motor_obj.id
                    })

            if cdb.get('status_hp'):
                status_hp_obj = quest_obj.get_selection('StatusMobilePhone', str(cdb.get('status_hp')))
                if status_hp_obj:
                    vals.update({
                        'mobile_plan_status_id': status_hp_obj.id
                    })

            if cdb.get('status_rumah'):
                status_rumah_obj = quest_obj.get_selection('HousingTenure', str(cdb.get('status_rumah')))
                if status_rumah_obj:
                    vals.update({
                        'housing_tenure_id': status_rumah_obj.id
                    })

            if cdb.get('last_wo_branch'):
                branch_wo_obj = self.env['res.company'].suspend_security().search([
                    ('code','=',str(cdb.get('last_wo_branch')))
                ], limit=1)
                if branch_wo_obj:
                    vals.update({'last_branch_service_id': branch_wo_obj.id})
            if cdb.get('nearest_branch'):
                nearest_branch_obj = self.env['res.company'].suspend_security().search([
                    ('code','=',str(cdb.get('nearest_branch')))
                ], limit=1)
                if nearest_branch_obj:
                    vals.update({'nearest_company_id': nearest_branch_obj.id})
            if cdb.get('last_sales_ktp'):
                last_sales_obj = self.env['hr.employee'].suspend_security().search([
                    ('identification_id','=',str(cdb.get('last_sales_ktp'))),
                    ('job_id.sales_force_id.value','in',('sales_operation_head','salesman','sales_coordinator')),
                ], limit=1)
                if last_sales_obj:
                    vals.update({'last_employee_id': last_sales_obj.id})

            crm_obj.suspend_security().write(vals)