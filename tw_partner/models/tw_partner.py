# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import timedelta,datetime

# 2: import of known third party lib
from validate_email import validate_email
import re
import time

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, AccessError
from odoo.osv import expression
from odoo.osv import expression
from odoo.addons.account.models.company import PEPPOL_LIST

# 5: local imports

# 6: Import of unknown third party lib


try:
    import phonenumbers
except ImportError:
    phonenumbers = None

class Partner(models.Model):
    _inherit = "res.partner"
    _description = "Inherit Res Partner"
    _rec_names_search = ['name', 'code']

    # 7: defaults methods 
    def _default_country_id(self):
        return self.env.user.company_id.country_id

    # 8: fields
    id_customer = fields.Char('ID Customer')
    code = fields.Char('Code', compute="_compute_code", store=True, readonly=False)
    same_address = fields.Boolean('Same Address ?')
    
    # pajak
    is_pkp = fields.Boolean('PKP ?')
    alamat_pkp = fields.Char('Alamat di PKP')
    tgl_pengukuhan = fields.Date('Tgl Pengukuhan')
    no_npwp = fields.Char('No NPWP')
    alamat_npwp = fields.Char('Alamat di NPWP')

    # informasi partner
    identification_number = fields.Char('No KTP')
    birthplace = fields.Char('Tempat Lahir')
    birthdate = fields.Date(string='Tgl Lahir')
    another_job = fields.Char(string='Occupation Lain')
    identification_family_number =  fields.Char(string='No KK')
    rt = fields.Char(string='RT')
    rw = fields.Char(string='RW')
    
    rt_domicile = fields.Char(string='RT Domicile')
    rw_domicile = fields.Char(string='RW Domicile')
    street_domicile = fields.Char(string='Street Domicile')
    street2_domicile = fields.Char(string='Street2 Domicile')
    zip_domicile = fields.Char(string='ZIP Domicile')

    state_text = fields.Char(string="Provinsi (Text)")
    city_text = fields.Char(string="Kota/Kabupaten (Text)")
    district_text = fields.Char(string="Kecamatan (Text)")
    sub_district_text = fields.Char(string="Kelurahan (Text)")

    # media social
    facebook = fields.Char(string='Facebook')
    instagram = fields.Char(string='Instagram')
    twitter = fields.Char(string='Twitter')
    youtube = fields.Char(string='Youtube')

    responsible =  fields.Char(string='Penanggung Jawab')
    ethnic_group = fields.Char(string='Suku')
    persona = fields.Text(string='Karakter Konsumen') 

    # selection

    # duplicate check message (non-stored, computed via onchange)
    duplicate_warning_message = fields.Char(
        string='Duplicate Warning',
        compute=False,
        store=False,
    )
    search_ktp_hp = fields.Char(
        string='Cari KTP / No HP',
        store=False,
    )
    duplicate_partner_html = fields.Html(
        string='Duplicate HTML',
        compute='_compute_duplicate_partner_html',
        store=False,
    )

    @api.depends('duplicate_partner_id')
    def _compute_duplicate_partner_html(self):
        for rec in self:
            if rec.duplicate_partner_id:
                url = f"/web#id={rec.duplicate_partner_id.id}&model=res.partner&view_type=form"
                rec.duplicate_partner_html = f'''
                    <a href="{url}" class="btn btn-success text-white" style="text-decoration: none;">
                        <i class="fa fa-check"></i> Gunakan Data Ini (Buka Profil)
                    </a>
                '''
            else:
                rec.duplicate_partner_html = False

    # 9: relation fields
    # Address
    country_domicile_id = fields.Many2one('res.country', string='Country Domicile', default=_default_country_id)
    state_domicile_id = fields.Many2one('res.country.state', string='State Domicile', domain="[('country_id', '=', country_domicile_id)]")
    city_domicile_id = fields.Many2one('res.city', string='City Domicile', domain="[('state_id', '=', state_domicile_id)]")
    district_domicile_id = fields.Many2one('res.district', string='District Domicile', domain="[('city_id', '=', city_domicile_id)]")
    sub_district_domicile_id = fields.Many2one('res.sub.district', string='Sub District Domicile', domain="[('district_id', '=', district_domicile_id)]")

    city_id = fields.Many2one(comodel_name='res.city',  string="Kabupaten",  help="",domain="[('state_id', '=', state_id)]")
    district_id = fields.Many2one(comodel_name='res.district',  string="Kecamatan",  help="",domain="[('city_id', '=', city_id)]")
    sub_district_id = fields.Many2one(comodel_name='res.sub.district',  string="Kelurahan",  help="",domain="[('district_id', '=', district_id)]")

    company_id = fields.Many2one("res.company", string="Branch")
    finco_id =  fields.Many2one('res.partner', string='Fincoy', domain=[('category_id.name','=','Finance Company')])
    contact_ids = fields.One2many('tw.partner.contact','partner_id','Contacts')
    address_ids = fields.One2many('tw.partner.address','partner_id','Addresses')
    customer_code_id = fields.Many2one('tw.selection',string='Kode Customer', domain=[('type','=','CustomerCode')])
    purchase_type_id = fields.Many2one('tw.selection',string='Jenis Pembelian', domain=[('type','=','PurchaseType')])
    religion_id = fields.Many2one('tw.selection',string='Agama', domain=[('type','=','Religion')])
    education_id = fields.Many2one('tw.selection',string='Pendidikan', domain=[('type','=','Education')])
    occupation_id = fields.Many2one('tw.selection',string='Pekerjaan', domain=[('type','=','Occupation')])
    expense_id = fields.Many2one('tw.selection',string='Expense', domain=[('type','=','Expense')])
    customer_type_id = fields.Many2one('tw.selection',string='Jenis Customer', domain=[('type','=','CustomerType')])
    mobile_plan_status_id = fields.Many2one('tw.selection', string='Status HP' , domain=[('type','=','StatusMobilePhone')])
    housing_tenure_id = fields.Many2one('tw.selection', string='Status Rumah' , domain=[('type','=','HousingTenure')])
    gender_id =  fields.Many2one('tw.selection', string='Jenis Kelamin' , domain=[('type','=','Gender')])
    hobby_id =  fields.Many2one('tw.selection',string='Hobby', domain=[('type','=','Hobby')])
    blood_type_id = fields.Many2one('tw.selection',string='Golongan Darah', domain=[('type','=','BloodType')])
    motor_brand_id = fields.Many2one('tw.selection',string='Merk Motor', domain=[('type','=','MotorBrand')])
    motor_type_id = fields.Many2one('tw.selection',string='Jenis Motor', domain=[('type','=','MotorType')])
    unit_usage_id = fields.Many2one('tw.selection',string='Kegunaan Motor', domain=[('type','=','MotorUtilization')])
    unit_operator_id = fields.Many2one('tw.selection',string='Pengguna Motor', domain=[('type','=','MotorUser')])
    family_card_ids = fields.One2many(
        comodel_name='tw.family.card',
        inverse_name='partner_id',
        string='Kartu Keluarga',
        required=False)
    partner_history_ids = fields.One2many('tw.partner.history', 'partner_id', string='History')
    
    # temporary relation fields
    duplicate_partner_id = fields.Many2one(
        'res.partner',
        string='Duplicate Partner',
        store=False,
    )
    
    # 10: constraints & sql constraints

    @api.constrains('zip', 'zip_domicile')
    def _check_zip_format(self):
        for record in self:
            if record.zip and not record.zip.isdigit():
                raise Warning("ZIP code must contain only numbers")
            if record.zip_domicile and not record.zip_domicile.isdigit():
                raise Warning("Domicile ZIP code must contain only numbers")

    @api.constrains('birthdate')
    def cek_birth_date(self):
        for record in self:
            if record.birthdate:
                today = fields.Date.today()
                
                if record.birthdate > today:
                    raise Warning('birthdate must be less than today')
                
                birthdate = datetime.strptime(record.birthdate.strftime('%Y-%m-%d'), '%Y-%m-%d')
                today = datetime.strptime(today.strftime('%Y-%m-%d'), '%Y-%m-%d')
                age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
                if age < 18:
                    raise Warning('Minimum age must be 18 years old.')


    @api.constrains('mobile')
    def cek_mobile(self):
        for partner in self:
            if partner.mobile:
                self._validate_phone_number(partner.mobile)
                
    @api.constrains('mobile', 'identification_number')
    def cek_duplicate_mobile_ktp(self):
        for partner in self:
            domain = []
            if partner.mobile:
                domain.append(('mobile', '=', partner.mobile))
            if partner.identification_number:
                domain.append(('identification_number', '=', partner.identification_number))
                
            if len(domain) == 2:
                domain = ['|'] + domain
                
            if domain:
                duplicate = self.search(domain + [('id', '!=', partner.id)], limit=1)
                if duplicate:
                    raise Warning(
                        f"Mohon maaf, No KTP / HP yang Anda masukkan sudah terdaftar di database kami atas nama {duplicate.name}.\n\n"
                        "Untuk mempertahankan kerapian data, mohon batalkan form ini dan gunakan fitur pencarian pada layar sebelumnya. "
                        "Jika terjadi kesalahan pendataan (KTP/HP diambil oleh orang lain), silakan melapor ke tim Operasional."
                    )

    @api.constrains('identification_number')
    def cek_identification_number(self):
        if self.identification_number and self.customer_code_id.value not in ('G','J','C'):
            if not self.identification_number.isdigit() or len(self.identification_number) != 16:
                raise Warning('Maaf, nomor KTP %s tidak falid. Format penulisan No KTP harus angka dan 16 Digit !' % self.identification_number)

    @api.constrains('rt','rw')
    def cek_rt_rw(self):
        if self.rt:
            if len(self.rt) > 3:
                raise Warning('RT tidak boleh lebih dari 3 digit !')

            if not self.rt.isdigit():
                raise Warning('RT hanya boleh angka !')
        
        if self.rw:
            if len(self.rw) > 3:
                raise Warning('RW tidak boleh lebih dari 3 digit !')

            if not self.rw.isdigit():
                raise Warning('RW hanya boleh angka !')

    
    @api.constrains('no_npwp')
    def cek_no_npwp(self):
        if self.no_npwp:
            if not self.no_npwp.isdigit() or len(self.no_npwp) != 15:
                raise Warning(f'Maaf, Format penulisan No NPWP harus angka (hiraukan tanda baca) dan 15 Digit ! \n\n HINT : Panjang No NPWP yang diinputkan ialah {len(self.no_npwp)} Digit.')


    # 11: compute/depends & on change methods
    @api.depends('company_type')
    def _compute_code(self):
        for record in self:
            if not record.code:
                record.code = record.get_sequence('STK')

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for record in self:
            name = record.name
            if record.code:
                name = f"[{record.code}] {name}"
            record.display_name = name
    
    @api.onchange('same_address')
    def _onchange_same_address(self):
        for partner in self:
            if partner.same_address:
                partner.street_domicile = partner.street
                partner.street2_domicile = partner.street2
                partner.city_domicile_id = partner.city_id.id
                partner.state_domicile_id = partner.state_id.id
                partner.country_domicile_id = partner.country_id.id
                partner.district_domicile_id = partner.district_id.id
                partner.sub_district_domicile_id = partner.sub_district_id.id
                partner.zip_domicile = partner.zip
                partner.rt_domicile = partner.rt
                partner.rw_domicile = partner.rw
            else:
                partner.street_domicile = False
                partner.street2_domicile = False
                partner.city_domicile_id = False
                partner.state_domicile_id = False
                partner.country_domicile_id = False
                partner.district_domicile_id = False
                partner.sub_district_domicile_id = False
                partner.zip_domicile = False
                partner.rt_domicile = False
                partner.rw_domicile = False

    @api.onchange('rt', 'rw', 'street', 'street2','zip_code', 'zip')
    def _onchange_rt(self):
        if self.same_address:
            self._onchange_same_address()
    
    @api.onchange('state_id')
    def _onchange_state_id(self):
        self.city_id = False
        if self.same_address:
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
        if self.same_address:
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
        if self.same_address:
            self._onchange_same_address()

    @api.onchange('district_id')
    def _onchange_district_text(self):
        if self.district_id:
            self.district_text = self.district_id.name
        else:
            self.district_text = False

    @api.onchange('sub_district_id')
    def _onchange_sub_district(self):
        if self.sub_district_id:
            self.zip = self.sub_district_id.zip_code
        if self.same_address:
            self._onchange_same_address()

    @api.onchange('sub_district_id')
    def _onchange_sub_district_text(self):
        if self.sub_district_id:
            self.sub_district_text = self.sub_district_id.name
        else:
            self.sub_district_text = False
    
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

    @api.onchange('search_ktp_hp')
    def _onchange_search_ktp_hp(self):
        """Real-time duplicate check for KTP or mobile number using a single field.
        Populates duplicate_warning_message to drive the Progressive Disclosure UI.
        If no duplicate, auto-fills mobile or identification_number to help the user."""
        self.duplicate_warning_message = False
        self.duplicate_partner_id = False
        
        if self.search_ktp_hp:
            val = self.search_ktp_hp.strip()
            
            # Remove all non-digits to get the core number
            clean_val = re.sub(r'\D', '', val)
            
            # Dynamically handle prefix '08' vs '628' and DB dirty formats (spaces, dashes, etc.)
            if clean_val and len(clean_val) >= 8:
                if clean_val.startswith('08'):
                    base = clean_val[1:]
                elif clean_val.startswith('628'):
                    base = clean_val[2:]
                else:
                    base = clean_val
                
                # Transform "8238..." into wildcard "%8%2%3%8%..." to seamlessly match dirty DB data
                wildcard_search = '%' + '%'.join(list(base)) + '%'
            else:
                wildcard_search = val
            
            # Check duplicate against both mobile and identification_number using ilike
            domain = ['|', ('mobile', 'ilike', wildcard_search), ('identification_number', 'ilike', wildcard_search)]
            duplicate = self.search(domain + [('id', '!=', self._origin.id or False)], limit=1)
            
            if duplicate:
                self.duplicate_warning_message = (
                    f"No HP / KTP ini sudah terdaftar atas nama: {duplicate.name} "
                    f"(Kode: {duplicate.code or '-'})."
                )
                self.duplicate_partner_id = duplicate.id
            else:
                # Auto-fill based on logic: 16 digits is usually KTP
                if val.isdigit() and len(val) == 16:
                    self.identification_number = val
                    if not self.mobile:
                        self.mobile = False
                else:
                    self.mobile = val
                    if not self.identification_number:
                        self.identification_number = False

    @api.onchange('email')
    def _onchange_email(self):
        if self.email:
            cek = validate_email(self.email)
            if not cek:
                raise Warning(
                    ('Email tidak valid, silahkan dicek kembali !')) 

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        create_vals_list = []
        created_partner = self.env['res.partner']
        updated_partner = self.env['res.partner']
        for vals in vals_list:
            if vals.get('alamat'):
                vals['alamat'] = vals['alamat'].title()
                vals['street'] = vals['alamat'].title()
            if vals.get('code'):
                vals['code'] = vals['code'].upper()
            if vals.get('ethnic_group'):
                vals['ethnic_group'] = vals['ethnic_group'].title()
            if vals.get('jabatan'):
                vals['jabatan'] = vals['jabatan'].title()
            if vals.get('another_job'):
                vals['another_job'] = vals['another_job'].title()
            if vals.get('mobile'):
                self._validate_phone_number(vals.get('mobile'))
                no_telp_type_id = self.env.ref('tw_partner.contact_type_no_telp').id
                no_telp_exist = self.env['tw.partner.contact'].suspend_security().check_partner_contact(self.id,no_telp_type_id,vals['mobile'])
                if not no_telp_exist:
                    vals.update({
                        'mobile': vals['mobile'],
                        'contact_ids': [[0,0,{
                            'company_id': vals.get('company_id',False),
                            'name': vals['mobile'],
                            'type_id': self.env.ref('tw_partner.contact_type_no_telp').id
                        }]]
                    })
            
            if vals.get('category_id'):
                if isinstance(vals.get('category_id'), list) and vals.get('category_id') and vals.get('category_id')[0][0] == 6:
                    category_ids = vals.get('category_id')[0][2]  # Extract list of IDs
                    categories = self.env['res.partner.category'].browse(category_ids)
                    if any(c.name == 'Customer' for c in categories):
                        if not vals.get('code'):
                            vals['code'] = self.get_sequence('STK')
            vals.update(self._validate_questionnaire(vals))
            if vals.get('identification_number'):
                existing_partner = self.env['res.partner'].sudo().search([
                    ('identification_number', '=', vals.get('identification_number')),
                ])
                if existing_partner:
                    if self.env.context.get('import_file'):
                        raise Warning("Data dengan nomor KTP %s sudah terdaftar" % vals.get('identification_number'))
                    existing_partner.write(vals)
                    updated_partner += existing_partner
                else:
                    create_vals_list.append(vals)
            else:
                create_vals_list.append(vals)
        
        if create_vals_list:
            created_partner = super(Partner,self).create(create_vals_list)
        all_partner = created_partner + updated_partner
        all_partner._validate_partner()
        return all_partner

    
    def write(self, vals):
        if vals.get('alamat'):
            vals['alamat'] = vals['alamat'].title()
            vals['street'] = vals['alamat'].title()
        if vals.get('ethnic_group'):
            vals['ethnic_group'] = vals['ethnic_group'].title()
        if vals.get('jabatan'):
            vals['jabatan'] = vals['jabatan'].title()
        if vals.get('another_job'):
            vals['another_job'] = vals['another_job'].title()
        if vals.get('code'):
            vals['code'] = vals['code'].upper()
        if vals.get('mobile'):
            self._validate_phone_number(vals.get('mobile'))
            no_telp_type_id = self.env.ref('tw_partner.contact_type_no_telp').id
            no_telp_exist = self.env['tw.partner.contact'].suspend_security().check_partner_contact(self.id,no_telp_type_id,vals['mobile'])
            if not no_telp_exist:
                vals.update({
                    'mobile': vals['mobile'],
                    'contact_ids': [Command.create({
                        'company_id': vals.get('company_id',False),
                        'name': vals['mobile'],
                        'type_id': self.env.ref('tw_partner.contact_type_no_telp').id
                    })]
                })
            if self._context.get('origin'):
                self._create_history(
                    description='Mobile Number',
                    before_update=self.mobile,
                    after_update=vals['mobile'],
                    origin=self._context.get('origin')
                )   

        vals.update(self._validate_questionnaire(vals))
        write = super(Partner, self).write(vals)
        self._validate_partner()
        return write

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100, order=None):
        domain = args or []
        match_domain = []
        if name:
            if name.isdigit():
                clean_val = re.sub(r'\D', '', name)
                if clean_val and len(clean_val) >= 8:
                    if clean_val.startswith('08'):
                        base = clean_val[1:]
                    elif clean_val.startswith('628'):
                        base = clean_val[2:]
                    else:
                        base = clean_val
                    
                    wildcard_search = '%' + '%'.join(list(base)) + '%'
                    match_domain = ['|', ('identification_number', 'ilike', wildcard_search), ('mobile', 'ilike', wildcard_search)]
                else:
                    if name[0] != '0':
                        match_domain = [('identification_number', '=ilike', '%' + name + '%')]
                    else:
                        match_domain = [('mobile', operator, name)]
            else:
                match_domain = ['|',('name', operator, name), ('code', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                match_domain = ['&', '!'] + match_domain[1:]
        
        partners = self.search_fetch(expression.AND([domain, match_domain]), ['display_name'], limit=limit)
        return [(product.id, product.display_name) for product in partners.sudo()]

    def get_formview_action(self, access_uid=None):
        """ Override this method in order to redirect many2one towards the right model depending on access_uid """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_partner.group_tw_partner_read'):
            raise AccessError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res

    # 13: action methods
    def action_res_partner_customer_tree(self):
        tree_id = self.env.ref('tw_partner.tw_res_partner_view_tree').id
        form_id = self.env.ref('tw_partner.tw_res_partner_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'res.partner',
            'domain': [('category_id.name','=','Customer')],
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'context':{}
        }
    
    def action_res_partner_supplier_tree(self):
        tree_id = self.env.ref('tw_partner.res_partner_vendor_view_tree').id
        form_id = self.env.ref('tw_partner.res_partner_vendor_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Supplier',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'res.partner',
            'domain': [('category_id.name','in',('Vendor','General Supplier'))],
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'context':{'default_is_vendor':1,  }
        }
    
    def action_view(self):
        tree_id = self.env.ref('tw_partner.view_tw_partner_tree').id
        form_id = self.env.ref('tw_partner.tw_partner_contact_form_view').id
        search_id = self.env.ref('tw_partner.search_tw_partner').id
        hidden_ids = self.get_hidden_ids()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Partners',
            'view_mode': 'list,form',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'search_view_id': search_id,
            'res_model': 'res.partner',
            'domain': [('id','not in',hidden_ids)]
        }
    
    # 14: private methods
    def get_sequence(self, prefix):
        seq = self.env['ir.sequence']
        seq_name = '{0}'.format(prefix)
        ids = self.env['ir.sequence'].search([('name',  '=',  seq_name)])
        if not ids:
            prefix = '/%(y)s/%(month)s/'
            prefix = seq_name + prefix
            ids = self.env['ir.sequence'].create(
                {
                    'name': seq_name,
                    'implementation': 'standard', 
                    'prefix': prefix,
                    'padding': 5,
                }
            )
        return ids.next_by_id()

    def get_partner(self, partner_id, partner_company_id=False,type_id=False):
        partner_id = int(partner_id)
        query_where = 'WHERE 1=1 '
        query_where += f'AND p.id = {partner_id}'
        
        if partner_company_id:
            query_where += f'AND p.company_id = {partner_company_id}'
        
        if type_id:
            query_where += f'AND tct.type_id = {type_id}'
        
        get_query = f"""
            SELECT 
                p.id,
                tpc.id,
                tct.name as name,
                tct.type_id
            FROM res_partner p
            LEFT JOIN tw_partner_contact tpc ON p.id = tpc.partner_id
            LEFT JOIN tw_selection tct ON tct.id = tpc.type_id and p.company_id = tpc.company_id
            {query_where}
            ORDER BY tpc.id desc LIMIT 1
        """
        self._cr.execute(get_query)
        ress = self._cr.dictfetchone()
        if ress:
            return str(ress['name'])
        return False
    
    def get_hidden_ids(self):
        ids = [1,3,4,5,6]
        get_resigned = """
            select p.id id from hr_employee e
            left join resource_resource r on r.id = e.resource_id
            left join res_users u on u.id = r.user_id
            left join res_partner p on p.id = u.partner_id
            where r.active = false and p.id is not null
        """
        self._cr.execute(get_resigned)
        results = self._cr.dictfetchall()
        for res in results:
            if res['id'] not in ids:
                ids.append(res['id'])
        return ids

    def _validate_partner(self):
        # Check duplicate partner based on KTP number & NPWP
        for partner in self:
            if partner.identification_number:
                existing_partner = self.env['res.partner'].sudo().search([
                    ('identification_number', '=', partner.identification_number),
                    ('id', '!=', partner.id)
                ])
                if existing_partner:
                    raise Warning('Nomor KTP %s sudah terdaftar di partner %s' % (partner.identification_number, existing_partner.display_name))
            #TODO: Apakah Main Dealer EX: Daya, hanya boleh menjadi 1 Partner?
            # if partner.no_npwp:
            #     existing_partner = self.env['res.partner'].sudo().search([
            #         ('no_npwp', '=', partner.no_npwp),
            #         ('id', '!=', partner.id)
            #     ])
            #     if existing_partner:
            #         raise Warning('Nomor NPWP %s sudah terdaftar di partner %s' % (partner.no_npwp, existing_partner.display_name))


    def _validate_questionnaire(self, vals):
        # questionnaire id must be validated to obtained the valid value
        selection = self.env['tw.selection']
        if 'customer_code_id' in vals:
            vals['customer_code_id'] = selection.validate_selection(vals['customer_code_id'], 'CustomerCode')
        if 'purchase_type_id' in vals:
            vals['purchase_type_id'] = selection.validate_selection(vals['purchase_type_id'], 'PurchaseType')
        if 'religion_id' in vals:
            vals['religion_id'] = selection.validate_selection(vals['religion_id'], 'Religion')
        if 'education_id' in vals:
            vals['education_id'] = selection.validate_selection(vals['education_id'], 'Education')
        if 'occupation_id' in vals:
            vals['occupation_id'] = selection.validate_selection(vals['occupation_id'], 'Occupation')
        if 'expense_id' in vals:
            vals['expense_id'] = selection.validate_selection(vals['expense_id'], 'Expense')
        if 'mobile_plan_status_id' in vals:
            vals['mobile_plan_status_id'] = selection.validate_selection(vals['mobile_plan_status_id'], 'StatusMobilePhone')
        if 'housing_tenure_id' in vals:
            vals['housing_tenure_id'] = selection.validate_selection(vals['housing_tenure_id'], 'HousingTenure')
        if 'gender_id' in vals:
            vals['gender_id'] = selection.validate_selection(vals['gender_id'], 'Gender')
        if 'hobby_id' in vals:
            vals['hobby_id'] = selection.validate_selection(vals['hobby_id'], 'Hobby')
        if 'blood_type_id' in vals:
            vals['blood_type_id'] = selection.validate_selection(vals['blood_type_id'], 'BloodType')
        if 'motor_brand_id' in vals:
            vals['motor_brand_id'] = selection.validate_selection(vals['motor_brand_id'], 'MotorBrand')
        if 'motor_type_id' in vals:
            vals['motor_type_id'] = selection.validate_selection(vals['motor_type_id'], 'MotorType')
        if 'unit_usage_id' in vals:
            vals['unit_usage_id'] = selection.validate_selection(vals['unit_usage_id'], 'MotorUtilization')
        if 'unit_operator_id' in vals:
            vals['unit_operator_id'] = selection.validate_selection(vals['unit_operator_id'], 'MotorUser')
        
        return vals
    
    def _validate_phone_number(self,phone):
        number_only = self._sanitize_phone_number(phone)
        if not number_only.isdigit() or len(number_only) < 5 :
            raise Warning('No telp tidak boleh mengandung karakter, minimal 5 digit harus angka ! \n No telp : %s' % str(phone))
        if len(number_only) > 13 :
            raise Warning('No telp tidak boleh lebih dari 13 dan harus angka ! \n No telp : %s' % str(phone))
        return number_only
        
    def _sanitize_phone_number(self, phone_number=None):
        # self.ensure_one() # ValueError: Expected singleton: res.partner()
        error_message = _(
            "Please enter the mobile number in the correct international format.\n"
            "For example: +628123456789, where +62 is the country code.")

        if not phonenumbers:
            raise Warning(_("Please install the phonenumbers library."))

        if not phone_number:
            return

        # Clean spaces, hyphens, and other characters
        phone_number = phone_number.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

        # If it starts with '0', convert to '62' (international format for Indonesia)
        if phone_number.startswith('0'):
            phone_number = '62' + phone_number[1:]

        if not phone_number.startswith('+'):
            phone_number = f'+{phone_number}'

        try:
            phone_nbr = phonenumbers.parse(phone_number)
        except phonenumbers.phonenumberutil.NumberParseException:
            raise Warning(error_message + '\n ' + phone_number)

        # Skip strict validation for Indonesian numbers (+62) because the python phonenumbers 
        # library is often outdated and rejects valid new prefix blocks (e.g., By.U, new Telkomsel).
        if not phone_number.startswith('+62') and not phonenumbers.is_valid_number(phone_nbr):
            raise Warning(error_message + '\n ' + phone_number)

        number_only = self._get_sanitized_phone_number(phone_number)
        return number_only
    
    def _get_sanitized_phone_number(self, phone_number=None):
        number = phone_number or self.mobile
        if number:
            number = number.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if number.startswith('0'):
                number = '62' + number[1:]
            if not number.startswith('+'):
                number = f'+{number}'
        try:
            phone_nbr = phonenumbers.parse(number)
        except phonenumbers.phonenumberutil.NumberParseException:
            raise Warning("Please enter the mobile number in the correct international format.")
        
        number_only = phonenumbers.format_number(phone_nbr, phonenumbers.PhoneNumberFormat.NATIONAL).replace(' ', '').replace('-', '')
        return number_only

    def _create_history(self,description,before_update,after_update,origin):
        self.env['tw.partner.history'].create({
            'description': description+' Changed!',
            'before_update': before_update,
            'after_update': after_update,
            'partner_id': self.id,
            'origin': origin,
        })

    # 12: Actions
    def action_use_duplicate_partner(self):
        """Action for 'Gunakan Data Ini' button.
        Returns an action to open the duplicate partner's form view directly in the same tab."""
        self.ensure_one()
        if self.duplicate_partner_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Customer Profile',
                'res_model': 'res.partner',
                'res_id': self.duplicate_partner_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

    # TODO: Area_id belum ada pada res_users
    # def action_res_partner_customer_tree(self):
    #     action_customer_tree = super(Partner,self).action_res_partner_customer_tree()
    #     areas = self.env['res.users'].suspend_security().browse(self._uid).area_id.company_ids
    #     action_customer_tree['domain']= [('company_id', 'in', [b.id for b in areas]),('is_customer','=',True)]
    #     return action_customer_tree
      
    
    # def action_res_partner_supplier_tree(self):
    #     action_supplier_tree = super(Partner,self).action_res_partner_supplier_tree()
    #     areas = self.env['res.users'].suspend_security().browse(self._uid).area_id.company_ids
    #     action_supplier_tree['domain'] = [('is_vendor','=',True),('company_id', 'in', [b.id for b in areas])]
    #     return action_supplier_tree 
