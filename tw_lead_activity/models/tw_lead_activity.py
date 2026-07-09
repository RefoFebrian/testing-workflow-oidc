# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools.translate import _

# 5: local imports

# 6: Import of unknown third party lib


class TwLeadActivity(models.Model):
    _name = "tw.lead.activity"
    _description = "Lead Activity"

    # 7: default methods
    def _get_default_datetime(self):
        return datetime.now()

    def _get_default_date(self):
        return date.today()

    # 8: fields
    name = fields.Char(string='Name', compute='_compute_name_activity', store=True,help='')
    date = fields.Datetime(string='Date', default=_get_default_datetime, help='')
    remark = fields.Text(string='Remark', help='')
    interest = fields.Char(related='interest_id.value', string='Interest Name', help='')
    latitude = fields.Float(string='Latitude', help='')
    longitude = fields.Float(string='Longitude', help='')
    stage = fields.Char(related='stage_id.name', string='Stage Name', help='')
    email = fields.Char(string='Email', help='')

    identification_number = fields.Char(string='No KTP', help='')
    identification_family_number = fields.Char(string='No KK', help='')
    mobile = fields.Char(string='Phone Number', help='')
    whatsapp = fields.Char(string='Whatsapp', help='')
    birthplace = fields.Char(string='Place of Birth', help='')
    birthdate = fields.Date(string='Date of Birth', help='')
    neighborhood = fields.Char(string='Neighborhood', help='')
    done_date = fields.Datetime(string='Done Date', help='')
    community = fields.Char(string='Community', help='')
    current_motorcycle = fields.Selection([
        ('ada', 'Ada'),
        ('tidak_ada', 'Tidak Ada')], string='Motor Sekarang', help="Currently owned motorcycle"
    )
    down_payment = fields.Float(string='Down Payment', help='')
    down_payment_date = fields.Date(string='Down Payment Date', help='')
    tenor = fields.Integer(string='Tenor', help='')
    installment = fields.Float(string='Installment', help='')
    discount = fields.Float(string='Discount', help='')
    payment_type = fields.Char(related='payment_type_id.value', string='Payment Type string', help='')
    due_date = fields.Date(string='Due Date', help='')
    followup_state = fields.Selection(selection=[
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed')
    ], string='Follow-up State', help="")
    relative_phone_number = fields.Char(store=True)
    is_test_ride = fields.Boolean(string='Test Ride?')
    test_ride_date = fields.Date(string='Test Ride Date')

    # Addresses Fields
    rt = fields.Char('RT', store=True)
    rw = fields.Char('RW', store=True)
    street = fields.Char('Street', store=True)
    street2 = fields.Char('Street2', store=True)
    zip = fields.Char('Zip', store=True)
    
    is_same_ktp = fields.Boolean('Sesuai dengan KTP?', help="Is domicile address same with KTP", store=True)
    rt_domicile = fields.Char('RT Domisili', store=True)
    rw_domicile = fields.Char('RW Domisili', store=True)
    street_domicile = fields.Char('Street Domisili', store=True)
    street2_domicile = fields.Char('Street2 Domisili', store=True)
    zip_domicile = fields.Char('Zip Domisili', store=True)

    # 9: relation fields
    # Addresses
    country_id = fields.Many2one('res.country', string="Negara", store=True ) 
    state_id = fields.Many2one('res.country.state', string="Provinsi", domain="[('country_id', '=?', country_id)]", store=True)
    city_id = fields.Many2one(comodel_name='res.city', string="Kabupaten", domain="[('state_id', '=', state_id)]", help='', store=True)
    district_id = fields.Many2one(comodel_name='res.district', string="Kecamatan", domain="[('city_id', '=', city_id)]", help='', store=True)
    sub_district_id = fields.Many2one(comodel_name='res.sub.district', string="Kelurahan", domain="[('district_id', '=', district_id)]", help='', store=True)
        
    country_domicile_id = fields.Many2one('res.country', string="Negara Domisili", store=True ) 
    state_domicile_id = fields.Many2one('res.country.state', string="Provinsi Domisili", domain="[('country_id', '=?', country_domicile_id)]", store=True)
    city_domicile_id = fields.Many2one(comodel_name='res.city', string="Kabupaten Domisili", domain="[('state_id', '=', state_domicile_id)]", help='', store=True)
    district_domicile_id = fields.Many2one(comodel_name='res.district', string="Kecamatan Domisili", domain="[('city_id', '=', city_domicile_id)]", help='', store=True)
    sub_district_domicile_id = fields.Many2one(comodel_name='res.sub.district', string="Kelurahan Domisili", domain="[('district_id', '=', district_domicile_id)]", help='', store=True)

    product_id = fields.Many2one(comodel_name='product.product', string='Product', domain="[('sale_ok','=',True), ('categ_id', 'in', product_category_ids)]")
    stage_id = fields.Many2one(comodel_name='crm.stage', string='Stage', help='')
    interest_id = fields.Many2one(comodel_name='tw.selection', domain="[('type', '=', 'Interest')]", string='Interest', help='')
    # customer_code_id = fields.Many2one(comodel_name='tw.selection', domain="[('type','=','CustomerCode')]", string='Customer Code', compute='_compute_customer_data', store=True, help='')
    lead_id = fields.Many2one(comodel_name='tw.lead', string='Lead', index=True, ondelete='cascade', help='')
    activity_result_id = fields.Many2one(comodel_name='tw.lead.activity.result', string='Follow-up Result', help='')
    next_activity_id = fields.Many2one(comodel_name='tw.lead.activity', string='Next Activity', help='')
    gender_id = fields.Many2one(comodel_name='tw.selection', domain="[('type','=','Gender')]", string='Gender', store=True, help='')
    blood_type_id = fields.Many2one(comodel_name='tw.selection', domain="[('type','=','BloodType')]", string='Blood Type', store=True, help='')
    religion_id = fields.Many2one(comodel_name='tw.selection', domain="[('type','=','Religion')]", string='Agama', store=True, help='')
    education_id = fields.Many2one(comodel_name='tw.selection', domain="[('type','=','Education')]", string='Pendidikan', store=True, help='')
    occupation_id = fields.Many2one(comodel_name='tw.selection', domain="[('type','=','Occupation')]", string='Pekerjaan', store=True, help='')
    payment_type_id = fields.Many2one(comodel_name='tw.selection', domain="[('type','=','PaymentType')]", string='Payment Type', store=True, help='')
    finco_id = fields.Many2one(comodel_name='res.partner', string='Finco', store=True, domain="[('category_id.name', '=', 'Finance Company')]", help='')
    
    unit_usage_id = fields.Many2one(comodel_name='tw.selection', string='Penggunaan Motor', domain=[('type', '=', 'MotorUtilization')])
    unit_operator_id = fields.Many2one(comodel_name='tw.selection', string='Pengguna Motor', domain=[('type', '=', 'MotorUser')])
    motor_brand_id = fields.Many2one(comodel_name='tw.selection', string='Merk Motor Sekarang', domain=[('type', '=', 'MotorBrand')])
    motor_type_id = fields.Many2one(comodel_name='tw.selection', string='Type Motor Sekarang', domain=[('type', '=', 'MotorType')])
    motor_ownership_id = fields.Many2one(comodel_name='tw.selection', string="Kepemilikan Motor", domain=[('type', '=', 'MotorOwnership')])
    motor_ownership = fields.Char(related='motor_ownership_id.value', string='Motor Ownership')
    partner_stnk_id = fields.Many2one(comodel_name='res.partner', string='Nama di STNK')
    
    product_category_ids = fields.Many2many(
        comodel_name='product.category',
        relation='tw_lead_activity_prod_categ_rel', column1='lead_activity_id', column2='product_category_id',
        default=lambda self: self.env['product.category'].get_child_ids('Unit'),
        string="Product Category")

    # 10: constraints & sql constraints
    @api.constrains('rt', 'rw', 'zip', 'rt_domicile', 'rw_domicile', 'zip_domicile')
    def _validate_address_digits(self):
        for record in self:
            for field, label in [
                ('rt', 'RT'), ('rw', 'RW'), ('zip', 'ZIP'),
                ('rt_domicile', 'RT Domisili'), ('rw_domicile', 'RW Domisili'), ('zip_domicile', 'ZIP Domisili')
            ]:
                val = record[field]
                if val and not val.isdigit():
                    raise Warning(f"{label} harus berisi angka.")

    @api.constrains('date', 'down_payment_date')
    def _validate_dates(self):
        today = date.today()
        for record in self:
            if record.date:
                # record.date is Datetime
                if record.date.date() < today:
                    raise Warning("Tanggal Aktivitas tidak boleh lewat dari hari ini.")
            if record.down_payment_date and record.down_payment_date < today:
                raise Warning("Tanggal Uang Muka tidak boleh lewat dari hari ini.")

    @api.constrains('down_payment', 'discount', 'tenor', 'installment', 'payment_type_id')
    def _validate_financials(self):
        for record in self:
            if record.down_payment < 0:
                raise Warning("Uang Muka tidak boleh negatif.")
            if record.discount < 0:
                raise Warning("Discount tidak boleh negatif.")
            if record.payment_type_id.value == 'Credit':
                if record.tenor <= 0:
                    raise Warning("Tenor harus lebih besar dari 0 untuk pembayaran Kredit.")
                if record.installment <= 0:
                    raise Warning("Cicilan harus lebih besar dari 0 untuk pembayaran Kredit.")

    # 11: compute/depends & on change methods
    @api.depends('stage_id', 'lead_id.name')
    def _compute_name_activity(self):
        for act in self:
            if act.stage_id and act.lead_id.name:
                act.name = f'{act.lead_id.name} - {act.stage_id.name}'

    @api.onchange('is_same_ktp')
    def _onchange_is_same_ktp(self):
        self.street_domicile = False
        self.street2_domicile = False
        self.rt_domicile = False
        self.rw_domicile = False
        self.zip_domicile = False
        self.state_domicile_id = False
        self.city_domicile_id = False
        self.district_domicile_id = False
        self.sub_district_domicile_id = False
        if self.is_same_ktp:
            self.street_domicile = self.street
            self.street2_domicile = self.street2
            self.rt_domicile = self.rt
            self.rw_domicile = self.rw
            self.state_domicile_id = self.state_id
            self.city_domicile_id = self.city_id
            self.district_domicile_id = self.district_id
            self.sub_district_domicile_id = self.sub_district_id
            self.zip_domicile = self.zip

    @api.onchange('state_id')
    def _onchange_state_id(self):
        self.city_id = False

    @api.onchange('city_id')
    def _onchange_city_id(self):
        self.district_id = False
    
    @api.onchange('district_id')
    def _onchange_district_id(self):
        self.sub_district_id = False

    @api.onchange('sub_district_id')
    def _onchange_sub_district(self):
        if self.sub_district_id:
            self.zip = self.sub_district_id.zip_code
    
    @api.onchange('sub_district_domicile_id')
    def _onchange_sub_district_domicile(self):
        self.zip_domicile = False
        if self.sub_district_domicile_id:
            self.zip_domicile = self.sub_district_domicile_id.zip_code
    
    @api.onchange('state_domicile_id')
    def _onchange_state_domicile_id(self):
        if not self.state_domicile_id:
            self.city_domicile_id = False

    @api.onchange('city_domicile_id')
    def _onchange_city_domicile_id(self):
        if not self.city_domicile_id:
            self.district_domicile_id = False
    
    @api.onchange('district_domicile_id')
    def _onchange_district_domicile_id(self):
        if not self.district_domicile_id:
            self.sub_district_domicile_id = False
    
    @api.onchange('payment_type')
    def onchange_payment_type(self):
        self.finco_id = False
        self.down_payment = False
        self.installment = False
        self.tenor = False
        self.due_date = False

    @api.onchange('current_motorcycle')
    def _onchange_current_motorcycle(self):
        """Mirror logic dari tw.lead: auto-set motor brand/type berdasarkan pilihan motor sekarang."""
        self.motor_brand_id = False
        self.motor_type_id = False
        if self.current_motorcycle == 'tidak_ada':
            self.motor_brand_id = self.env.ref('tw_selection.selection_merk_mtr_blm').id
            self.motor_type_id = self.env.ref('tw_selection.selection_jns_mtr_blm').id
        elif self.current_motorcycle == 'ada':
            return

    @api.onchange('motor_brand_id')
    def _onchange_motor_brand_id(self):
        """Mirror logic dari tw.lead: jika brand = 'Belum', ubah current_motorcycle jadi 'tidak_ada'."""
        if self.motor_brand_id.id == self.env.ref('tw_selection.selection_merk_mtr_blm').id:
            if self.current_motorcycle == 'ada':
                self.current_motorcycle = 'tidak_ada'

    @api.onchange('motor_type_id')
    def _onchange_motor_type_id(self):
        """Mirror logic dari tw.lead: jika type = 'Belum', ubah current_motorcycle jadi 'tidak_ada'."""
        if self.motor_type_id.id == self.env.ref('tw_selection.selection_jns_mtr_blm').id:
            if self.current_motorcycle == 'ada':
                self.current_motorcycle = 'tidak_ada'

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'stage_id' in vals:
                stage = self.env['crm.stage'].browse(vals['stage_id'])
                vals['name'] = stage.name

        return super().create(vals_list)
    
    def write(self, vals):
        if vals.get('remark'):
            vals['remark'] = vals['remark'].title()
        if vals.get('activity_result_id') and not vals.get('done_date'):
            vals['followup_state'] = 'completed'
            vals['done_date'] = self._get_default_datetime()
        
        result = super().write(vals)

        # Clear next_activity_id on the parent lead if the result was just set
        if vals.get('activity_result_id'):
            for record in self:
                if record.lead_id and record.lead_id.next_activity_id == record:
                    record.lead_id.next_activity_id = False

        return result

    # 13: action methods
    def action_add_activity(self):
        if self.lead_id.state not in ('open','reject'):
            raise Warning(f'Tidak bisa tambah activity, karena state telah {self.lead_id._get_state_value()}')
        self.ensure_one()
        vals = self._prepare_leads_vals()
        self.lead_id.write(vals)

    def action_add_and_next_activity(self):
        self.ensure_one()
        self.action_add_activity()
        form1_id = self.env.ref('tw_lead_activity.view_tw_lead_activity_first_view_form').id
        return {
            'name': ('Next Activity'),
            'res_model': 'tw.lead.activity',
            'context': {
                'default_lead_id': self.lead_id.id,
            },
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(form1_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'view_type': 'form'
        }
    
    # 14: private methods
    def _prepare_leads_vals(self):
        # Initialize base values
        interest_value = self.interest_id.value if self.interest_id else 'cold'
        
        # Base values that are always included
        lead_obj = self.lead_id
        vals = {
            'next_activity_id': False if self.activity_result_id else self.id,
            'mobile': self._phone_format_number(self.mobile, self.env.company.country_id) if self.mobile else lead_obj.mobile,
            'whatsapp': self._phone_format_number(self.whatsapp, self.env.company.country_id) if self.whatsapp else lead_obj.whatsapp,
            'gender_id': self.gender_id.id if self.gender_id else lead_obj.gender_id.id,
            'activity_result_id': self.activity_result_id.id if self.activity_result_id else lead_obj.activity_result_id.id,
            'remark': self.remark if self.remark else lead_obj.remark,
            'interest_id': self.interest_id.id if self.interest_id else lead_obj.interest_id.id,
        }
            
        # For medium and hot interests, include additional fields
        if interest_value in ['medium', 'hot']:
            vals.update({
                'product_id': self.product_id.id if self.product_id else False,
                'payment_type_id': self.payment_type_id.id if self.payment_type_id else False,
                'payment_type': self.payment_type_id.value if self.payment_type_id else False,
                'unit_usage_id': self.unit_usage_id.id if self.unit_usage_id else lead_obj.unit_usage_id.id,
                'unit_operator_id': self.unit_operator_id.id if self.unit_operator_id else lead_obj.unit_operator_id.id,
                'motor_brand_id': self.motor_brand_id.id if self.motor_brand_id else lead_obj.motor_brand_id.id,
                'motor_type_id': self.motor_type_id.id if self.motor_type_id else lead_obj.motor_type_id.id,
                'current_motorcycle': self.current_motorcycle if self.current_motorcycle else lead_obj.current_motorcycle,
                'motor_ownership_id': self.motor_ownership_id.id if self.motor_ownership_id else lead_obj.motor_ownership_id.id,
                'partner_stnk_id': self.partner_stnk_id.id if self.partner_stnk_id else lead_obj.partner_stnk_id.id,
            })
            personal_info = {
                'identification_number': self.identification_number,
                'identification_family_number': self.identification_family_number,
                'birthplace': self.birthplace,
                'birthdate': self.birthdate,
                'relative_phone_number': self.relative_phone_number,
                'email': self.email,
                'religion_id': self.religion_id.id if self.religion_id else False,
                'education_id': self.education_id.id if self.education_id else False,
                'occupation_id': self.occupation_id.id if self.occupation_id else False,
            }
            # Only add non-empty values
            vals.update({k: v for k, v in personal_info.items() if v is not None and v is not False})

            address_vals = {
                'street': self.street,
                'street2': self.street2,
                'rt': self.rt,
                'rw': self.rw,
                'zip': self.zip,
                'state_id': self.state_id.id if self.state_id else False,
                'city_id': self.city_id.id if self.city_id else False,
                'district_id': self.district_id.id if self.district_id else False,
                'sub_district_id': self.sub_district_id.id if self.sub_district_id else False,
                'country_id': self.country_id.id if self.country_id else False,

                'is_same_ktp': self.is_same_ktp,
                'street_domicile': self.street_domicile,
                'street2_domicile': self.street2_domicile,
                'rt_domicile': self.rt_domicile,
                'rw_domicile': self.rw_domicile,
                'zip_domicile': self.zip_domicile,
                'state_domicile_id': self.state_domicile_id.id if self.state_domicile_id else False,
                'city_domicile_id': self.city_domicile_id.id if self.city_domicile_id else False,
                'district_domicile_id': self.district_domicile_id.id if self.district_domicile_id else False,
                'sub_district_domicile_id': self.sub_district_domicile_id.id if self.sub_district_domicile_id else False,
                'country_domicile_id': self.country_domicile_id.id if self.country_domicile_id else False,
            }

            vals.update({k: v for k, v in address_vals.items() if v is not None and v is not False})
        
        # For hot interests, include financial information
        if interest_value == 'hot':
            financial_info = {
                'current_motorcycle': self.current_motorcycle,
                'down_payment': self.down_payment,
                'down_payment_date': self.down_payment_date,
                'tenor': self.tenor,
                'installment': self.installment,
                'due_date': self.due_date,
                'discount': self.discount,
                'finco_id': self.finco_id.id if self.finco_id else False,
                'product_id': self.product_id.id if self.product_id else False,
                'blood_type_id': self.blood_type_id.id if self.blood_type_id else False,
            }
            # Only add non-empty values
            vals.update({k: v for k, v in financial_info.items() if v is not None and v is not False})
        
        return vals
