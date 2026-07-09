# 1: imports of python lib
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib
import boto3
import holidays
import pandas as pd
import csv

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwLeadCrm(models.Model):
    _name = "tw.lead.crm"
    _order = "next_date_purchase DESC"
    _description = 'Leads CRM'

    # 7: defaults methods
    def _get_default_datetime(self):
        return datetime.now()
    
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()

    # 8: fields
    name = fields.Char(string='Name', index='trigram', compute='_compute_name', store=True)
    encryption_identification_number = fields.Char(string='No KTP (Enkripsi)')
    purchase_frequency = fields.Char(string='Purchase Frequency')
    product_type = fields.Char(string='Product Type')
    village = fields.Char(string='Village')
    profession = fields.Char(string='Profession')
    unique_code = fields.Char(string='Unique Code')
    source_document = fields.Char(string='Source Document')
    customer_name = fields.Char(string='Customer name')
    identification_number = fields.Char(string='No KTP')
    identification_family_number = fields.Char(string='No kk')
    mobile = fields.Char(string='No HP', size=(13))
    no_wa = fields.Char(string='No WA')
    street = fields.Char(string='Alamat')
    rt = fields.Char(string='Rt', size=3)
    rw = fields.Char(string='Rw', size=3)
    zip_code = fields.Char(string='Kode pos')
    email = fields.Char(string='Email')
    log_note = fields.Text(string='Log Note')

    mediator_customer = fields.Boolean(string='Mediator Customer')
    repurchase = fields.Boolean(string='Repurchase')
    date = fields.Date(string='Date', default=_get_default_datetime)
    periode = fields.Date(string='Periode', compute='_compute_period')
    latest_date_purchase = fields.Date(string='Latest Date Purchase')
    next_date_purchase = fields.Date(string='Next Date Purchase')
    last_date_order = fields.Date(string='Last Date Order')
    birthdate = fields.Date(string='Tanggal lahir')
    average_lead_time_months = fields.Float(string='Avg Lead Time (Months)')
    down_payment = fields.Float(string='Down Payment')
    down_payment_percent = fields.Float(string='Down Payment(%)')
    down_payment_sistem = fields.Float(string='Down Payment Sistem')
    down_payment_sistem_percent = fields.Float(string='Down Payment Sistem(%)')
    price_unit_on_road = fields.Float(string='OTR')
    cash = fields.Integer(string='Cash')
    credit = fields.Integer(string='Credit')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('outstanding', 'Outstanding'),
        ('done', 'Done'),
        ('unused', 'Unused'),
        ('error', 'Error'),
    ], string='Status', default='draft')
    data_source = fields.Selection([
        ('web', 'Web'),
        ('s3_aws', 'S3 AWS')
    ], string='Sumber Data', default='s3_aws')
    
    # Audit Trail
    open_date = fields.Datetime('Open on')
    open_uid = fields.Many2one(comodel_name='res.users', string='Open by')
    outstanding_date = fields.Datetime('Outstanding on')
    outstanding_uid = fields.Many2one(comodel_name='res.users', string='Outstanding by')
    assign_date = fields.Datetime('Assigned on')
    assign_uid = fields.Many2one(comodel_name='res.users', string='Assigned by')

    # 9: relation fields
    lead_id = fields.Many2one(comodel_name='tw.lead', string='Buku Tamu')
    customer_id = fields.Many2one(comodel_name='res.partner', string='Customer')
    company_id = fields.Many2one(comodel_name='res.company', string="Branch", domain="[('parent_id','!=',False)]")
    last_branch_service_id = fields.Many2one(comodel_name='res.company', string='Last Branch Service', domain="[('parent_id','!=',False)]")
    nearest_company_id = fields.Many2one(comodel_name='res.company', string='Nearest Branch', domain="[('parent_id','!=',False)]")
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', domain="[('company_id','=',company_id), ('state','=','approved'), ('working_end_date','=',False), ('atpm_id','!=',False), ('job_id.sales_force_id.value','!=',False)]")
    last_employee_id = fields.Many2one(comodel_name='hr.employee', string='Last Sales Person',help='')
    sales_coordinator_id = fields.Many2one(comodel_name='hr.employee', string='Sales Koordinator', domain="[('company_id','=',company_id), ('state','=','approved'), ('working_end_date','=',False), ('atpm_id','!=',False), ('job_id.sales_force_id.value','in',['sales_coordinator','sales_operation_head','area_manager'])]")
    md_id = fields.Many2one(comodel_name='res.company', string='MD Source', domain="[('branch_type_id.value','=','MD')]")
    branch_resource_id = fields.Many2one(comodel_name='res.company', string='Branch Source', domain="[('parent_id','!=',False)]")

    state_id = fields.Many2one(comodel_name='res.country.state', string='Provinsi')
    city_id = fields.Many2one(comodel_name='res.city', domain="[('state_id','=',state_id)]", string='Kabupaten')
    district_id = fields.Many2one(comodel_name='res.district', domain="[('city_id','=',city_id)]", string='Kecamatan')
    sub_district_id = fields.Many2one(comodel_name='res.sub.district', domain="[('district_id','=',district_id)]", string='Kelurahan')

    gender_id = fields.Many2one(comodel_name='tw.selection', domain="[('type','=','Gender')]", string='Jenis Kelamin')
    blood_type_id = fields.Many2one(comodel_name='tw.selection', domain="[('type','=','BloodType')]", string='Golongan Darah')
    hobby_id = fields.Many2one('tw.selection', domain=[('type','=','Hobby')], string='Hobi')
    religion_id = fields.Many2one(comodel_name='tw.selection', domain="[('type','=','Religion')]", string='Agama')
    education_id = fields.Many2one(comodel_name='tw.selection', domain="[('type','=','Education')]", string='Pendidikan')
    occupation_id = fields.Many2one(comodel_name='tw.selection', domain="[('type','=','Occupation')]", string='Pekerjaan')
    unit_usage_id = fields.Many2one('tw.selection', domain=[('type','=','MotorUtilization')], string='Penggunaan')
    unit_operator_id = fields.Many2one('tw.selection', domain=[('type','=','MotorUser')], string='Pengguna')
    expense_id = fields.Many2one('tw.selection', domain=[('type','=','Expense')], string='Pengeluaran')
    motor_brand_id = fields.Many2one('tw.selection', domain=[('type','=','MotorBrand')], string='Merk Motor')
    motor_type_id = fields.Many2one('tw.selection', string='Jenis Motor', domain=[('type','=','MotorType')])
    mobile_plan_status_id = fields.Many2one('tw.selection', string='Status HP', domain=[('type','=','StatusMobilePhone')])
    housing_tenure_id = fields.Many2one('tw.selection', string='Status Rumah', domain=[('type','=','HousingTenure')])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('source_document', 'data_source')
    def _compute_period(self):
        for record in self:
            if record.source_document and record.data_source == 's3_aws':
                record.periode = record.source_document.split('_')[0]

    @api.depends('company_id')
    def _compute_name(self):
        for lead_crm in self:
            if lead_crm.id:
                code = lead_crm.company_id.code
                if not code:
                    if lead_crm.unique_code:
                        code = lead_crm.unique_code.split('/')[1]
                prefix = 'CRM'
                if lead_crm.data_source == 's3_aws':
                    prefix += '/S3'
                lead_crm.name = self.env['ir.sequence'].get_sequence_code(code, prefix)
            else:
                lead_crm.name = False

    # 12: override methods

    # 13: action methods
    def action_lead_crm_tree(self, menu='raw'):
        domain = [('state','=','draft')]
        context = {
            'search_default_fieldname': 1,
            'readonly_by_pass': 1
        }
        if menu != 'raw':
            domain = [('state','!=','draft')]
            context.update({'search_default_filter_by_outstanding': 1})
        list_view_id = self.env.ref('tw_lead_crm.tw_lead_crm_list_view').id
        form_view_id = self.env.ref('tw_lead_crm.tw_lead_crm_form_view').id
        search_view_id = self.env.ref('tw_lead_crm.tw_lead_crm_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Data Raw CRM',
            'path': 'lead-crm',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.lead.crm',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': context,
        }
    
    def action_assign(self):
        form_id = self.env.ref('tw_lead_crm.tw_lead_crm_assign_form_view').id
        return {
            'name': ('Assign CRM'),
            'res_model': 'tw.lead.crm',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(form_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'view_type': 'form',
            'res_id': self.id
        }

    def action_outstanding(self):
        self.suspend_security().write({
            'state': 'outstanding',
            'outstanding_uid': self._uid,
            'outstanding_date': self._get_default_datetime()
        })

    def action_assign_form(self):
        try: 
            lead_obj = self.action_create_lead()
            if lead_obj:
                self.suspend_security().write({
                    'lead_id': lead_obj.id,
                    'state': 'done',
                    'assign_uid': self._uid,
                    'assign_date': self._get_default_datetime()
                })
        except Exception as err:
            self.suspend_security().write({
                'state': 'error',
                'log_note': err
            })
            return

    def action_create_lead(self):
        return False

    # 14: private methods        
    def _get_holidays(self, year, month):
        # Create a holiday object for Indonesia
        id_holidays = holidays.Indonesia(years=year)

        # Get the list of holidays for the given year and month
        holidays_in_month = [(date, name) for date, name in id_holidays.items() if date.year == year and date.month == month]

        return holidays_in_month
    
    def _get_working_days(self, start_date, end_date):
        date_range = pd.date_range(start=start_date, end=end_date)
        working_days = sum(1 for date in date_range if date.weekday() < 6)  # 0 = Senin, 5 = Sabtu
        
        return working_days