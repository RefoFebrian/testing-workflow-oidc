#!/usr/bin/python
#-*- coding: utf-8 -*-
# 1: imports of python lib
import pytz
from validate_email import validate_email
from datetime import datetime, date, time
from odoo.tools import email_normalize

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
import logging
_logger = logging.getLogger(__name__)

STATES = [('draft', 'Draft'),('approved', 'Approved'),('resign','Resign')]

class Employee(models.Model):
    _inherit = "hr.employee"
    _description = "Employee"
    _rec_names_search = ['name', 'registry_number']

    # 7: defaults methods

    @api.model
    def _get_default_date(self): 
        return date.today().strftime("%Y-%m-%d")
    
    def _get_default_branch(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return company_ids[0].id
        return False
    
    registry_number = fields.Char(string='NIP', help='')
    tax_number = fields.Char(string='No. NPWP', help='')
    contract_number = fields.Char(string='No. Kontrak', help='')
    acc_number = fields.Char('Nomor Rekening', help="Input nomor rekening Employee untuk memproses gaji.")
    acc_holder_name = fields.Char('Nama Pemilik Rekening', help="Input nama pemilik rekening Employee untuk memproses gaji.")
    
    working_start_date = fields.Date(string='Working start date', default=fields.Date.context_today, help='')
    working_end_date = fields.Date(string='Working end date', help='')
    
    is_user = fields.Boolean(string='Create user?', help='Check this option to Create a Login Account for this Employee. ')

    state = fields.Selection(selection=STATES, readonly=True, default=STATES[0][0], string='State', help='')

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch',  help='', domain="[('parent_id', '!=', False)]")
    city_id = fields.Many2one(comodel_name='res.city', domain="[('state_id','=',private_state_id)]", string="Kabupaten / Kota", help='')
    district_id = fields.Many2one(comodel_name='res.district', string="Kecamatan", help="")
    sub_district_id = fields.Many2one(comodel_name='res.sub.district', string="Kelurahan", help="")
    employee_career_record_ids = fields.One2many(comodel_name='tw.employee.career.record', inverse_name='employee_id', string='Employee Career Record')
    bank_id = fields.Many2one('res.bank', string='Bank')
    
    # 10: constraints & sql constraints
    _sql_constraints = [
        ('mobile_phone_uniq', 'unique (mobile_phone)', 'Nomor telp sudah digunakan !'),
        ('identification_id_uniq', 'unique (identification_id)', 'No. KTP sudah digunakan.'),
    ]

    # 10: compute/depends & on change methods
    @api.onchange('sub_district_id')
    def _onchange_sub_district_id(self):
        if self.sub_district_id:
            self.zip = self.sub_district_id.zip_code
    
    @api.onchange('company_id')
    def _onchange_company_job_id(self):
        self.job_id = False
    
    @api.onchange('job_id')
    def _onchange_job_id_department(self):
        self.department_id = False
        if self.job_id:
            self.department_id = self.job_id.department_id.id

    # 12: override methods
    def _create_work_contacts(self):
        for employee in self:
            if not employee.work_contact_id and employee.identification_id:
                partner = self.env['res.partner'].suspend_security().search([('identification_number', '=', employee.identification_id)], limit=1)
                if partner:
                    employee.work_contact_id = partner.id
        
        return super(Employee, self.filtered(lambda e: not e.work_contact_id))._create_work_contacts()

    @api.model_create_multi
    def create(self,vals_list):
        allow_non_branch_control_creation = (self.env['ir.config_parameter'].sudo().get_param('tw_hr.allow_non_branch_control_creation_for_hrd', '').strip().lower() == 'true')

        if allow_non_branch_control_creation:
            group_list_str = (self.env['ir.config_parameter'].sudo().get_param('tw_hr.allow_hrd_group_names', ''))
            allowed_group_names = [g.strip() for g in group_list_str.split(',') if g.strip()]
            user_group_names = self.env.user.groups_id.mapped('name')
            is_hrd = any(name in user_group_names for name in allowed_group_names)

            if not is_hrd:
                for vals in vals_list:
                    job_id = vals.get('job_id')
                    if job_id:
                        job = self.env['hr.job'].browse(job_id)
                        if not job.branch_control:
                            raise Warning('Hanya HRD yang dapat membuat employee untuk job tanpa branch control.')

        to_create_vals = []
        existing_employee = []
        for vals in vals_list:
            create_employee = True
            employee_career_record_ids = []
            if vals.get('identification_id'):
                if not vals['identification_id'].isdigit() or len(vals['identification_id']) != 16:
                    raise Warning('Perhatian, Format penulisan No KTP harus angka dan 16 Digit.')

                emp = self.suspend_security().with_context(active_test=False).search([('identification_id','=',vals.get('identification_id'))])
                if emp:
                    if self.env.context.get('import_file'):
                        raise Warning(f'Import gagal, Data Karyawan dengan NIK {vals.get("identification_id")} sudah ada')
                    self.reactive_user_data(emp,vals)
                    create_employee = False
                    existing_employee.append(emp)
                
            if vals.get('name'):
                vals['name'] = vals['name'].title()
                
            if vals.get('work_email'):
                if not validate_email(vals['work_email']):
                    raise Warning('Email tidak valid, silahkan dicek kembali.')  
                vals['work_email'] = vals['work_email']

            if vals.get('mobile_phone'):
                self.validate_phone_number(vals['mobile_phone'], 'Mobile Phone Number')
                # If importing, check for existing mobile number to avoid unique constraint violation
                if self.env.context.get('import_file'):
                    existing_mobile = self.env['hr.employee'].sudo().search_count([
                        ('mobile_phone', '=', vals['mobile_phone'])
                    ])
                    if existing_mobile > 0:
                        vals['mobile_phone'] = False

            if vals.get('work_phone'):
                self.validate_phone_number(vals['work_phone'], 'Work Phone Number')

            if vals.get('emergency_phone'):
                self.validate_phone_number(vals['emergency_phone'], 'Emergency Phone Number')
                
            if vals.get('identification_id'):
                if not vals['identification_id'].isdigit() or len(vals['identification_id']) != 16:
                    raise Warning('Perhatian, Format penulisan No KTP harus angka dan 16 Digit.')
            
            group_id = False
            jobs = False
            if vals.get('job_id'):
                jobs = self.env['hr.job'].suspend_security().browse(vals['job_id'])
                if 'department_id' not in vals and jobs.department_id:
                    vals['department_id'] = jobs.department_id.id

                employee_career_record_ids.append(Command.create({
                    'type': self.env.ref('tw_hr.tw_hr_job_career_record_type_new_hire').value or 'new_hire',
                    'model_name': 'hr.job',
                    'date_assign': datetime.now(),
                    'remark': _("Newly assigned employee"),
                    'curr_id': jobs.id
                }))
            
            if vals.get('company_id'):
                branch = self.env['res.company'].suspend_security().browse(vals['company_id'])
                employee_career_record_ids.append(Command.create({
                    'type': self.env.ref('tw_hr.tw_hr_job_career_record_type_transfer').value or 'transfer',
                    'model_name': 'res.company',
                    'date_assign': datetime.now(),
                    'remark': _(f"Assigned to branch: {branch.name}"),
                    'curr_id': branch.id
                }))

            if not jobs: 
                if vals.get('job_title'):
                    jobs = self.env['hr.job'].suspend_security().search([('name','=',vals['job_title'])],limit=1)
                    vals['job_id'] = vals.get('job_id') or jobs.id
                    if not jobs:
                        raise Warning('Perhatian ! Job %s tidak ditemukan.' %vals.get('job_title'))
            
                    group_id = jobs.group_id.id
                    if not group_id: 
                        raise Warning('Perhatian ! User Group belum diisi di Master Job.')
            
                    if not vals.get('department_id'):
                        if jobs.department_id:
                            vals['department_id'] = jobs.department_id.id 
            
            if employee_career_record_ids:
                vals['employee_career_record_ids'] = employee_career_record_ids

            if create_employee:
                to_create_vals.append(vals)

        # Clean stale resource_ids from previous import passes (Test vs Import)
        if self.env.context.get('import_file'):
            for v in to_create_vals:
                v.pop('resource_id', None)

        print(str(to_create_vals))
        create = super().create(to_create_vals)
        for emp in create:
            emp._create_bank_accounts()
            if emp.is_user:
                emp.with_company(emp.company_id.id).create_user()
            
            if emp.identification_id and emp.work_contact_id:
                emp.work_contact_id.suspend_security().write({'identification_number': emp.identification_id})

        return create

    def write(self,vals):
        employee_career_record_ids = []
        sensitive_fields = {
            'identification_id',
            'registry_number',
            'mobile_phone',
            'work_phone',
            'bank_account_id',
            'working_start_date',
            'working_end_date'
        }

        allow_non_branch_control_creation = (
                str(self.env['ir.config_parameter'].sudo()
                    .get_param('tw_hr.allow_non_branch_control_creation_for_hrd', 'false')
                    ).strip().lower() == 'true'
        )

        group_list_str = self.env['ir.config_parameter'].sudo().get_param('tw_hr.allow_hrd_group_names', '')
        allowed_group_names = [g.strip() for g in group_list_str.split(',') if g.strip()]
        user_group_names = self.env.user.groups_id.mapped('name')

        is_hrd = False
        if allow_non_branch_control_creation:
            is_hrd = any(name in user_group_names for name in allowed_group_names)

        is_hr_admin = is_hrd or self.env.user.has_group('base.group_system')

        if not is_hr_admin:
            for record in self:
                if record.job_id and record.job_id.exists() and not record.job_id.branch_control:
                    modified_sensitive_fields = sensitive_fields.intersection(vals.keys())
                    if modified_sensitive_fields:
                        raise Warning(
                            _(
                                "Anda tidak memiliki izin untuk mengubah field data pribadi (%s) "
                                "untuk karyawan yang job-nya tidak memiliki branch control."
                            ) % ", ".join(modified_sensitive_fields)
                        )

        if vals.get('name'):
            vals['name'] = vals['name'].title()
        if vals.get('identification_id'):
            ktp_employee = self.suspend_security().with_context(active_test=False).search([('identification_id','=',vals['identification_id']),('id','!=',self.id)],limit=1)
            if ktp_employee:
                raise Warning('KTP sudah digunakan pada salesman %s (%s). \nSilahkan aktifkan kembali user tsb' % (ktp_employee.name,str(ktp_employee.id)))
            if not vals['identification_id'].isdigit() or len(vals['identification_id']) != 16:
                raise Warning('Perhatian, Format penulisan No KTP harus angka dan 16 Digit.')
            
        if vals.get('work_email'):
            if not validate_email(vals['work_email']):
                raise Warning('Email tidak valid, silahkan dicek kembali.')  
            vals['work_email'] = vals['work_email']

        if vals.get('mobile_phone'):
            self.validate_phone_number(vals['mobile_phone'], 'Mobile Phone Number')

        if vals.get('work_phone'):
            self.validate_phone_number(vals['work_phone'], 'Work Phone Number')

        if vals.get('emergency_phone'):
            self.validate_phone_number(vals['emergency_phone'], 'Emergency Phone Number')
        
        if vals.get('identification_id'):
            if not vals['identification_id'].isdigit() or len(vals['identification_id']) != 16:
                raise Warning('Perhatian, Format penulisan No KTP harus angka dan 16 Digit.')
       
        if vals.get('job_id',False):
            employee_career_record_ids.append(Command.create({
                'type': self.env.ref('tw_hr.tw_hr_job_career_record_type_promotion').value or 'promotion',
                'model_name': 'hr.job',
                'date_assign': datetime.now(),
                'remark': _("New assigned role."),
                'prev_id': self.job_id.id,
                'curr_id': vals.get('job_id')
            }))
            if self.user_id:
                self.user_id.suspend_security().groups_id = False
                job = self.env['hr.job'].suspend_security().browse(vals['job_id'])
                if not job.group_id:
                    raise Warning('Perhatian ! User Group belum diisi di Master Job.')
                groups_to_set = [job.group_id.id]
                internal_user_group = self.env.ref('base.group_user', raise_if_not_found=False)
                if internal_user_group:
                    groups_to_set.append(internal_user_group.id)
                self.user_id.suspend_security().write({'groups_id': [(6, 0, groups_to_set)]})

        if vals.get('job_id'):
            job = self.env['hr.job'].browse(vals['job_id'])
            is_sales_force = bool(job.sales_force_id)
            allow_non_branch_control_creation = (self.env['ir.config_parameter'].sudo().get_param('tw_hr.allow_non_branch_control_creation_for_hrd', '').strip().lower() == 'true')
            group_list_str = self.env['ir.config_parameter'].sudo().get_param('tw_hr.allow_hrd_group_names', '')
            allowed_group_names = [g.strip() for g in group_list_str.split(',') if g.strip()]
            user_group_names = self.env.user.groups_id.mapped('name')

            is_hrd = False
            if allow_non_branch_control_creation:
                is_hrd = any(name in user_group_names for name in allowed_group_names)

            if self.env.user._is_admin():
                is_hrd = True

            if is_sales_force and not is_hrd:
                today = fields.Date.today()
                if today.day != 1:
                    raise Warning("Perubahan Job Sales Force hanya boleh dilakukan pada tanggal 1, kecuali oleh HRD.")

        if vals.get('company_id'):
            if self.company_id.id != vals.get('company_id'):
                employee_career_record_ids.append(Command.create({
                    'type': self.env.ref('tw_hr.tw_hr_job_career_record_type_transfer').value or 'transfer',
                    'model_name': 'res.company',
                    'date_assign': datetime.now(),
                    'remark': _("Transfer employee to branch"),
                    'prev_id': self.company_id.id,
                    'curr_id': vals.get('company_id')
                }))

        if employee_career_record_ids:
            vals['employee_career_record_ids'] = employee_career_record_ids

        if vals.get('is_user',False):
            if not self.user_id:
                login = self.registry_number
                name = self.name
                email = self.work_email
                group_id = False
                if vals.get('registry_number',False):
                    login = vals['registry_number'] 
                if vals.get('name',False):
                    name = vals['name'] 
                if vals.get('job_id',False):
                    jobs = self.env['hr.job'].suspend_security().browse(vals['job_id'])
                    if not jobs.group_id:
                        raise Warning('Perhatian ! User Group belum diisi di Master Job.')    
                    group_id = jobs.group_id.id 
                if vals.get('email',False):
                    email = vals['email']
                
                # Check if group is false
                if not group_id:
                    if not self.job_id.group_id:
                        raise Warning('Perhatian ! User Group belum diisi di Master Job.')    
                    else:
                        group_id = self.job_id.group_id.id
                        
        if vals.get('working_end_date',False):
            if 'is_user' not in vals:
                vals['is_user'] = False
            if 'state' not in vals:
                vals['state'] = 'resign'
            if self.user_id:
                self.user_id.suspend_security().write({'active': False})

        write = super(Employee,self).write(vals)
        for employee in self:
            if vals.get('is_user'):
                employee.suspend_security().create_user()
            
            if vals.get('identification_id') and employee.work_contact_id:
                employee.work_contact_id.suspend_security().write({'identification_number': vals['identification_id']})

        return write

    def unlink(self):
        for record in self:
            raise Warning('Perhatian ! \n Data tidak bisa dihapus, silahkan non-aktifkan !')
        return super(Employee, self).unlink()

    # 13: action methods
    def action_employee_tree(self, category='all'):
        domain = []
        context = {'search_default_fieldname': 1, 'readonly_by_pass': 1}
        name = 'All Employee'
        job_ids = self.env['hr.job'].sudo().search([])
        if category == 'salesman':
            name = 'Salesman'
            domain += [('job_id.branch_control','=','salesman')]
            job_ids = job_ids.filtered(lambda job: job.branch_control == 'salesman')
        elif category == 'mechanic':
            name = 'Mechanic'
            domain += [('job_id.branch_control','=','workshop')]
            job_ids = job_ids.filtered(lambda job: job.branch_control == 'workshop')
        if job_ids:
            context['default_job_ids'] = job_ids.ids
        list_view_id = self.env.ref('tw_hr.tw_hr_employee_list_view').id
        form_view_id = self.env.ref('tw_hr.tw_hr_employee_form_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': 'employees',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'hr.employee',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'context': context
        }
    
    def action_open_user(self):
        domain = []
        context = {}
        form_view_id = self.env.ref('base.view_users_form').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Users',
            'path': 'users',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.users',
            'nodestroy': True,
            'res_id': self.user_id.id,
            'domain': domain,
            'views': [(form_view_id, 'form')],
            'context': context
        }
    
    def action_confirm(self):
        self.state = STATES[1][0]

    def action_done(self):
        self.state = STATES[2][0]

    def action_draft(self):
        self.state = STATES[0][0]

    def action_employee_deactivate(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Deactivate Employee',
            'res_model': 'hr.employee',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'views': [(self.env.ref('tw_hr.tw_employee_deactivate_form_view').id, 'form')],
        }

    def action_confirm_deactivate(self):
        self.ensure_one()
        if not self.active:
            raise Warning(_("This employee is already deactivated."))
        if not self.working_end_date:
            raise Warning(_("Please set working end date first."))

        user_tz = self.env.user.tz or 'UTC'
        tz = pytz.timezone(user_tz)

        dt_local = tz.localize(datetime.combine(self.working_end_date, time(23, 59, 59)))
        dt_utc = dt_local.astimezone(pytz.UTC).replace(tzinfo=None)

        termination_type = self.env.ref('tw_hr.tw_hr_job_career_record_type_termination').value or 'termination'
        existing_record = self.env['tw.employee.career.record'].search([
            ('employee_id', '=', self.id),
            ('type', '=', termination_type),
            ('date_assign', '>=', fields.Datetime.now())
        ], limit=1)

        vals = {}

        if existing_record:
            existing_record.date_assign = dt_utc
        else:
            vals['employee_career_record_ids'] = [Command.create({
                'employee_id': self.id,
                'type': termination_type,
                'model_name': 'hr.employee',
                'model_id': self.id,
                'date_assign': dt_utc,
                'remark': _('Employee no longer active'),
                'curr_id': self.id,
            })]

        if self.working_end_date < fields.Date.today():
            vals['active'] = False

        if vals:
            self.write(vals)

        return {'type': 'ir.actions.act_window_close'}

    def action_employee_reactivate(self):
        self.ensure_one()
        vals = {
            'working_end_date': False,
            'active': True,
            'state': 'draft',
        }
        self.reactive_user_data(self, vals)

        self.write({
            'employee_career_record_ids': [Command.create({
                'employee_id': self.id,
                'type': self.env.ref('tw_hr.tw_hr_job_career_record_type_contract_renewal').value or 'contract renewal',
                'model_name': 'hr.employee',
                'model_id': self.id,
                'date_assign': datetime.now(),
                'remark': _('Employee is active again'),
                'curr_id': self.id,
            })]
        })

    # 14: private methods
    def _cron_deactivate_employees(self, limit = 50):
        employees = self.search([('working_end_date', '<', fields.Date.today()), ('active', '=', True)], limit = limit)
        for employee in employees:
            employee.write({'active': False})

    def validate_phone_number(self, phone_number, field_name):
        if not phone_number.isdigit() or len(phone_number) < 5:
            raise Warning(f"Perhatian !, Format {field_name} harus angka dan minimal 5 digit.")

    def reactive_user_data(self,emp,vals):
        vals['working_end_date'] = False
        vals['active'] = True
        vals['state'] = 'draft'
        
        user_data = {
            'active' : True,
        }

        if vals.get('work_email'):
            user_data['email'] = vals.get('work_email')
        
        emp.suspend_security().write(vals)
        if emp.user_id:
            emp.user_id.write(user_data)
        else:
            if emp.is_user or vals.get('is_user'):
                create_user = self.create_user()
                emp.user_id = create_user

    def create_user(self, **kwargs):
        self.ensure_one()
        login = kwargs.get('login') or self.registry_number
        user_vals = self._get_user_vals(**kwargs)
        
        user_obj = self.user_id
        if user_obj:
            user_obj.write(user_vals)
        else:
            # Check existing user
            existing_user = self.env['res.users'].sudo().with_context(active_test=False).search([('login','=',login)],limit=1)
            if existing_user:
                raise Warning('User dengan login %s sudah ada, silahkan periksa kembali' % login)
            # Create new user
            user_obj = self.env['res.users'].sudo().with_context(no_reset_password=False)._create_user_from_template(user_vals)
        
        # Penulisan group tidak bisa dilakukan saat create, karena hanya value yang aman yang dapat ditulis
        group_id = kwargs.get('group_id') or self.job_id.group_id.id
        groups_to_add = []
        if group_id:
            groups_to_add.append((4, group_id))
        
        internal_user_group = self.env.ref('base.group_user', raise_if_not_found=False)
        if internal_user_group:
            groups_to_add.append((4, internal_user_group.id))
            
        portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
        if portal_group:
            groups_to_add.append((3, portal_group.id))
            
        public_group = self.env.ref('base.group_public', raise_if_not_found=False)
        if public_group:
            groups_to_add.append((3, public_group.id))
            
        if groups_to_add:
            user_obj.write({
                'groups_id': groups_to_add
            })
        # Simpan user_id ke employee
        self.write({'user_id': user_obj.id})
        return user_obj
    
    def _get_user_vals(self, **kwargs):
        name = kwargs.get('name') or self.name
        login = kwargs.get('login') or self.registry_number
        email = email_normalize(kwargs.get('work_email') or self.work_email)
        company_id = self.company_id.id or self.env.company.id
        area_ids = kwargs.get('area_ids') or self.area_id.company_ids.ids
        return {
            'active': True,
            'create_employee_id': self.id,
            'partner_id': self.work_contact_id.id,
            'name': name,
            'login': login,
            'email': email,
            'company_id': company_id,
            'company_ids': [(6, 0, area_ids)],
            # 'oauth_provider_id':oauth_obj.id, # TODO: oauth doesn't exist. turn on later?
            # 'oauth_uid':work_email, # TODO: oauth doesn't exist. turn on later?
        }

    def get_api_login(self, user):       
        query = """
            SELECT emp.company_id FROM hr_employee emp  
            LEFT JOIN resource_resource resource ON resource.id=emp.resource_id
            WHERE resource.user_id = %s
        """% (user["user"])
        self._cr.execute(query)
        ress1 = self._cr.fetchone()
        return ress1[0]
    
    def get_employee_career_record(self, date, record_type='role'):
        self.ensure_one()
        types = ['promotion', 'demotion', 'new_hire', 'contract_renewal']
        if record_type == 'mutation':
            types = ['transfer', 'rotation']
        elif record_type == 'termination':
            types = ['resignation', 'termination', 'retirement']

        filtered_record = self.employee_career_record_ids.filtered(lambda rec: rec.date_assign <= date and rec.type in types)
        if filtered_record:
            return filtered_record.sorted(key=lambda rec: rec.date_assign)[-1]
        return filtered_record

    def _create_bank_accounts(self, **kwargs):
        for emp in self:
            vals = emp.get_bank_account_vals(**kwargs)
            if not vals.get('acc_number'):
                continue
            
            # Check if bank account already exists to avoid unique constraint violation
            existing_bank = self.env['res.partner.bank'].sudo().search([
                ('acc_number', '=', vals['acc_number'])
            ], limit=1)
            
            if existing_bank:
                # Update existing bank account details if provided
                update_vals = {}
                # Odoo prevents changing partner_id if the bank account is 'trusted'.
                # We only attempt to update it if the partner is different.
                if vals.get('partner_id') and existing_bank.partner_id.id != vals['partner_id']:
                    update_vals['partner_id'] = vals['partner_id']
                if vals.get('acc_holder_name'):
                    update_vals['acc_holder_name'] = vals['acc_holder_name']
                
                if update_vals:
                    try:
                        existing_bank.sudo().write(update_vals)
                    except Exception as e:
                        if not self.env.context.get('import_file'):
                            raise Warning(f'Error: {e}')
                        else:
                            _logger.warning(f'Error: {e}')
                
                emp.bank_account_id = existing_bank.id
            else:
                back_accoung_obj = self.env['res.partner.bank'].suspend_security().create(vals)
                if back_accoung_obj:
                    emp.bank_account_id = back_accoung_obj.id

    def get_bank_account_vals(self, **kwargs):
        bank_id = kwargs.get('bank_id') or self.bank_id.id
        acc_number = kwargs.get('acc_number') or self.acc_number
        acc_holder_name = kwargs.get('acc_holder_name') or self.acc_holder_name
        partner_id = kwargs.get('work_contact_id') or self.work_contact_id.id 

        vals = {
            'bank_id': bank_id,
            'acc_number': acc_number,
            'acc_holder_name': acc_holder_name,
            'partner_id': partner_id,
        }

        return vals
        
