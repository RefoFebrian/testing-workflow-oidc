# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command


# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib

class TWPartnerCdb(models.Model):
    _name = "tw.partner.cdb"
    _description = "Partner CDB"
    
    # 7: defaults methods 
    def _default_country_id(self):
        return self.env.user.company_id.country_id

    # 8: fields
    name = fields.Char(string='Name')
    cddb_code = fields.Char(string='CDDB Code')
    identification_number = fields.Char(string='No KTP')
    identification_family_number = fields.Char(string='No KK')
    birthplace = fields.Char(string='Tempat Tanggal Lahir')
    mobile = fields.Char(string='Mobile')
    email = fields.Char(string='Email')
    whatsapp = fields.Char(string='Whatsapp')
    phone = fields.Char(string='No Telp')
    customer_traits = fields.Char(string='Karakter Konsumen')
    responsible = fields.Char(string='Penanggung Jawab')

    street = fields.Char(string='Street')
    street2 = fields.Char(string='Street2')
    rt = fields.Char(string='RT')
    rw = fields.Char(string='RW')
    zip_code = fields.Char(string='Kode Pos')
    rt_domicile = fields.Char(string='RT Domisili')
    rw_domicile = fields.Char(string='RW Domisili')
    street_domicile = fields.Char(string='Street Domisili')
    street2_domicile = fields.Char(string='Street2 Domisili')
    zip_code_domicile = fields.Char(string='Kode Pos Domisili')

    state_text = fields.Char(string="Provinsi (Text)")
    city_text = fields.Char(string="Kota/Kabupaten (Text)")
    district_text = fields.Char(string="Kecamatan (Text)")
    sub_district_text = fields.Char(string="Kelurahan (Text)")

    ethnic_group = fields.Char(string='Suku')
    job_position = fields.Char(string='Jabatan')

    downpayment = fields.Float('Uang Muka')
    installments = fields.Integer('Angsuran')
    tenor = fields.Integer(string="Tenor")
    
    date = fields.Date(string='Tanggal', default=date.today())
    birthdate = fields.Date(string='Tgl Lahir')
    same_address = fields.Boolean('Same Address ?')

    can_contacted = fields.Selection(
        string='Dapat Dihubungi',
        selection=[
            ('yes', 'Ya'),
            ('no', 'Tidak'),
        ],
        required=False
    )
    program = fields.Selection(
        string='Program',
        selection=[
            ('loyalty', 'Loyalty Member Card'),
            ('community', 'Community Program'),
        ],
        required=False
    )

    is_branch = fields.Boolean(string='Branch?', default=False)
    is_customer = fields.Boolean(string='Customer?', default=False)
    is_ro_honda = fields.Boolean(string='RO Honda?', default=False)
    is_ro_dealer = fields.Boolean(string='RO Dealer?', default=False)
    
    # 9: relation fields
    partner_id = fields.Many2one('res.partner', string='Customer', domain=[('category_id.name', '=', 'Customer')])
    company_id = fields.Many2one('res.company', string="Branch")
    employee_id = fields.Many2one('hr.employee', string='Sales', domain=[('company_id', '=', company_id),('working_end_date','=',False)])
    sales_channel_id = fields.Many2one('tw.selection', string='Sales Channel', domain=[('type','=','SalesChannel')])
    payment_type_id = fields.Many2one('tw.selection', string='Payment Type', domain=[('type','=','PaymentType')])
    finco_id = fields.Many2one('res.partner', 'Finance Company', domain=[('category_id.name', '=', 'Finance Company')])
    
     # Address
    country_domicile_id = fields.Many2one('res.country', string='Country Domicile', default=_default_country_id)
    state_domicile_id = fields.Many2one('res.country.state', string='State Domicile', domain="[('country_id', '=', country_domicile_id)]")
    city_domicile_id = fields.Many2one('res.city', string='City Domicile', domain="[('state_id', '=', state_domicile_id)]")
    district_domicile_id = fields.Many2one('res.district', string='District Domicile', domain="[('city_id', '=', city_domicile_id)]")
    sub_district_domicile_id = fields.Many2one('res.sub.district', string='Sub District Domicile', domain="[('district_id', '=', district_domicile_id)]")

    country_id = fields.Many2one('res.country', string='Country', default=_default_country_id)
    state_id = fields.Many2one('res.country.state', string='State', domain="[('country_id', '=', country_id)]")
    city_id = fields.Many2one('res.city', string='City', domain="[('state_id', '=', state_id)]")
    district_id = fields.Many2one('res.district', string='District', domain="[('city_id', '=', city_id)]")
    sub_district_id = fields.Many2one('res.sub.district', string='Sub District', domain="[('district_id', '=', district_id)]")

    gender_id = fields.Many2one('tw.selection', string='Jenis Kelamin' , domain=[('type','=','Gender')])
    religion_id = fields.Many2one('tw.selection', string='Agama' , domain=[('type','=','Religion')])
    education_id = fields.Many2one('tw.selection', string='Pendidikan' , domain=[('type','=','Education')])
    occupation_id = fields.Many2one('tw.selection', string='Pekerjaan' , domain=[('type','=','Occupation')])
    responsible_occupation_id = fields.Many2one('tw.selection', string='Pekerjaan Penanggung Jawab' , domain=[('type','=','Occupation')])
    hobby_id = fields.Many2one('tw.selection', string='Hobi' , domain=[('type','=','Hobby')])
    blood_type_id = fields.Many2one('tw.selection', string='Golongan Darah' , domain=[('type','=','BloodType')])
    
    customer_code_id = fields.Many2one('tw.selection',string='Kode Customer', domain=[('type','=','CustomerCode')])
    customer_type_id = fields.Many2one('tw.selection',string='Jenis Customer', domain=[('type','=','CustomerType')])
    housing_tenure_id = fields.Many2one('tw.selection', string='Status Rumah' , domain=[('type','=','HousingTenure')])
    mobile_plan_status_id = fields.Many2one('tw.selection', string='Status HP' , domain=[('type','=','StatusMobilePhone')])
    expense_id = fields.Many2one('tw.selection',string='Pengeluaran', domain=[('type','=','Expense')])
    motor_brand_id = fields.Many2one('tw.selection',string='Merk Motor', domain=[('type','=','MotorBrand')])
    motor_type_id = fields.Many2one('tw.selection',string='Jenis Motor', domain=[('type','=','MotorType')])

    unit_usage_id = fields.Many2one('tw.selection',string='Penggunaan', domain=[('type','=','MotorUtilization')])
    unit_operator_id = fields.Many2one('tw.selection',string='Pengguna', domain=[('type','=','MotorUser')])
    product_id = fields.Many2one('product.product', string='Product')
    lot_ids = fields.One2many('stock.lot', 'cdb_partner_id', string='Lot')
    
    # 10: constraints & sql constraints
    @api.constrains('birthdate')
    def cek_birth_date(self):
        for record in self:
            if record.birthdate:
                today = fields.Date.today()
                
                if record.birthdate > today:
                    raise ValidationError('birthdate must be less than today')
                
                birthdate = datetime.strptime(record.birthdate.strftime('%Y-%m-%d'), '%Y-%m-%d')
                today = datetime.strptime(today.strftime('%Y-%m-%d'), '%Y-%m-%d')
                age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
                if age < 18:
                    raise ValidationError('Minimum age must be 18 years old.')


    @api.constrains('zip_code', 'zip_code_domicile')
    def _check_zip_format(self):
        for record in self:
            if record.zip_code and not record.zip_code.isdigit():
                raise ValidationError("ZIP code must contain only numbers")
            if record.zip_code_domicile and not record.zip_code_domicile.isdigit():
                raise ValidationError("Domicile ZIP code must contain only numbers")

    # 11: compute/depends & on change methods
    @api.onchange('same_address')
    def _onchange_same_address(self):
        self.street_domicile = False
        self.street2_domicile = False
        self.city_domicile_id = False
        self.state_domicile_id = False
        self.country_domicile_id = False
        self.zip_code_domicile = False
        self.district_domicile_id = False
        self.sub_district_domicile_id = False
        self.rt_domicile = False
        self.rw_domicile = False
        for cdb in self:
            if cdb.same_address:
                cdb.street_domicile = cdb.street
                cdb.street2_domicile = cdb.street2
                cdb.city_domicile_id = cdb.city_id.id
                cdb.state_domicile_id = cdb.state_id.id
                cdb.country_domicile_id = cdb.country_id.id
                cdb.district_domicile_id = cdb.district_id.id
                cdb.sub_district_domicile_id = cdb.sub_district_id.id
                cdb.zip_code_domicile = cdb.zip_code
                cdb.rt_domicile = cdb.rt
                cdb.rw_domicile = cdb.rw

    @api.onchange('sub_district_domicile_id')
    def _onchange_sub_district_domicile(self):
        self.zip_code_domicile = False
        if self.sub_district_domicile_id:
            self.zip_code_domicile = self.sub_district_domicile_id.zip_code
    
    @api.onchange('rt', 'rw', 'street', 'street2','zip_code')
    def _onchange_rt(self):
        self._onchange_same_address()
    
    @api.onchange('state_id')
    def _onchange_state_id(self):
        self.city_id = False
        if self.state_id and self.same_address:
            self._onchange_same_address()

    @api.onchange('state_id')
    def _onchange_state_text(self):
        if self.state_id:
            self.state_text = self.state_id.name
        else:
            self.state_text = False
        
    @api.onchange('city_id')
    def _onchange_city_id(self):
        self.district_id = False
        if self.city_id and self.same_address:
            self._onchange_same_address()

    @api.onchange('city_id')
    def _onchange_city_text(self):
        if self.city_id:
            self.city_text = self.city_id.name
        else:
            self.city_text = False
    
    @api.onchange('district_id')
    def _onchange_district_id(self):
        self.sub_district_id = False
        if self.district_id and self.same_address:
            self._onchange_same_address()

    @api.onchange('district_id')
    def _onchange_district_text(self):
        if self.district_id:
            self.district_text = self.district_id.name
        else:
            self.district_text = False

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

    
    @api.onchange('sub_district_id')
    def _onchange_sub_district_id(self):
        self.zip_code = False
        for address in self:
            if address.sub_district_id:
                address.zip_code = address.sub_district_id.zip_code
                if address.same_address:
                    self._onchange_same_address()

    @api.onchange('sub_district_id')
    def _onchange_sub_district_text(self):
        if self.sub_district_id:
            self.sub_district_text = self.sub_district_id.name
        else:
            self.sub_district_text = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' in vals and 'partner_id' in vals:
                vals['cddb_code'] = self._generate_cddb_code(
                    vals['name'],
                    vals['partner_id']
                )
            
            if 'customer_code_id' in vals:
                customer_code_id = self.env['tw.selection'].search([('id', '=', vals.get('customer_code_id'))])
                if customer_code_id.value in ('I', 'C'):
                    vals['responsible'] = 'N'
        
        return super(TWPartnerCdb, self).create(vals_list)

    # 13: action methods

    # 14: private methods

    def _generate_cddb_code(self, name, customer_id):
        base_code = name.replace(' ', '')[:10].upper()
        
        existing_codes = self.search([
            ('partner_id', '=', customer_id),
            ('cddb_code', '!=', False)
        ]).mapped('cddb_code')

        if not existing_codes:
            return f"{base_code}001"

        code_numbers = []
        for code in existing_codes:
            if code and code.startswith(base_code) and code[len(base_code):].isdigit():
                code_numbers.append(int(code.split(base_code)[1]))
        
        if not code_numbers:
            return f"{base_code}001"
        
        next_number = max(code_numbers) + 1
        return f"{base_code}{next_number:03d}"