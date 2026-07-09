# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime
from optparse import Values
import re

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib


LEAD_STATE = [
    ('open', 'Open'),
    ('dealt', 'Dealt'),
    ('proposed', 'Proposed'),
    ('receipt', 'Receipt'),
    ('approved', 'Approved'),
    ('spk', 'SPK'),
    ('cancel', 'Cancel')
]

class Leads(models.Model):
    _name = "tw.lead"
    _inherit = "crm.lead"
    _description = "Leads"

    # 7: defaults methods
    def _get_default_branch(self):
        company_ids = self.env.companies
        return company_ids[0].id if company_ids and len(company_ids) == 1 else False

    def _get_default_sales(self):
        sales_force = self.env.user.employee_id.job_id.sales_force_id
        if sales_force.value in ('salesman', 'sales_counter', 'sales_partner', 'sales_coordinator', 'sales_operation_head'):
            return self.env.user.employee_id.id
        elif self.env.user.employee_id.coach_id:
            return self.env.user.employee_id.id
        else:
            return False
    
    def _get_default_interest(self):
        try:
            return self.env.ref('tw_lead.tw_lead_interest_cold').id
        except ValueError:
            return False

    def _get_default_date(self): 
        return date.today()

    def _get_default_datetime(self):
        return datetime.now()

    def _get_default_data_source(self):
        data_source = self.env['tw.selection'].search([
            ('type', '=', 'DataSource'),
            ('value', '=', 'web')
        ], limit=1)
        return data_source.id

    def _get_default_country(self):
        return self.env.ref('base.id').id
    
    def _get_state_value(self):
        # Mengambil value yang sesuai dengan key di state
        selection = self._fields.get('state') and self._fields['state'].selection
        return dict(selection).get(self.state, self.state) if selection else self.state
    
    # 8: fields
    name = fields.Char('No. Buku Tamu', index='trigram', required=False, compute='_compute_name', store=True)
    customer_name = fields.Char()
    date = fields.Date(default=_get_default_date, help="Date of the lead creation")
    identification_number = fields.Char()
    identification_family_number = fields.Char()
    birthplace = fields.Char(string='Tempat Lahir', help="Customer's place of birth")
    birthdate = fields.Date(string='Tanggal Lahir', help="Customer's date of birth")
    ethnicity = fields.Char(string='Ethnis', help="Ethnicity of the customer prospect")
    position = fields.Char(string='Posisi', help="Customer's position in their company or job")
    
    state = fields.Selection(selection=LEAD_STATE, string='Status', default='open')
    note = fields.Text(string='Note/Reason')
    data_by = fields.Selection([
        ('lead', 'Buku Tamu'),
        ('crm', 'CRM'),
        ('activity_after_dealing', 'Activity After Dealing')],
        string='Data By', default='lead',
        help="The source of data for this record")
    type = fields.Selection([
        ('lead', 'Lead'),
        ('opportunity', 'Opportunity')],
        string='Type', default='lead')
    current_motorcycle = fields.Selection([
        ('ada', 'Ada'),
        ('tidak_ada', 'Tidak Ada')], string='Motor Sekarang', help="Currently owned motorcycle"
    )

    # related fields that used for attributes
    payment_type = fields.Char(string='Payment Type')
    unit_availability = fields.Char(string='Unit Availability')
    motor_ownership = fields.Char(string='Motor Ownership')
    interest = fields.Char(string='Interest', compute='_compute_interest', store=True)
    
    # credit composition
    down_payment = fields.Float(string='Uang Muka', help="Enter the amount of down payment")
    down_payment_date = fields.Date(string='Tanggal Uang Muka', default=_get_default_date, help="Date when the down payment is made")
    tenor = fields.Integer(string='Tenor', help="Enter the number of months for the loan tenure")
    installment = fields.Float(string='Angsuran', help="Enter the monthly installment amount")
    due_date = fields.Date(string='Tanggal Jatuh Tempo')
    last_state_date = fields.Date(string='Last State Date', help="Latest date of the state change!")
    last_state = fields.Selection(selection=LEAD_STATE)

    # payments field
    price_otr = fields.Float(string='OTR', compute='_compute_price_otr', store=True, readonly=False, help="(On The Road) the vehicle price inclusive of all additional costs")
    discount = fields.Float(string='Diskon')

    # finance company documents
    finco_po = fields.Char(help="Purchase Order number from the finance company")
    finco_pic = fields.Char(help="Person in charge at the finance company")
    finco_identify = fields.Char(help="Identification details of the finance company")
    finco_po_create = fields.Char(help="Date when the finance company PO was created")
    finco_po_sent = fields.Char(help="Date when the finance company PO was sent")
    finco_submission_id = fields.Char(string='Finco Submission', help="Finance Company Submission document's name")
    rejection_reason = fields.Char( string="Rejection Reason", help="Rejection reason for customer Proposal")

    # social media account & additional contact
    is_same_with_mobile = fields.Boolean('is_same_with_mobile', help="Is mobile number is whatsapp number")
    email = fields.Char(string="E-mail")
    whatsapp = fields.Char(string="Whatsapp")
    facebook = fields.Char(string="Facebook")
    youtube = fields.Char(string="Youtube")
    tiktok = fields.Char(string="Tiktok")
    instagram = fields.Char(string="Instagram")
    twitter = fields.Char(string="Twitter / X")
    relative_phone_number = fields.Char(string="Relative Phone Number")

    # Addresses
    rt = fields.Char('RT')
    rw = fields.Char('RW')
    street = fields.Char('Street', compute=False)
    street2 = fields.Char('Street2', compute=False)
    zip = fields.Char('Zip', compute=False)
    
    is_same_ktp = fields.Boolean('Sesuai dengan KTP?', help="Is domicile address same with KTP")
    rt_domicile = fields.Char('RT Domisili')
    rw_domicile = fields.Char('RW Domisili')
    street_domicile = fields.Char('Street Domisili')
    street2_domicile = fields.Char('Street2 Domisili')
    zip_domicile = fields.Char('Zip Domisili')

    # Doodool Apps
    data_source_char = fields.Char(compute='_compute_data_source_char', store=True)
    version_code = fields.Char('version Code')
    version_name = fields.Char('version Name')
    version_display = fields.Char(string="Version", compute="_compute_version_display")

    # 9: relation fields
    # Addresses
    country_id = fields.Many2one('res.country', string="Negara", default=_get_default_country) 
    state_id = fields.Many2one('res.country.state', string="Provinsi", domain="[('country_id', '=?', country_id)]")
    city_id = fields.Many2one(comodel_name='res.city', string="Kabupaten", domain="[('state_id', '=', state_id)]", help='')
    district_id = fields.Many2one(comodel_name='res.district', string="Kecamatan", domain="[('city_id', '=', city_id)]", help='')
    sub_district_id = fields.Many2one(comodel_name='res.sub.district', string="Kelurahan", domain="[('district_id', '=', district_id)]", help='')
        
    country_domicile_id = fields.Many2one('res.country', string="Negara Domisili", default=_get_default_country ) 
    state_domicile_id = fields.Many2one('res.country.state', string="Provinsi Domisili", domain="[('country_id', '=?', country_domicile_id)]")
    city_domicile_id = fields.Many2one(comodel_name='res.city', string="Kabupaten Domisili", domain="[('state_id', '=', state_domicile_id)]", help='')
    district_domicile_id = fields.Many2one(comodel_name='res.district', string="Kecamatan Domisili", domain="[('city_id', '=', city_domicile_id)]", help='')
    sub_district_domicile_id = fields.Many2one(comodel_name='res.sub.district', string="Kelurahan Domisili", domain="[('district_id', '=', district_domicile_id)]", help='')

    company_id = fields.Many2one(comodel_name='res.company', string="Branch", domain="[('parent_id', '!=', False)]")
    md_id = fields.Many2one(comodel_name='res.company', related='company_id.parent_id')
    payment_type_id = fields.Many2one(comodel_name='tw.selection', string='Tipe Pembayaran', domain="[('type', '=', 'PaymentType')]")
    interest_id = fields.Many2one(comodel_name='tw.selection', string='Minat', domain="[('type', '=', 'Interest')]", default=_get_default_interest)
    gender_id = fields.Many2one(comodel_name='tw.selection', string='Jenis Kelamin', domain="[('type', '=', 'Gender')]")
    blood_type_id = fields.Many2one(comodel_name='tw.selection', string='Golongan Darah', domain="[('type', '=', 'BloodType')]")
    religion_id = fields.Many2one(comodel_name='tw.selection', string='Agama', domain="[('type', '=', 'Religion')]")
    education_id = fields.Many2one(comodel_name='tw.selection', string='Pendidikan', domain="[('type', '=', 'Education')]")
    occupation_id = fields.Many2one(comodel_name='tw.selection', string='Pekerjaan', domain="[('type', '=', 'Occupation')]")
    hobby_id = fields.Many2one(comodel_name='tw.selection' , string='Hobby', domain=[('type', '=', 'Hobby')])
    unit_usage_id = fields.Many2one(comodel_name='tw.selection' , string='Penggunaan Motor', domain=[('type', '=', 'MotorUtilization')])
    unit_operator_id = fields.Many2one(comodel_name='tw.selection' , string='Pengguna Motor', domain=[('type', '=', 'MotorUser')])
    expense_id = fields.Many2one(comodel_name='tw.selection' , string='Pengeluaran', domain=[('type', '=', 'Expense')])
    income_id = fields.Many2one(comodel_name='tw.selection' , string='Pemasukan', domain=[('type', '=', 'Income')])
    motor_brand_id = fields.Many2one(comodel_name='tw.selection' , string='Merk Motor Sekarang', domain=[('type', '=', 'MotorBrand')])
    motor_type_id = fields.Many2one(comodel_name='tw.selection' , string='Type Motor Sekarang', domain=[('type', '=', 'MotorType')])
    mobile_plan_status_id = fields.Many2one(comodel_name='tw.selection', string='Status Paket Data', domain=[('type', '=', 'StatusMobilePhone')])
    housing_tenure_id = fields.Many2one(comodel_name='tw.selection', string='Kepemilikan Rumah', domain=[('type', '=', 'HousingTenure')])
    marital_status_id = fields.Many2one(comodel_name='tw.selection', string='Status Pernikahan', domain=[('type', '=', 'MaritalStatus')])
    customer_grade_id = fields.Many2one(comodel_name='tw.selection', string='Grade', domain=[('type', '=', 'CustomerGrade')])
    data_source_id = fields.Many2one(comodel_name='tw.selection', string='Sumber Data', domain=[('type', '=', 'DataSource')], default=_get_default_data_source)

    product_id = fields.Many2one(comodel_name='product.product', string='Product', domain="[('sale_ok','=',True), ('categ_id', 'in', product_category_ids)]")
    sales_id = fields.Many2one(comodel_name='hr.employee', string='Sales Person', 
                               domain="[('company_id', '=', company_id),('job_id.sales_force_id.value', 'in', ('salesman', 'sales_counter', 'sales_partner', 'sales_coordinator', 'sales_operation_head'))]", default=_get_default_sales)
    sales_coordinator_id = fields.Many2one(comodel_name='hr.employee', string='Sales Coordinator',
                                           compute='_compute_sales_coordinator_id', store=True,
                                           domain="[('company_id', '=', company_id), ('job_id.sales_force_id.value', '=', 'sales_coordinator')]")
    
    source_location_id = fields.Many2one('stock.location', string="Source Location", domain="[('company_id', '=', company_id)]")
    finco_id = fields.Many2one(comodel_name='res.partner', string='Finco', domain="[('category_id.name', '=', 'Finance Company')]", help='')
    unit_availability_id = fields.Many2one(comodel_name='tw.selection', string="Ketersediaan Unit",
                                           compute='_compute_unit_availability', domain="[('type', '=', 'UnitAvailability')]",store=True)
    motor_ownership_id = fields.Many2one(comodel_name='tw.selection', string="Kepemilikan Motor", domain="[('type', '=', 'MotorOwnership')]")
    partner_stnk_id = fields.Many2one(comodel_name='res.partner', string='Customer STNK', check_company=True, tracking=10, help="")
    
    address_ids = fields.One2many(
        comodel_name='tw.lead.addresses', inverse_name='lead_id',
        string='Addresses List', help="To record addresses owned by customer")
    document_ids = fields.One2many(
        comodel_name='tw.lead.documents', inverse_name='lead_id',
        string='Documents', help="All related documents for Lead")
    log_ids = fields.One2many(
        comodel_name='tw.lead.logs', inverse_name='lead_id',
        string='Logs', help="To record all logs related to this lead")
    product_category_ids = fields.Many2many(
        comodel_name='product.category',
        relation='tw_lead_prod_categ_rel', column1='lead_id', column2='product_category_id',
        default=lambda self: self.env['product.category'].get_child_ids('Unit'),
        string="Product Category")
    tag_ids = fields.Many2many(
        comodel_name='crm.tag',
        relation='tw_lead_tag_rel', column1='lead_id', column2='tag_id',
        string="Tags")
    

    # audit trails
    deal_uid = fields.Many2one(comodel_name='res.users', string='Dealt by')
    deal_date = fields.Datetime(string='Dealt on')
    propose_uid = fields.Many2one(comodel_name='res.users', string='Proposed by')
    propose_date = fields.Datetime(string='Proposed on')
    receipt_uid = fields.Many2one(comodel_name='res.users', string='Received by')
    receipt_date = fields.Datetime(string='Received on')
    approve_uid = fields.Many2one(comodel_name='res.users', string='Approved by')
    approve_date = fields.Datetime(string='Approved on')
    reject_uid = fields.Many2one(comodel_name='res.users', string='Rejected by')
    reject_date = fields.Datetime(string='Rejected on')

    # 10: constraints & sql constraints
    @api.constrains('identification_number')
    def _validate_identification_number(self):
        for record in self:
            id = record.identification_number
            if record.interest_id.value != 'cold':
                if not (id and id.isdigit() and len(id) == 16 and not id.startswith('0')):
                    raise ValidationError(_("Nomor KTP harus terdiri dari 16 digit, "
                                            "hanya boleh mengandung angka, dan tidak boleh diawali dengan angka 0."))

    @api.constrains('identification_family_number')
    def _validate_identification_family_number(self):
        for record in self:
            id = record.identification_number
            family_id = record.identification_family_number
            if family_id and family_id == id:
                raise ValidationError(_("Nomor KK tidak boleh sama dengan nomor KTP."))
            
    @api.constrains('birthdate')
    def _validate_birthdate(self):
        for record in self:
            if record.birthdate:
                today = date.today()
                age = today.year - record.birthdate.year - ((today.month, today.day) < (record.birthdate.month, record.birthdate.day))
                if age < 17:
                    raise ValidationError(_("Customer belum cukup umur dan tidak dapat diproses sebagai prospek."))

    @api.constrains('phone', 'mobile', 'whatsapp')
    def _validate_phone_number(self):
        for record in self:
            for field, label in [('phone', 'Telepon'), ('mobile', 'Mobile'), ('whatsapp', 'WhatsApp')]:
                val = record[field]
                if val:
                    if not re.match(r'^[0-9\s.+\-()]+$', val):
                        raise Warning(f"Nomor {label} hanya boleh berisi angka dan karakter format (+, -, space, dll).")
                    num_digits = len(re.sub(r'\D', '', val))
                    if not (10 <= num_digits <= 13):
                        raise Warning(f"Nomor {label} harus memiliki panjang antara 10 dan 13 digit.")

    @api.constrains('email')
    def _validate_email(self):
        for record in self:
            if record.email:
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', record.email):
                    raise Warning("Email tidak valid.")

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

    @api.constrains('down_payment_date')
    def _validate_dp_date(self):
        for record in self:
            if record.down_payment_date and record.down_payment_date < date.today():
                raise Warning("Tanggal Uang Muka tidak boleh lewat dari hari ini.")

    @api.constrains('down_payment', 'discount', 'tenor', 'installment', 'payment_type_id', 'price_otr')
    def _validate_financials(self):
        for record in self:
            if record.down_payment < 0:
                raise Warning("Uang Muka tidak boleh negatif.")
            if record.discount < 0:
                raise Warning("Discount tidak boleh negatif.")
            if record.payment_type_id.value == 'Credit':
                if len(str(record.tenor)) > 2:
                    raise Warning("Tenor tidak boleh lebih dari 2 digit.")
                if record.tenor <= 0:
                    raise Warning("Tenor harus lebih besar dari 0 untuk pembayaran Kredit.")
                if record.installment <= 0:
                    raise Warning("Cicilan harus lebih besar dari 0 untuk pembayaran Kredit.")
                if record.down_payment > record.price_otr:
                    raise Warning("Uang Muka tidak boleh melebihi nilai OTR untuk pembayaran Kredit.")

    # 11: compute/depends & on change methods
    @api.depends('interest_id')
    def _compute_interest(self):
        for lead in self:
            lead.interest = lead.interest_id.value

    @api.depends('company_id')
    def _compute_name(self):
        for lead in self:
            if lead.id and not lead.name:
                code = 'LEADS'
                prefix = lead.company_id.code
                lead.name = lead.env['ir.sequence'].get_sequence_code(code, prefix)

    @api.depends('data_source_id')
    def _compute_data_source_char(self):
        for lead in self:
            lead.data_source_char = lead.data_source_id.value

    @api.depends("version_code", "version_name", "data_source_char")
    def _compute_version_display(self):
        for rec in self:
            if rec.data_source_char == "apps":
                rec.version_display = f"- {rec.version_code or ''} {rec.version_name or ''}".strip()
            else:
                rec.version_display = False

    @api.depends('partner_id')
    def _compute_partner_address_values(self):
        """ Sync all or none of address fields """
        for lead in self:
            lead = super()._compute_partner_address_values()
            if lead:
                lead.clear()

    @api.depends('sales_id')
    def _compute_sales_coordinator_id(self):
        for order in self:
            if order.sales_id:
                if order.sales_id.job_id.sales_force_id.value in ('sales_coordinator', 'sales_operation_head'):
                    order.sales_coordinator_id = order.sales_id.id
                else:
                    if not order.sales_id.coach_id:
                        raise Warning(_(f"Salesman {order.sales_id.name} tidak memiliki Coach / Coordinator!"))
                    order.sales_coordinator_id = order.sales_id.coach_id.id
    
    @api.depends('company_id', 'product_id')
    def _compute_unit_availability(self):
        for order in self:
            if order.product_id and order.company_id:
                ready_id = order.env.ref('tw_lead.tw_lead_unit_availibility_ready').id
                indent_id = order.env.ref('tw_lead.tw_lead_unit_availibility_indent').id
                quantity = order.env['stock.quant'].get_stock_available(order.product_id.id, order.company_id.id)
                order.unit_availability_id = ready_id if quantity > 0 else indent_id
            else:
                order.unit_availability_id = False

    @api.depends('product_id', 'company_id')
    def _compute_price_otr(self):
        for lead in self:
            if lead.product_id and lead.company_id:
                lead.price_otr = lead._get_on_the_road_price()
            elif not lead.product_id:
                lead.price_otr = 0.0

    @api.onchange('interest_id', 'payment_type_id', 'unit_availability_id', 'motor_ownership_id')
    def _onchange_field_attribute(self):
        for lead in self:
            lead.down_payment_date = date.today()
            lead.payment_type = lead.payment_type_id.value
            lead.unit_availability = lead.unit_availability_id.value
            lead.motor_ownership = lead.motor_ownership_id.value
    
    @api.onchange('is_same_with_mobile')
    def _onchange_is_same_with_mobile(self):
        if self.is_same_with_mobile:
            self.whatsapp = self.mobile
        else:
            self.whatsapp = False
            
    @api.onchange('mobile')
    def _onchange_mobile_is_same_with_mobile(self):
        if self.is_same_with_mobile:
            self.whatsapp = self.mobile

    @api.onchange('whatsapp')
    def _onchange_whatsapp_validation(self):
        if self.whatsapp:
            self.whatsapp = self._phone_format(fname='whatsapp', force_format='INTERNATIONAL') or self.whatsapp
            num_digits = len(re.sub(r'\D', '', self.whatsapp))
            if not (10 <= num_digits <= 13):
                raise Warning("Nomor WhatsApp harus memiliki panjang antara 10 dan 13 digit.")

    @api.onchange('phone', 'mobile', 'whatsapp')
    def _onchange_valid_phone_number(self):
        for field, label in [('phone', 'Telepon'), ('mobile', 'Mobile'), ('whatsapp', 'WhatsApp')]:
            val = self[field]
            if val:
                if not re.match(r'^[0-9\s.+\-()]+$', val):
                    raise Warning(f"Nomor {label} hanya boleh berisi angka dan karakter format (+, -, space, dll).")
                num_digits = len(re.sub(r'\D', '', val))
                if not (10 <= num_digits <= 13):
                    raise Warning(f"Nomor {label} harus memiliki panjang antara 10 dan 13 digit.")

    @api.onchange('email')
    def _onchange_valid_email(self):
        for record in self:
            if record.email:
                if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', record.email):
                    raise Warning("Email tidak valid.")

    @api.onchange('is_same_ktp')
    def _onchange_is_same_ktp(self):
        if self.is_same_ktp:
            self.street_domicile = self.street
            self.street2_domicile = self.street2
            self.rt_domicile = self.rt
            self.rw_domicile = self.rw
            self.state_domicile_id = self.state_id.id
            self.city_domicile_id = self.city_id.id
            self.district_domicile_id = self.district_id.id
            self.sub_district_domicile_id = self.sub_district_id.id
            self.zip_domicile = self.zip
            self.country_domicile_id = self.country_id.id

    @api.onchange('street', 'street2', 'rt', 'rw')
    def _onchange_address_ktp(self):
        if self.is_same_ktp:
            self.street_domicile = self.street
            self.street2_domicile = self.street2
            self.rt_domicile = self.rt
            self.rw_domicile = self.rw

    @api.onchange('state_id')
    def _onchange_state_id(self):
        self.city_id = False
        self.district_id = False
        self.sub_district_id = False
        self.zip = False
        if self.is_same_ktp:
            self.state_domicile_id = self.state_id
            self.city_domicile_id = False
            self.district_domicile_id = False
            self.sub_district_domicile_id = False
            self.zip_domicile = False

    @api.onchange('city_id')
    def _onchange_city_id(self):
        self.district_id = False
        self.sub_district_id = False
        self.zip = False
        if self.is_same_ktp:
            self.city_domicile_id = self.city_id
            self.district_domicile_id = False
            self.sub_district_domicile_id = False
            self.zip_domicile = False
    
    @api.onchange('district_id')
    def _onchange_district_id(self):
        self.sub_district_id = False
        self.zip = False
        if self.is_same_ktp:
            self.district_domicile_id = self.district_id
            self.sub_district_domicile_id = False
            self.zip_domicile = False

    @api.onchange('sub_district_id')
    def _onchange_sub_district(self):
        if self.sub_district_id:
            self.zip = self.sub_district_id.zip_code
            if self.is_same_ktp:
                self.sub_district_domicile_id = self.sub_district_id
                self.zip_domicile = self.zip
    
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
            self.zip_domicile = False

    @api.onchange('identification_number')
    def _onchange_identification_number(self):
        if self.identification_number:
            partner = self.env['res.partner'].search([
                ('identification_number', '=', self.identification_number)
                ], limit=1, order='id DESC')
            if partner:
                values = {
                    'customer_name': partner.name,
                    'identification_family_number': partner.identification_family_number,
                    'birthplace': partner.birthplace,
                    'birthdate': partner.birthdate,
                    'phone': partner.phone,
                    'mobile': partner.mobile,
                    'whatsapp': partner.whatsapp,
                    'is_same_with_mobile': partner.mobile == partner.whatsapp,
                    'email': partner.email,
                    'gender_id': partner.gender_id.id,
                    'blood_type_id': partner.blood_type_id.id,
                    'hobby_id': partner.hobby_id.id,
                    'religion_id': partner.religion_id.id,
                    'education_id': partner.education_id.id,
                    'occupation_id': partner.occupation_id.id,
                    'unit_usage_id': partner.unit_usage_id.id,
                    'unit_operator_id': partner.unit_operator_id.id,
                    'expense_id': partner.expense_id.id,
                    'motor_brand_id': partner.motor_brand_id.id,
                    'motor_type_id': partner.motor_type_id.id,
                    'mobile_plan_status_id': partner.mobile_plan_status_id.id,
                    'housing_tenure_id': partner.housing_tenure_id.id,
                    'facebook': partner.facebook,
                    'youtube': partner.youtube,
                    'instagram': partner.instagram,
                    'twitter': partner.twitter,
                    'is_same_ktp': partner.same_address,
                }
                
                # Add address fields
                address_fields = {
                    'street': partner.street,
                    'street2': partner.street2,
                    'rt': partner.rt,
                    'rw': partner.rw,
                    'state_id': partner.state_id.id,
                    'city_id': partner.city_id.id,
                    'district_id': partner.district_id.id,
                    'sub_district_id': partner.sub_district_id.id,
                    'zip': partner.zip,
                    'country_id': partner.country_id.id,
                    'street_domicile': partner.street_domicile,
                    'street2_domicile': partner.street2_domicile,
                    'rt_domicile': partner.rt_domicile,
                    'rw_domicile': partner.rw_domicile,
                    'state_domicile_id': partner.state_domicile_id.id,
                    'city_domicile_id': partner.city_domicile_id.id,
                    'district_domicile_id': partner.district_domicile_id.id,
                    'sub_district_domicile_id': partner.sub_district_domicile_id.id,
                    'zip_domicile': partner.zip_domicile,
                    'country_domicile_id': partner.country_domicile_id.id,
                }

                # Update all fields at once
                values.update(address_fields)
                
                # Update self with all values
                for field, value in values.items():
                    setattr(self, field, value)

    @api.onchange('identification_family_number')
    def _onchange_identification_family_number(self):
        for record in self:
            id = record.identification_number
            family_id = record.identification_family_number
            if family_id and family_id == id:
                raise Warning("Nomor KK tidak boleh sama dengan nomor KTP.")

    @api.onchange('sales_id')
    def _onchange_sales_id(self):
        if not self.sales_id:
            self.sales_coordinator_id = False

    @api.onchange('payment_type_id')
    def _onchange_payment_type_id(self):
        self.finco_id = False
        self.down_payment = False
        self.down_payment_date = False
        self.tenor = False
        self.installment = False

    @api.onchange('current_motorcycle')
    def _onchange_current_motorcycle(self):
        self.motor_brand_id = False
        self.motor_type_id = False
        if self.current_motorcycle == 'tidak_ada':
            self.motor_brand_id = self.env.ref('tw_selection.selection_merk_mtr_blm').id
            self.motor_type_id = self.env.ref('tw_selection.selection_jns_mtr_blm').id
        elif self.current_motorcycle == 'ada':
            return

    @api.onchange('motor_brand_id')
    def _onchange_motor_brand_id(self):
        if self.motor_brand_id.id == self.env.ref('tw_selection.selection_merk_mtr_blm').id:
            if self.current_motorcycle == 'ada':
                self.current_motorcycle = 'tidak_ada'

    @api.onchange('motor_type_id')
    def _onchange_motor_type_id(self):
        if self.motor_type_id.id == self.env.ref('tw_selection.selection_jns_mtr_blm').id:
            if self.current_motorcycle == 'ada':
                self.current_motorcycle = 'tidak_ada'

    @api.onchange('motor_ownership_id')
    def _onchange_motor_ownership_id(self):
        self.partner_stnk_id = False
        if self.motor_ownership_id.value == 'self':
            self.partner_stnk_id = self.partner_id.id
        else:
            self.partner_stnk_id = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('mobile'):
                mobile = vals['mobile']
                if mobile.startswith('0'):
                    vals['mobile'] = '+62' + mobile[1:]

            if vals.get('whatsapp'):
                whatsapp = vals['whatsapp']
                if whatsapp.startswith('0'):
                    vals['whatsapp'] = '+62' + whatsapp[1:]

            self._sync_addresses(vals)
            if vals.get('identification_number'):
                partner_id = self._get_or_create_partner_by_id(vals['identification_number'], vals)
                vals['partner_id'] = partner_id.id

            identification_number = vals.get('identification_number', self.identification_number)
            if identification_number:
                cek_duplikat = self.get_lead_by_identification_number(identification_number)
                if cek_duplikat:
                    raise Warning(f"Buku Tamu dengan no ktp {str(identification_number)} sudah terbuat.\nNo Buku Tamu : {cek_duplikat.name}")

        return super().create(vals_list)
    
    def write(self, vals):
        address_fields = {
            'rt', 'rw', 'street', 'street2', 'zip', 'is_same_ktp',
            'rt_domicile', 'rw_domicile', 'street_domicile', 'street2_domicile', 'zip_domicile',
            'country_id', 'state_id', 'city_id', 'district_id', 'sub_district_id',
            'country_domicile_id', 'state_domicile_id', 'city_domicile_id',
            'district_domicile_id', 'sub_district_domicile_id'
        }
        # Only process partner creation/update if we have an identification number
        identification_number = vals.get('identification_number', self.identification_number)
        if vals.get('mobile'):
            mobile = vals.get('mobile')
            if mobile.startswith('0'):
                vals['mobile'] = '+62' + mobile[1:]

        if vals.get('whatsapp'):
            whatsapp = vals.get('whatsapp')
            if whatsapp.startswith('0'):
                vals['whatsapp'] = '+62' + whatsapp[1:]
                
        # Only sync addresses if any address-related fields are being updated
        if any(field in vals for field in address_fields):
            self._sync_addresses(vals)

        # If we're dealing with a dealt state or have an identification number
        if vals.get('state') == 'dealt' or identification_number:
            # Ensure we have a name for partner creation/update
            if 'name' not in vals and not self.name:
                raise ValidationError(("Nama dibutuhkan untuk pembuatan/pembaruan data customer"))
                
            # Get or create partner if we have an identification number
            if identification_number:
                partner = self._get_or_create_partner_by_id(identification_number, vals)
                if partner:
                    vals['partner_id'] = partner.id

                    if vals.get('motor_ownership_id'):
                        motor_ownership_id = self.env['tw.selection'].browse(vals['motor_ownership_id'])
                        if motor_ownership_id.value == 'self':
                            vals['partner_stnk_id'] = partner.id

            # Handle case where we're in dealt state but no identification number
            elif vals.get('state') == 'dealt':
                raise ValidationError(("Identification number is required when marking as dealt"))
        
        # Update related customer information
        write = super().write(vals)
        self._update_related_customer(vals)
        return write
    
    def unlink(self):
        raise Warning(_("You cannot delete this lead"))
        
    # 13: action methods
    def action_update_otr(self):
        if self.state not in ('proposed','dealt'):
            raise ValidationError(f'Gagal update OTR karena sudah {self._get_state_value()} .\n Update OTR hanya pada saat Dealt atau Proposed')
        price_otr = self._get_on_the_road_price()
        if not price_otr or price_otr <= 0:
            raise Warning(_("On The Road price tidak tersedia!\n"
                            "Silahkan konfigurasi pricelist settings atau "
                            "branch settings di menu Master"))
        self.price_otr = price_otr

    def action_show_deal_form(self):
        self.ensure_one()
        total = False
        if self.product_id:
            total = self._get_on_the_road_price()
            self.price_otr = total
            
        return {
            'name': ('Deal'),
            'res_model': 'tw.lead', 
            'type': 'ir.actions.act_window', 
            'view_id': False,
            'views': [(self.env.ref('tw_lead.view_tw_lead_deal_form').id, 'form')],
            'view_mode': 'form', 
            'target': 'new', 
            'view_type': 'form',
            'res_id': self.id,
        }

    def action_deal(self):
        if self.state != 'open':
            raise ValidationError(f'Silakan refresh halaman ini, karena state sudah {self._get_state_value()}')
        identification_number = self.identification_number
        self.write({
            'state': 'dealt',
            'identification_number': identification_number,
            'interest_id': self.env.ref('tw_lead.tw_lead_interest_hot').id, 
            'deal_uid': self._uid,
            'deal_date': self._get_default_date(),
            'log_ids': [Command.create({
                'name': 'Dealing prospect data',
                'date': datetime.now(),
                'category_id': self.env.ref('tw_lead.tw_lead_log_category_type_general').id
            })]
        })
        return True
    
    def action_show_propose_form(self):
        form_id = self.env.ref('tw_lead.view_tw_lead_propose_form').id
        return {
            'name': ('Proposed'),
            'res_model': 'tw.lead', 
            'type': 'ir.actions.act_window', 
            'view_id': False,
            'views': [(form_id, 'form')],
            'view_mode': 'form', 
            'target': 'new', 
            'view_type': 'form', 
            'res_id': self.id,
        }
    
    def action_propose(self):
        if self.state != 'dealt':
            raise ValidationError(f'Silakan refresh halaman ini, karena state sudah {self._get_state_value()}')
        
        # Validate required documents (KTP and KK) before proposing
        doc_types = self.document_ids.mapped('document_type_id.value')
        missing_docs = []
        if 'ktp' not in doc_types:
            missing_docs.append('KTP')
        if 'kk' not in doc_types:
            missing_docs.append('KK')
        if missing_docs:
            raise ValidationError(
                _("Dokumen %s harus diunggah sebelum Lead dapat diubah menjadi Proposed.") % " dan ".join(missing_docs)
            )

        vals = {
            'propose_uid': self._uid,
            'propose_date': self._get_default_date(),
            'log_ids': [Command.create({
                'name': 'Proposed',
                'date': datetime.now(),
                'category_id': self.env.ref('tw_lead.tw_lead_log_category_type_general').id,
            })]
        }
        if self.motor_ownership == 'other':
            if (
                not self.partner_stnk_id.identification_number
                or not self.partner_stnk_id.occupation_id
                or not self.partner_stnk_id.street
            ):
                raise Warning(_("STNK customer data is incomplete!\n"
                                "Please edit and complete the data."))

        if int(self.price_otr) <= 0:
            raise Warning(_("The On The Road (OTR) price tidak diatur atau adalah nol.\n"
                            "Silahkan update OTR price atau hubungi MD untuk bantuan."))
        
        # TODO: margin validation should do in PBT modules
        # series = self.product_id.product_tmpl_id.series_id
        # margin = self.env['tw.master.target.margin.line'].sudo().search([
        #             ('series_id',  '=',  series.id),
        #             ('target_margin_id.company_id',  '=',  self.company_id.id),
        #             ('target_margin_id.state',  '=',  'active')])
        # if not margin:
        #     raise Warning(
        #         'Belum ada master margin untuk series %s di %s, silahkan hubungi SOH.'
        #         % (series.name, self.company_id.name)
        #     )
        sequence = self.env['ir.sequence'].suspend_security()
        if self.payment_type == 'Credit':
            if (self.unit_availability == 'indent') and (self.down_payment == 0):
                raise Warning(_("Attention! Indent unit down payment cannot be 0"))
            vals['state'] = 'proposed'
            vals['finco_submission_id'] = sequence.get_code_transaksi_4(self.finco_id.code, self.company_id.code)
            
            self.write(vals)

        # auto approved similar as Tunas Honda
        self.action_approved()
    
    def action_reject(self):
        vals = {
            'state':'open',
            'reject_uid': self._uid,
            'reject_date': self._get_default_date(),
            'log_ids': [Command.create({
                'name':'Reject Proposed',
                'date': datetime.now(),
                'category_id': self.env.ref('tw_lead.tw_lead_log_category_type_general').id,
            })]
        }
        if self.env.context.get('rejection_reason'):
            vals['rejection_reason'] = self.env.context['rejection_reason']

        self.write(vals)

    def action_receipt(self):
        if self.state == 'receipt':
            raise ValidationError(f'Silakan refresh halaman ini, karena state sudah {self._get_state_value()}')
        # TODO: in case this method is used like HoKi
        self.write({
            'state': 'receipt',
            'receipt_uid': self._uid,
            'receipt_date': self._get_default_date(),
        })

    def action_approved(self):
        if self.state == 'approved':
            raise ValidationError(f'Silakan refresh halaman ini, karena state sudah {self._get_state_value()}')
        self.write({
            'state': 'approved',
            'approve_uid': self._uid,
            'approve_date': self._get_default_date(),
            'log_ids': [Command.create({
                'name':'Approved Prospect',
                'date': datetime.now(),
                'category_id': self.env.ref('tw_lead.tw_lead_log_category_type_general').id,
            })]
        })

    # 14: private methods
    def _handle_won_lost(self, vals):
        # This method called again in module tw_lead is to change from crm.lead to tw.lead
        """ This method handle the state changes :
        - To lost : We need to increment corresponding lost count in scoring frequency table
        - To won : We need to increment corresponding won count in scoring frequency table
        - From lost to Won : We need to decrement corresponding lost count + increment corresponding won count
        in scoring frequency table.
        - From won to lost : We need to decrement corresponding won count + increment corresponding lost count
        in scoring frequency table."""
        Lead = self.env['tw.lead']
        leads_reach_won = Lead
        leads_leave_won = Lead
        leads_reach_lost = Lead
        leads_leave_lost = Lead
        won_stage_ids = self.env['crm.stage'].search([('is_won', '=', True)]).ids
        for lead in self:
            if 'stage_id' in vals:
                if vals['stage_id'] in won_stage_ids:
                    if lead.probability == 0:
                        leads_leave_lost += lead
                    leads_reach_won += lead
                elif lead.stage_id.id in won_stage_ids and lead.active:  # a lead can be lost at won_stage
                    leads_leave_won += lead
            if 'active' in vals:
                if not vals['active'] and lead.active:  # archive lead
                    if lead.stage_id.id in won_stage_ids and lead not in leads_leave_won:
                        leads_leave_won += lead
                    leads_reach_lost += lead
                elif vals['active'] and not lead.active:  # restore lead
                    leads_leave_lost += lead

        leads_reach_won._pls_increment_frequencies(to_state='won')
        leads_leave_won._pls_increment_frequencies(from_state='won')
        leads_reach_lost._pls_increment_frequencies(to_state='lost')
        leads_leave_lost._pls_increment_frequencies(from_state='lost')


    def _create_customer(self, payload):
        vals = {}
        if 'customer_name' in payload or self.customer_name:
            vals['name'] = payload.get('customer_name', self.customer_name)
        if 'identification_number' in payload:
            vals['identification_number'] = payload['identification_number']
        if 'identification_family_number' in payload:
            vals['identification_family_number'] = payload['identification_family_number']
        if 'birthplace' in payload:
            vals['birthplace'] = payload['birthplace']
        if 'birthdate' in payload:
            vals['birthdate'] = payload['birthdate']
        if 'phone' in payload:
            vals['phone'] = payload['phone']
        if 'mobile' in payload:
            vals['mobile'] = payload['mobile']
        if 'whatsapp' in payload:
            vals['whatsapp'] = payload['whatsapp']
        if 'email' in payload:
            vals['email'] = payload['email']
        if 'gender_id' in payload:
            vals['gender_id'] = payload['gender_id']
        if 'blood_type_id' in payload:
            vals['blood_type_id'] = payload['blood_type_id']
        if 'hobby_id' in payload:
            vals['hobby_id'] = payload['hobby_id']
        if 'religion_id' in payload:
            vals['religion_id'] = payload['religion_id']
        if 'education_id' in payload:
            vals['education_id'] = payload['education_id']
        if 'occupation_id' in payload:
            vals['occupation_id'] = payload['occupation_id']
        if 'unit_usage_id' in payload:
            vals['unit_usage_id'] = payload['unit_usage_id']
        if 'unit_operator_id' in payload:
            vals['unit_operator_id'] = payload['unit_operator_id']
        if 'expense_id' in payload:
            vals['expense_id'] = payload['expense_id']
        if 'motor_brand_id' in payload:
            vals['motor_brand_id'] = payload['motor_brand_id']
        if 'motor_type_id' in payload:
            vals['motor_type_id'] = payload['motor_type_id']
        if 'mobile_plan_status_id' in payload:
            vals['mobile_plan_status_id'] = payload['mobile_plan_status_id']
        if 'housing_tenure_id' in payload:
            vals['housing_tenure_id'] = payload['housing_tenure_id']
        if 'facebook' in payload:
            vals['facebook'] = payload['facebook']
        if 'youtube' in payload:
            vals['youtube'] = payload['youtube']
        if 'instagram' in payload:
            vals['instagram'] = payload['instagram']
        if 'twitter' in payload:
            vals['twitter'] = payload['twitter']

        category = self.env['res.partner.category'].search([('name', '=', 'Customer')])
        vals['category_id'] = [(6, 0, category.ids)]
        
        # TODO: this 2 fields could be company if any GC customer
        if 'company_type'in payload:
            vals['company_type'] = 'person'
        if 'company_id'in payload:
            vals['company_id'] = False

        if 'street' in payload:
            vals['street'] = payload['street']
        if 'street2' in payload:
            vals['street2'] = payload['street2']
        if 'rt' in payload:
            vals['rt'] = payload['rt']
        if 'rw' in payload:
            vals['rw'] = payload['rw']
        if 'state_id' in payload:
            vals['state_id'] = payload['state_id']
        if 'city_id' in payload:
            vals['city_id'] = payload['city_id']
        if 'district_id' in payload:
            vals['district_id'] = payload['district_id']
        if 'sub_district_id' in payload:
            vals['sub_district_id'] = payload['sub_district_id']
        if 'zip' in payload:
            vals['zip'] = payload['zip']

        if 'is_same_ktp' in payload:
            vals['same_address'] = payload['is_same_ktp']
        if 'street_domicile' in payload:
            vals['street_domicile'] = payload['street_domicile']
        if 'street2_domicile' in payload:
            vals['street2_domicile'] = payload['street2_domicile']
        if 'rt_domicile' in payload:
            vals['rt_domicile'] = payload['rt_domicile']
        if 'rw_domicile' in payload:
            vals['rw_domicile'] = payload['rw_domicile']
        if 'state_domicile_id' in payload:
            vals['state_domicile_id'] = payload['state_domicile_id']
        if 'city_domicile_id' in payload:
            vals['city_domicile_id'] = payload['city_domicile_id']
        if 'district_domicile_id' in payload:
            vals['district_domicile_id'] = payload['district_domicile_id']
        if 'sub_district_domicile_id' in payload:
            vals['sub_district_domicile_id'] = payload['sub_district_domicile_id']
        if 'zip_domicile' in payload:
            vals['zip_domicile'] = payload['zip_domicile']

        partner = self.env['res.partner'].suspend_security().create(vals)

        # Now create/update partner addresses
        if 'address_ids' in payload or self.address_ids:
            for address in payload.get('address_ids', self.address_ids):
                address_type_id = False
                address_name = False
                if isinstance(address, (list, tuple)) and len(address) > 2:
                    address_data = address[2]
                    address_name = address_data.get('name', address[1])
                    address_type_id = address_data.get('address_type_id') or (hasattr(address, 'address_type_id') and address.address_type_id.id)
                    address_fields = {
                        'street': address_data.get('street'),
                        'state_id': address_data.get('state_id'),
                        'city_id': address_data.get('city_id'),
                        'district_id': address_data.get('district_id'),
                        'sub_district_id': address_data.get('sub_district_id'),
                        'zip': address_data.get('zip')
                    }
                else:
                    address_type_id = getattr(address, 'address_type_id', False) and address.address_type_id.id
                    address_name = getattr(address, 'name', False)
                    address_fields = {
                        'street': getattr(address, 'street', False),
                        'state_id': getattr(address, 'state_id', False) and address.state_id.id,
                        'city_id': getattr(address, 'city_id', False) and address.city_id.id,
                        'district_id': getattr(address, 'district_id', False) and address.district_id.id,
                        'sub_district_id': getattr(address, 'sub_district_id', False) and address.sub_district_id.id,
                        'zip': getattr(address, 'zip', False)
                    }

                # Get address type
                address_type = self.env['tw.selection'].sudo().search([
                    ('type', '=', 'AddressType'),
                    ('id', '=', address_type_id)
                ], limit=1)

                if not address_type:
                    continue

                address_vals = {
                    'name': address_name or 'Alamat ' + address_type.value.capitalize(),
                    'rt': address_fields.get('rt'),
                    'rw': address_fields.get('rw'),
                    'street': address_fields.get('street'),
                    'street2': address_fields.get('street2'),
                    'zip': address_fields.get('zip'),
                    'state_id': address_fields.get('state_id'),
                    'city_id': address_fields.get('city_id'),
                    'district_id': address_fields.get('district_id'),
                    'sub_district_id': address_fields.get('sub_district_id'),
                    'address_type_id': address_type_id,
                }

                # Create/update the address in tw.partner.address
                self._update_partner_address(partner, address_vals)

        return partner

    def _update_related_customer(self, vals):
        # Ensure that only existing keys will be updated; key validation must be performed first.
        data = {}
        if 'identification_family_number' in vals:
            data['identification_family_number'] = vals['identification_family_number']
        if 'birthplace' in vals:
            data['birthplace'] = vals['birthplace']
        if 'birthdate' in vals:
            data['birthdate'] = vals['birthdate']
        if 'phone' in vals:
            data['phone'] = vals['phone']
        if 'mobile' in vals:
            data['mobile'] = vals['mobile']
        if 'whatsapp' in vals:
            data['whatsapp'] = vals['whatsapp']
        if 'email' in vals:
            data['email'] = vals['email']
        if 'gender_id' in vals:
            data['gender_id'] = vals['gender_id']
        if 'blood_type_id' in vals:
            data['blood_type_id'] = vals['blood_type_id']
        if 'hobby_id' in vals:
            data['hobby_id'] = vals['hobby_id']
        if 'religion_id' in vals:
            data['religion_id'] = vals['religion_id']
        if 'education_id' in vals:
            data['education_id'] = vals['education_id']
        if 'occupation_id' in vals:
            data['occupation_id'] = vals['occupation_id']
        if 'unit_usage_id' in vals:
            data['unit_usage_id'] = vals['unit_usage_id']
        if 'unit_operator_id' in vals:
            data['unit_operator_id'] = vals['unit_operator_id']
        if 'expense_id' in vals:
            data['expense_id'] = vals['expense_id']
        if 'motor_brand_id' in vals:
            data['motor_brand_id'] = vals['motor_brand_id']
        if 'motor_type_id' in vals:
            data['motor_type_id'] = vals['motor_type_id']
        if 'mobile_plan_status_id' in vals:
            data['mobile_plan_status_id'] = vals['mobile_plan_status_id']
        if 'housing_tenure_id' in vals:
            data['housing_tenure_id'] = vals['housing_tenure_id']
        if 'facebook' in vals:
            data['facebook'] = vals['facebook']
        if 'youtube' in vals:
            data['youtube'] = vals['youtube']
        if 'instagram' in vals:
            data['instagram'] = vals['instagram']
        if 'twitter' in vals:
            data['twitter'] = vals['twitter']

        # Update Address KTP and Domicile
        if 'street' in vals or self.street:
            data['street'] = vals.get('street', self.street)
        if 'street2' in vals or self.street2:
            data['street2'] = vals.get('street2', self.street2)
        if 'state_id' in vals or self.state_id:
            data['state_id'] = vals.get('state_id', self.state_id)
        if 'city_id' in vals or self.city_id:
            data['city_id'] = vals.get('city_id', self.city_id)
        if 'district_id' in vals or self.district_id:
            data['district_id'] = vals.get('district_id', self.district_id)
        if 'sub_district_id' in vals or self.sub_district_id:
            data['sub_district_id'] = vals.get('sub_district_id', self.sub_district_id)
        if 'zip' in vals or self.zip:
            data['zip'] = vals.get('zip', self.zip)

        if 'street_domicile' in vals or self.street_domicile:
            data['street_domicile'] = vals.get('street_domicile', self.street_domicile)
        if 'street2_domicile' in vals or self.street2_domicile:
            data['street2_domicile'] = vals.get('street2_domicile', self.street2_domicile)
        if 'state_domicile_id' in vals or self.state_domicile_id:
            data['state_domicile_id'] = vals.get('state_domicile_id', self.state_domicile_id)
        if 'city_domicile_id' in vals or self.city_domicile_id:
            data['city_domicile_id'] = vals.get('city_domicile_id', self.city_domicile_id)
        if 'district_domicile_id' in vals or self.district_domicile_id:
            data['district_domicile_id'] = vals.get('district_domicile_id', self.district_domicile_id)
        if 'sub_district_domicile_id' in vals or self.sub_district_domicile_id:
            data['sub_district_domicile_id'] = vals.get('sub_district_domicile_id', self.sub_district_domicile_id)
        if 'zip_domicile' in vals or self.zip_domicile:
            data['zip_domicile'] = vals.get('zip_domicile', self.zip_domicile)

        if 'address_ids' in vals:
            for address in vals['address_ids']:
                if isinstance(address, (list, tuple)) and len(address) > 2:
                    address_data = address[2]
                    address_type_id = address_data.get('address_type_id')
                    
                    # Prepare address data for both partner and address model
                    address_vals = {
                        'name': address_data.get('name', 'Alamat'),
                        'street': address_data.get('street'),
                        'street2': address_data.get('street2'),
                        'rt': address_data.get('rt'),
                        'rw': address_data.get('rw'),
                        'state_id': address_data.get('state_id'),
                        'city_id': address_data.get('city_id'),
                        'district_id': address_data.get('district_id'),
                        'sub_district_id': address_data.get('sub_district_id'),
                        'zip': address_data.get('zip'),
                        'address_type_id': address_type_id,
                    }

                    # Update the partner address record
                    self._update_partner_address(self.partner_id, address_vals)

        self.partner_id.suspend_security().write(data)
        self._sync_addresses(vals)

    def _sync_addresses(self, vals):
        """Sync address data from lead form to tw.lead.addresses model"""
        address_fields = [
            'street', 'street2', 'rt', 'rw', 'state_id', 'city_id', 
            'district_id', 'sub_district_id', 'zip',
            'street_domicile', 'street2_domicile', 'rt_domicile', 
            'rw_domicile', 'state_domicile_id', 'city_domicile_id',
            'district_domicile_id', 'sub_district_domicile_id', 'zip_domicile'
        ]
        if not self.ids and not any(field in vals for field in address_fields):
            return

        if not any(field in vals for field in address_fields):
            return

        AddressType = self.env['tw.selection']
        ktp_type = AddressType.search([('type', '=', 'AddressType'), ('value', '=', 'ktp')], limit=1)
        domisili_type = AddressType.search([('type', '=', 'AddressType'), ('value', '=', 'domisili')], limit=1)

        existing_ktp = self.address_ids.filtered(lambda a: a.address_type_id == ktp_type)
        existing_domisili = self.address_ids.filtered(lambda a: a.address_type_id == domisili_type)

        # Build KTP values
        ktp_vals = {
            'name': "Alamat KTP",
            'street': vals.get('street', self.street if self.ids else False),
            'street2': vals.get('street2', self.street2 if self.ids else False),
            'rt': vals.get('rt', self.rt if self.ids else False),
            'rw': vals.get('rw', self.rw if self.ids else False),
            'state_id': vals.get('state_id', self.state_id.id if self.ids else False),
            'city_id': vals.get('city_id', self.city_id.id if self.ids else False),
            'district_id': vals.get('district_id', self.district_id.id if self.ids else False),
            'sub_district_id': vals.get('sub_district_id', self.sub_district_id.id if self.ids else False),
            'zip': vals.get('zip', self.zip if self.ids else False),
            'address_type_id': ktp_type.id if ktp_type else False,
        }

        # Build Domicile values
        domicile_vals = {
            'name': "Alamat Domisili",
            'street': vals.get('street_domicile', self.street_domicile if self.ids else False),
            'street2': vals.get('street2_domicile', self.street2_domicile if self.ids else False),
            'rt': vals.get('rt_domicile', self.rt_domicile if self.ids else False),
            'rw': vals.get('rw_domicile', self.rw_domicile if self.ids else False),
            'state_id': vals.get('state_domicile_id', self.state_domicile_id.id if self.ids else False),
            'city_id': vals.get('city_domicile_id', self.city_domicile_id.id if self.ids else False),
            'district_id': vals.get('district_domicile_id', self.district_domicile_id.id if self.ids else False),
            'sub_district_id': vals.get('sub_district_domicile_id', self.sub_district_domicile_id.id if self.ids else False),
            'zip': vals.get('zip_domicile', self.zip_domicile if self.ids else False),
            'address_type_id': domisili_type.id if domisili_type else False,
        }

        address_vals_list = []

        if any(v for k, v in ktp_vals.items() if k not in ('name', 'address_type_id')):
            if existing_ktp:
                existing_ktp.write(ktp_vals)
            else:
                address_vals_list.append((0, 0, ktp_vals))

        if any(v for k, v in domicile_vals.items() if k not in ('name', 'address_type_id')):
            if existing_domisili:
                existing_domisili.write(domicile_vals)
            else:
                address_vals_list.append((0, 0, domicile_vals))

        if address_vals_list:
            if self.ids:
                self.write({'address_ids': address_vals_list})
            else:
                vals.setdefault('address_ids', []).extend(address_vals_list)


    def _update_partner_address(self, partner, address_vals):
        partner_address_obj = self.env['tw.partner.address']
        address_type_id = address_vals.get('address_type_id')

        if not address_type_id:
            return False

        # Search for existing address of the same type
        existing_address = partner_address_obj.search([
            ('partner_id', '=', partner.id),
            ('address_type_id', '=', address_type_id)
        ], limit=1)

        address_data = {
            'partner_id': partner.id,
            'address_type_id': address_type_id,
            'name': address_vals.get('name'),
            'street': address_vals.get('street', False),
            'street2': address_vals.get('street2', False),
            'rt': address_vals.get('rt', False),
            'rw': address_vals.get('rw', False),
            'state_id': address_vals.get('state_id', False),
            'city_id': address_vals.get('city_id', False),
            'district_id': address_vals.get('district_id', False),
            'sub_district_id': address_vals.get('sub_district_id', False),
            'zip': address_vals.get('zip', False),
        }

        if existing_address:
            existing_address.suspend_security().write(address_data)
            return existing_address
        else:
            return partner_address_obj.suspend_security().create(address_data)

    def get_lead_by_identification_number(self,no_ktp):
        lead_obj = self.suspend_security().search([
            ('identification_number','=',no_ktp),
            ('state','=','open')
        ],limit=1)
        return lead_obj
    
    def _get_or_create_partner_by_id(self, identification_number, vals):
        res_partner = False
        if identification_number:
            res_partner = self.env['res.partner'].search([('identification_number', '=', identification_number)])
            if not res_partner:
                res_partner = self._create_customer(vals)
        return res_partner
    
    def _get_on_the_road_price(self):
        self.ensure_one()
        
        currency = self.company_id.currency_id
        product_tmpl = self.product_id.product_tmpl_id
        price = self._get_basic_price()
        taxes = product_tmpl.taxes_id.compute_all(price, currency=currency, quantity=1, product=self.product_id)
        tax = sum([t['amount'] for t in taxes['taxes']])
        otr = taxes.get('total_excluded', 0)
        
        return otr + tax
    
    def _get_basic_price(self):
        currency = self.company_id.currency_id
        product_tmpl = self.product_id.product_tmpl_id
        pricelist_sale = self.company_id.branch_setting_id.pricelist_sale_unit_id
        unit_price = pricelist_sale.with_company(self.company_id)._get_product_price(product_tmpl, 1, currency, company_id=self.company_id.id)
        return unit_price