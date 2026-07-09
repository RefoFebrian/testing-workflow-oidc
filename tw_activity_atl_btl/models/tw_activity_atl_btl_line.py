# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
from threading import local
from dateutil.relativedelta import relativedelta
import calendar
import base64
import tempfile
from PIL import Image
import io
import re

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWActivityPlanLine(models.Model):
    _name = "tw.activity.atl.btl.line"
    _description = "Activity Plan ATL & BTL Line"
    _rec_name = 'display_name'
    _rec_names_search = ['name', 'activity_name']

    # 7: defaults methods
    def _get_year_default(self):
        return date.today().year
    
    def _get_domain_pic(self):
        company_obj = self.activity_id.company_id
        domain = [
            ('job_id.sales_force_id.value', 'in', ('salesman', 'sales_counter', 'sales_operation_head', 'sales_coordinator'))
        ]
        if company_obj:
            domain.append(('company_id', '=', company_obj.id))

        return domain

    # 8: fields
    name = fields.Char('Name')
    activity_name = fields.Char('Activity Name')
    display_name = fields.Char('Display Name', compute='_compute_display_name')
    act_type_code = fields.Char('Activity Type Code', related='act_type_id.code')
    sales_channel = fields.Char(compute='_compute_sales_channel')
    street = fields.Char('Street')
    rt = fields.Char('RT')
    rw = fields.Char('RW')
    lat = fields.Char('Latitude', compute='_compute_coordinates', store=True)
    long = fields.Char('Longitude', compute='_compute_coordinates', store=True)
    registry_number = fields.Char(string='Identification Number', compute='_compute_pic')
    job = fields.Char('Jabatan', compute='_compute_pic')
    phone_number = fields.Char('No Telp', compute='_compute_phone_number', store=True, readonly=False)
    rent_note = fields.Char('Rent Note')
    reason_reject_outstanding = fields.Text('Reason')
    
    display_unit = fields.Integer('Display Unit')
    target_unit = fields.Integer('Target Unit')
    target_customer = fields.Integer('Target Customer')
    
    total_cost = fields.Float('Total Cost',compute='compute_total_cost', store=True)
    cost_unit = fields.Float('Cost Unit')
    cost_unit_lm = fields.Float('Cost Unit LM')
    
    state = fields.Selection([
        ('draft','Draft'),
        ('open','Open'),
        ('confirmed','Confirmed'),
        ('done','Done'),
        ('rejected','Rejected'),
        ('revision','Revision')], default='draft')
    submission_type = fields.Selection([
        ('new','Baru'),
        ('update','Perpanjang')], string="Submission Type")

    is_location = fields.Boolean('Location ?',related='act_type_id.is_location',readonly=True)
    start_date = fields.Date('Start Date', help="Periode Event berlaku dari tanggal ini")
    end_date = fields.Date('End Date', help="Periode Event berlaku hingga tanggal ini")
    rent_start_date = fields.Date('Rent Start Date', help="Periode Sewa Lokasi berlaku dari tanggal ini")
    rent_end_date = fields.Date('Rent End Date', help="Periode Sewa Lokasi berlaku hingga tanggal ini")

    # 8.1: fields for foto
    loc_photo = fields.Binary('Foto Lokasi Upload')
    loc_photo_show = fields.Binary('Foto Lokasi', compute='_compute_loc_photo_show')
    filename_loc_photo = fields.Char('Filename')

    # 8.2: Audit Trail Fields
    open_uid = fields.Many2one('res.users','Open by')
    open_date = fields.Datetime('Open on')
    approved_loc_uid = fields.Many2one('res.users','Approved Loc by')
    approved_loc_date = fields.Datetime('Approved Loc on')
    reject_outstanding_uid = fields.Many2one('res.users','Reject Outstanding by')
    reject_outstanding_date = fields.Datetime('Rejected Outstanding on')
    confirm_lpj_uid = fields.Many2one('res.users','LPJ Confirmed by')
    confirm_lpj_date = fields.Datetime('LPJ Confirmed on')

    # 9: relation fields
    activity_id = fields.Many2one('tw.activity.atl.btl','Plan Activity',ondelete='cascade')
    company_id = fields.Many2one('res.company', 'Branch', compute='_compute_company', store=True)
    source_pos_location_id = fields.Many2one('stock.location','Source POS Location')
    location_id = fields.Many2one('stock.location','Location', copy=False)
    act_type_id = fields.Many2one('tw.master.activity.type','Activity Type',domain=[('active','=',True),('is_btl','!=',False)])
    mapping_activity_id = fields.Many2one('tw.mapping.titik.keramaian', 'Mapping Titik Keramaian')
    # activity_point_id = fields.Many2one('tw.titik.keramaian','Titik Keramaian', domain=[('active','=',True)])
    ring_id = fields.Many2one('tw.ring', 'Ring', compute='_compute_location', store=True)
    state_id = fields.Many2one('res.country.state', 'Provinsi', compute='_compute_location', store=True)
    city_id = fields.Many2one('res.city', 'Kota / Kab', compute='_compute_location', store=True)
    district_id = fields.Many2one('res.district', 'Kecamatan', compute='_compute_location', store=True)
    sub_district_id = fields.Many2one('res.sub.district', 'Kelurahan', compute='_compute_location', store=True)
    pic_id = fields.Many2one('hr.employee','PIC',domain=_get_domain_pic)
    sales_channel_id = fields.Many2one('tw.selection', "Jaringan Penjualan", domain=[('type', '=', 'SalesChannel')])

    detail_cost_ids = fields.One2many('tw.activity.atl.btl.detail.biaya','activity_line_id')
    history_location_ids = fields.One2many('tw.activity.detail.loc.history','activity_line_id')
    
    available_pic_ids = fields.Many2many('hr.employee', compute='_compute_pic_domain_ids')

    # 10: constraints & sql constraints
    @api.constrains('phone_number')
    def _validate_phone_number(self):
        for record in self:
            if record.phone_number and not re.match(r'^\d+$', record.phone_number):
                raise Warning("Nomor Telepon hanya boleh berisi angka saja.")

    @api.constrains('mapping_activity_id')
    def _check_similar_location(self):
        for record in self:
            if record.mapping_activity_id:
                similar_location = self.search([
                    ('activity_id', '=', record.activity_id.id),
                    ('mapping_activity_id', '=', record.mapping_activity_id.id),
                    ('start_date', '<=', record.end_date),
                    ('end_date', '>=', record.start_date),
                    ('id', '!=', record.id),
                    ('state', '!=', 'rejected'),
                ])
                if similar_location:
                    location_name = record.mapping_activity_id.activity_point_id.description
                    raise Warning('Titik Keramaian %s sudah ada! untuk periode %s - %s' % (location_name, record.start_date, record.end_date))
                
    @api.constrains('lat')
    def check_lat(self):
        for record in self:
            if record.lat:
                # Check if the latitude is a valid decimal number
                if not re.match(r'^-?\d*\.?\d+$', record.lat):
                    raise Warning('Format koordinat latitude tidak valid. Harap isi dengan angka desimal !\ncontoh: -6.2001, 106.8167')
    
    @api.constrains('long')
    def check_long(self):
        for record in self:
            if record.long:
                if not re.match(r'^-?\d*\.?\d+$', record.long):
                    raise Warning('Format koordinat latitude tidak valid. Harap isi dengan angka desimal !\ncontoh: -6.2001, 106.8167')

    @api.constrains('start_date')
    def cek_start_date(self):
        if self.start_date:
            month = calendar.month_name[int(self.activity_id.month)]
            
            # Use self.start_date directly, no need for strptime()
            start_date = self.start_date  

            if (start_date.month != int(self.activity_id.month)) or (start_date.year != int(self.activity_id.year)):
                raise Warning('Start date (periode awal event) tidak masuk pada periode bulan %s!' % (month))

        # Ensure start_date is checked against end_date only when both are set
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise Warning('Activity %s, End date (periode akhir event) tidak boleh kurang dari start date!' % (self.name))
        
    @api.constrains('end_date')
    def cek_end_date(self):
        if self.end_date:
            month = calendar.month_name[int(self.activity_id.month)]
            end_date = self.end_date  

            if (end_date.month != int(self.activity_id.month)) or (end_date.year != int(self.activity_id.year)):
                raise Warning('Activity %s, End date (periode akhir event) tidak masuk pada periode bulan %s!' % (self.name, month))

    @api.constrains('display_unit','target_unit', 'target_customer')
    def check_qty_fields(self):
        for record in self:
            if record.is_location and record.display_unit <= 0:
                raise Warning('Display unit harus lebih dari 0!')
            if record.target_unit <= 0:
                raise Warning('Target unit harus lebih dari 0!')
            if record.target_customer <= 0:
                raise Warning('Target customer harus lebih dari 0!')

    @api.constrains('start_date', 'end_date', 'rent_start_date', 'rent_end_date')
    def _check_rent_period_constrains(self):
        for record in self:
            if record.submission_type != 'update':
                record._check_rent_period()

    @api.constrains('activity_name', 'company_id', 'submission_type')
    def _check_existing_location_name(self):
        for record in self:
            if record.submission_type == 'new' and record.activity_name and record.company_id:
                existing_loc = self.env['stock.location'].sudo().search([
                    ('description', '=', record.activity_name),
                    ('company_id', '=', record.company_id.id)
                ], limit=1)
                if existing_loc:
                    raise Warning("Activity Name '%s' sudah terdaftar sebagai lokasi di Dealer ini. Mohon gunakan nama kegiatan lain atau hubungi admin." % record.activity_name)

    # 11: compute/depends & on change methods
    # TODO: compute for display unit based on product qty in location, need confirmation
    # @api.depends('source_pos_location_id', 'location_id')
    # def compute_display_units(self):
    #     testing = 0

    @api.depends('name', 'activity_name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = "[%s] %s" % (record.name, record.activity_name)

    @api.depends('company_id')
    def _compute_pic_domain_ids(self):
        for record in self:
            domain = [
                ('company_id', '=', record.company_id.id),
                ('job_id.sales_force_id.value', 'in', ('salesman', 'sales_counter', 'sales_operation_head', 'sales_coordinator'))
            ]

            record.available_pic_ids = self.env['hr.employee'].suspend_security().search(domain)

    @api.depends('pic_id')
    def _compute_phone_number(self):
        for record in self:
            if record.pic_id and record.pic_id.mobile_phone:
                record.phone_number = record.pic_id.mobile_phone
            elif not record.phone_number:
                record.phone_number = False

    @api.depends('filename_loc_photo')
    def _compute_loc_photo_show(self):
        for record in self:
            if record.filename_loc_photo:
                image_file = self.env['tw.config.files'].suspend_security().get_file(record.filename_loc_photo)
                record.loc_photo_show = image_file
            else:
                record.loc_photo_show = False

    @api.onchange('phone_number')
    def _onchange_valid_phone_number(self):
        for record in self:
            if record.phone_number:
                if not re.match(r'^\d+$', record.phone_number):
                    raise Warning("Nomor Telepon hanya boleh berisi angka saja.")
                if len(record.phone_number) < 10 or len(record.phone_number) > 13:
                    raise Warning("Nomor Telepon hanya boleh berisi angka dengan panjang antara 10 dan 13 digit.")

    @api.onchange('display_unit')
    def onchange_display_unit(self):
        for record in self:
            if record.display_unit and record.display_unit <= 0:
                raise Warning('Display unit harus lebih dari 0!')

    @api.onchange('target_customer')
    def onchange_target_customer(self):
        for record in self:
            if record.target_customer and record.target_customer <= 0:
                raise Warning('Target customer harus lebih dari 0!')

    @api.onchange('target_unit')
    def onchange_target_unit(self):
        for record in self:
            if record.target_unit and record.target_unit <= 0:
                raise Warning('Target unit harus lebih dari 0!')

    @api.depends('activity_id.company_id')
    def _compute_company(self):
        for record in self:
            record.company_id = record.activity_id.company_id
            
    @api.depends('sales_channel_id')
    def _compute_sales_channel(self):
        for record in self:
            if record.sales_channel_id:
                record.sales_channel = record.sales_channel_id.value.lower()
            else:
                record.sales_channel = False

    @api.depends('pic_id')
    def _compute_pic(self):
        for record in self:
            if record.pic_id:
                record.job = record.pic_id.job_id.name
                record.registry_number = record.pic_id.registry_number
            else:
                record.job = False
                record.registry_number = False
            

    @api.depends('detail_cost_ids.subtotal')
    def compute_total_cost(self):
        for record in self:
            total_cost = sum([x.subtotal for x in record.detail_cost_ids])
            record.total_cost = total_cost

    @api.depends('mapping_activity_id')
    def _compute_coordinates(self):
        for record in self:
            if record.mapping_activity_id:
                record.lat = record.mapping_activity_id.activity_point_id.lat
                record.long = record.mapping_activity_id.activity_point_id.long
            else:
                record.lat = False
                record.long = False

    @api.depends('mapping_activity_id')
    def _compute_location(self):
        for record in self:
            mapping_activity_obj = record.mapping_activity_id
            if mapping_activity_obj:
                if mapping_activity_obj.activity_point_id.street:
                    record.street = mapping_activity_obj.activity_point_id.street
                elif not record.street:
                    record.street = False

                if mapping_activity_obj.activity_point_id.rt:
                    record.rt = mapping_activity_obj.activity_point_id.rt
                elif not record.rt:
                    record.rt = False

                if mapping_activity_obj.activity_point_id.rw:
                    record.rw = mapping_activity_obj.activity_point_id.rw
                elif not record.rw:
                    record.rw = False

                record.state_id = mapping_activity_obj.activity_point_id.state_id.id
                record.city_id = mapping_activity_obj.activity_point_id.city_id.id
                record.district_id = mapping_activity_obj.activity_point_id.district_id.id
                record.sub_district_id = mapping_activity_obj.activity_point_id.sub_district_id.id
                record.ring_id = mapping_activity_obj.ring_id.id
            else:
                if not record.street:
                    record.street = False
                if not record.rt:
                    record.rt = False
                if not record.rw:
                    record.rw = False
                record.state_id = False
                record.city_id = False
                record.district_id = False
                record.sub_district_id = False
                record.ring_id = False

    @api.onchange('sales_channel_id')
    def onchange_sales_channel_id(self):
        self.act_type_id = False
        self.mapping_activity_id = False

    @api.onchange('start_date', 'end_date')
    def onchange_date(self):
        if self.start_date:
            month = calendar.month_name[int(self.activity_id.month)]
            
            # Use self.start_date directly, no need for strptime()
            start_date = self.start_date  

            if (start_date.month != int(self.activity_id.month)) or (start_date.year != int(self.activity_id.year)):
                raise Warning('Start date tidak masuk pada periode bulan %s!' % (month))

        # Ensure start_date is checked against end_date only when both are set
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise Warning('End date tidak boleh kurang dari start date!')

    @api.onchange('mapping_activity_id', 'start_date', 'end_date')
    def onchange_check_similar_location(self):
        self._check_similar_location()

    @api.onchange('mapping_activity_id')
    def onchange_mapping_activity_id(self):
        for rec in self:
            if rec.mapping_activity_id:
                rec.lat = rec.mapping_activity_id.activity_point_id.lat
                rec.long = rec.mapping_activity_id.activity_point_id.long
    
    @api.onchange('is_location')
    def onchange_is_location(self):
        self.submission_type = False
        self.location_id = False
        self.display_unit = False
        self.source_pos_location_id = False

    @api.onchange('lat')
    def onchange_lat(self):
        if self.lat:
            valid_chars = '0123456789.-'
            # Check if all characters are in the valid set
            is_all_valid_chars = all(char in valid_chars for char in self.lat)
            # Check if the value contains at least one digit and at most one dot
            has_valid_format = bool(re.match(r'^-?\d*\.?\d+$', self.lat))
            is_valid = is_all_valid_chars and has_valid_format
            if not is_valid:
                raise Warning('Silahkan isi angka sesuai dengan latitude !')
    
    @api.onchange('long')
    def onchange_long(self):
        if self.long:
            valid_chars = '0123456789.-'
            # Check if all characters are in the valid set
            is_all_valid_chars = all(char in valid_chars for char in self.long)
            # Check if the value contains at least one digit and at most one dot
            has_valid_format = bool(re.match(r'^-?\d*\.?\d+$', self.long))
            is_valid = is_all_valid_chars and has_valid_format
            if not is_valid:
                raise Warning('Silahkan isi angka sesuai dengan longitude !')
            
    @api.onchange('location_id')
    def onchange_name_location(self):
        self.activity_name = False
        if self.location_id:
            self.activity_name = self.location_id.description

    @api.onchange('location_id')
    def onchange_rent_period(self):
        if self.location_id:
            self.rent_start_date = self.location_id.effective_start_date
            self.rent_end_date = self.location_id.effective_end_date
            today = date.today()
            if self.rent_end_date and self.rent_end_date >= today:
                self.rent_note = "Lokasi sewa telah dibayar dan masih berlaku sampai %s" % (self.rent_end_date.strftime('%d-%b-%Y')) if self.rent_end_date else "Tidak ada tanggal akhir sewa yang ditetapkan untuk lokasi ini"
            else:
                self.rent_note = "Lokasi sewa telah kedaluwarsa pada %s" % (self.rent_end_date.strftime('%d-%b-%Y')) if self.rent_end_date else "Tidak ada tanggal akhir sewa yang ditetapkan untuk lokasi ini"

            if self.submission_type == 'update':
                self.rent_note += "\n*Periode akhir sewa akan update setelah melakukan approval pada Line data ini"
        else:
            self.rent_start_date = False
            self.rent_end_date = False
            self.rent_note = False

    @api.onchange('submission_type', 'rent_start_date', 'rent_end_date', 'start_date', 'end_date')
    def onchange_submission_type(self):
        if self.submission_type != 'update':
            self._check_rent_period()    

    @api.onchange('state')
    def onchange_branch(self):
        ctx_act_id = self._context.get('default_activity_id')
        if ctx_act_id and isinstance(ctx_act_id, int):
            activity_obj = self.env['tw.activity.atl.btl'].browse(ctx_act_id)
        elif self.activity_id and self.activity_id._origin and isinstance(self.activity_id._origin.id, int):
            activity_obj = self.activity_id._origin
        else:
            activity_obj = self.activity_id

        if not activity_obj or not activity_obj.company_id or not activity_obj.month or not activity_obj.year:
            raise Warning('Silahkan isi data header terlebih dahulu !')
        self.company_id = activity_obj.company_id.id       

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        config = self.env['tw.config.files']
        for vals in vals_list:
            loc_photo = False
            if vals.get('act_type_id'):
                activity_id = vals.get('activity_id') or self._context.get('default_activity_id')
                activity_atl_btl_obj = self.env['tw.activity.atl.btl'].browse(activity_id)
                branch_src = self.env['res.company'].suspend_security().search([('id','=',activity_atl_btl_obj.company_id.id)],limit=1)
                act_type_obj = self.env['tw.master.activity.type'].suspend_security().search([('id','=',vals['act_type_id'])],limit=1)
            vals['name'] = self.env['ir.sequence'].get_sequence_code(str(branch_src.code), str(act_type_obj.code))
            
            if vals.get('loc_photo'):
                loc_photo = vals.get('loc_photo')
                vals['loc_photo'] = False

            activity_atl_btl_line = super(TWActivityPlanLine, self).create(vals)

            if activity_atl_btl_line.state == 'open':
                # Initialize record if it starts in 'open' state (e.g. late additions via Add Activity)
                if not activity_atl_btl_line.open_uid:
                    activity_atl_btl_line.write({
                        'open_uid': self.env.uid,
                        'open_date': datetime.now()
                    })
                activity_atl_btl_line.check_activity_open()
                activity_atl_btl_line.action_history_result()

            titik_keramaian = activity_atl_btl_line.mapping_activity_id.activity_point_id.description
            config_obj = self.env['ir.config_parameter'].sudo()
            max_size_kb = float(config_obj.get_param('tw_activity_atl_btl.max_photo_size_kb', 300))
            min_size_kb = float(config_obj.get_param('tw_activity_atl_btl.min_photo_size_kb', 50))
            if loc_photo:
                allowed_ext = self.env['ir.config_parameter'].get_param('image_extensions')
                tmp_foto = str(vals['filename_loc_photo']).split('.')
                ext = tmp_foto[-1]
                if ext not in allowed_ext:
                    raise Warning('Event %s dengan Titik Keramaian %s, Tipe File Foto Lokasi yang diterima hanya format %s' % (activity_atl_btl_line.activity_name, titik_keramaian, allowed_ext))

                lead_id = vals.get('activity_id') or 'unknown'
                filename = f"tw_activity-loc_photo-{lead_id}.{ext}"
                file = config.suspend_security().upload_file(filename, loc_photo)
                cek_size = config.suspend_security().cek_size(filename)
                cek_size_kb = cek_size / 1024.0
                if cek_size_kb > max_size_kb:
                    raise Warning('Event %s dengan Titik Keramaian %s, File Foto Lokasi terlalu besar, maksimal %s KB' % (activity_atl_btl_line.activity_name, titik_keramaian, max_size_kb))
                if cek_size_kb < min_size_kb:
                    raise Warning('Event %s dengan Titik Keramaian %s, File Foto Lokasi terlalu kecil, minimal %s KB' % (activity_atl_btl_line.activity_name, titik_keramaian, min_size_kb))
                activity_atl_btl_line.filename_loc_photo = filename

        return activity_atl_btl_line

    def write(self, vals):
        config = self.env['tw.config.files']
        if vals.get('loc_photo'):
            loc_photo = vals.get('loc_photo')
            vals['loc_photo'] = False

            allowed_ext = self.env['ir.config_parameter'].get_param('image_extensions')
            tmp_foto = str(vals['filename_loc_photo']).split('.')
            ext = tmp_foto[-1]
            titik_keramaian = self.mapping_activity_id.activity_point_id.description
            config_obj = self.env['ir.config_parameter'].sudo()
            max_size_kb = float(config_obj.get_param('tw_activity_atl_btl.max_photo_size_kb', 300))
            min_size_kb = float(config_obj.get_param('tw_activity_atl_btl.min_photo_size_kb', 50))
            if ext not in allowed_ext:
                raise Warning('Event %s dengan Titik Keramaian %s, Tipe File Foto Lokasi yang diterima hanya format %s' % (self.activity_name, titik_keramaian, allowed_ext))

            lead_id = vals.get('activity_id') or 'unknown'
            filename = f"tw_activity-loc_photo-{lead_id}.{ext}"
            file = config.suspend_security().upload_file(filename, loc_photo)
            cek_size = config.suspend_security().cek_size(filename)
            cek_size_kb = cek_size / 1024.0
            if cek_size_kb > max_size_kb:
                raise Warning('Event %s dengan Titik Keramaian %s, File Foto Lokasi terlalu besar, maksimal %s KB' % (self.activity_name, titik_keramaian, max_size_kb))
            if cek_size_kb < min_size_kb:
                raise Warning('Event %s dengan Titik Keramaian %s, File Foto Lokasi terlalu kecil, minimal %s KB' % (self.activity_name, titik_keramaian, min_size_kb))
            self.filename_loc_photo = filename
                
        return super(TWActivityPlanLine, self).write(vals)

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning('Tidak bisa menghapus data detail !\n Data yang berstatus Draft saja yang bisa dihapus')
        return super(TWActivityPlanLine,self).unlink()

    # 13: action methods
    def action_open_activity(self):
        for rec in self:
            rec.write({
                'state': 'open',
                'open_uid': self.env.user.id,
                'open_date': datetime.now()
            })
            rec.check_activity_open()
            rec.action_history_result()

    def action_confirm_outstanding(self):
        for rec in self:
            if rec.is_location:
                vals = rec._prepare_vals_location()
                if not rec.location_id:
                    # Check for existing location with same name before creating
                    existing_loc = self.env['stock.location'].suspend_security().search([
                        ('name', '=', rec.name),
                        ('company_id', '=', rec.company_id.id)
                    ], limit=1)
                    if existing_loc:
                        rec.location_id = existing_loc.id
                    else:
                        create_loc = rec._create_stock_location(vals)
                        rec.location_id = create_loc.id
                else:
                    for key in ('effective_start_date', 'is_loc_btl', 'act_type_id'):
                        vals.pop(key, None)
                    rec.location_id.suspend_security().write(vals)
         
            rec.write({
                'state':'confirmed',
                'approved_loc_uid': rec.env.uid,
                'approved_loc_date': datetime.now(),
            })
            rec.action_history_result()

    def action_confirm_lpj(self):
        vals = {
            'state': 'done',
            'confirm_lpj_uid': self._uid,
            'confirm_lpj_date': datetime.now()
        }

        if self.state == 'done':
            raise Warning('Activity Plan sudah dalam status Done!')

        self.write(vals)
        self.check_activity_done()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_view_detail_activity(self):
        form_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_line_all_form_view').id
        return {
            'name': 'Detail',
            'res_model': 'tw.activity.atl.btl.line',
            'type': 'ir.actions.act_window',
            'view_id': form_id,
            'views': [(form_id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id, 
            'context': {
                'create': False,
                'edit': False,
                'delete': False,
            },
        }
    
    def action_history_result(self):
        ctx_act_id = self._context.get('default_activity_id')
        if ctx_act_id and isinstance(ctx_act_id, int):
            activity_obj = self.env['tw.activity.atl.btl'].browse(ctx_act_id)
        elif self.activity_id and self.activity_id._origin and isinstance(self.activity_id._origin.id, int):
            activity_obj = self.activity_id._origin
        else:
            activity_obj = self.activity_id

        if not activity_obj or not activity_obj.company_id or not activity_obj.month or not activity_obj.year:
            raise Warning('Silahkan isi data header terlebih dahulu !')
        
        self.history_location_ids = False
        history_ids = []
        now = date(int(self.activity_id.year), int(self.activity_id.month), 1)  
        start_month = now - relativedelta(months=3)
        if self.sales_channel_id and self.act_type_id and self.mapping_activity_id:
            activity_point_id = self.mapping_activity_id.activity_point_id.id
            query_loc = ""
            if self.location_id:
                query_loc += "AND pal.location_id = %d" %(self.location_id)
            query = """
                SELECT EXTRACT(MONTH FROM date_order) as month
                , pp.id as prod_id
                , pt.categ_id as categ_id
                FROM tw_activity_atl_btl pa
                INNER JOIN tw_activity_atl_btl_line pal ON pal.activity_id = pa.id
                INNER JOIN tw_dealer_sale_order so ON so.activity_plan_id = pal.id
                INNER JOIN tw_dealer_sale_order_line sol on so.id = sol.order_id
                INNER JOIN product_product pp ON pp.id = sol.product_id
                INNER JOIN product_template pt ON pt.id = pp.product_tmpl_id                
                WHERE so.sales_channel_id = %d
                AND so.sales_source_location_id = %d
                AND so.activity_point_id = %d
                AND date_order BETWEEN '%s' AND '%s'
                %s
                ORDER BY month ASC
            """ %(self.sales_channel_id.id,self.act_type_id.id,activity_point_id,start_month,now,query_loc)
            self._cr.execute (query)
            ress =  self._cr.dictfetchall()
            ids = {}
            if len(ress) > 0:
                for res in ress:
                    month = (calendar.month_name[int(res['month'])])
                    if not ids.get(month):
                        ids[month] = {
                            'name':month,
                            'qty':0,
                            'detail_ids':[]
                        }
                    ids[month]['qty'] += 1
                    ids[month]['detail_ids'].append([0,False,{
                        'product_id':res['prod_id'],
                        'categ_id':res['categ_id']
                    }])
            for x in ids.values():
                history_ids.append([0,False,x])
        self.history_location_ids = history_ids

    def action_tw_activity_atl_btl_review_list(self):
        list_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_review_list_view').id
        form_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_review_form_view').id
        tgl = str(date.today())
        domain = [('state','in',('open','confirmed','done')),('total_cost','>',0)]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Review Location BTL',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.activity.atl.btl.line',
            'domain': domain,
            'context':{'group_by': ['company_id'], 'search_default_state_open': 1},
            'views': [(list_id, 'list'), (form_id, 'form')],
        }

    def action_view_location(self):
        form_id = self.env.ref('stock.view_location_form').id
        return {
            'name': ('Location'),
            'res_model': 'stock.location',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(form_id, 'form')],
            'view_mode': 'form',
            'target': 'current',
            'view_type': 'form',
            'res_id': self.location_id.id,
        }   
    
    def action_outstanding_btl(self):
        list_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_line_all_list_view').id
        form_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_line_all_form_view').id
        tgl = str(date.today())
        domain = [('state','in',('open','waiting_for_approval'))]

        # user = self.env.user
        # employee = user.employee_id
        # job_obj = employee.job_id
        # sales_force_id = job_obj.sales_force_id
        # if sales_force_id and sales_force_id.value in ('sales_coordinator', 'area_manager'):
        #     # Team members = subordinates in HR hierarchy
        #     team_ids = employee.child_ids.ids  # direct reports
        #     domain += [('pic_id', 'in', team_ids + [employee.id])]
        # else:
        #     # Regular employee: only own records
        #     domain += [('pic_id', '=', employee.id)]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Outstanding BTL',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.activity.atl.btl.line',
            'domain': domain,
            'views': [(list_id, 'list'), (form_id, 'form')],
            'context': {
                'outstanding_btl': True,
                'create': False,
                'edit': False,
                'delete': False,
            },
        }
    
    def action_lpj_atl_btl(self):
        list_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_line_all_list_view').id
        form_id = self.env.ref('tw_activity_atl_btl.tw_activity_atl_btl_line_all_form_view').id
        tgl = str(date.today())
        
        domain = self.get_domain_lpj_menu()

        return {
            'type': 'ir.actions.act_window',
            'name': 'LPJ',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.activity.atl.btl.line',
            'domain': domain,
            'views': [(list_id, 'list'), (form_id, 'form')],
            'context': {
                'lpj_btl': True,
                'create': False,
                'edit': False,
                'delete': False,
            },
        }

    # 14: private methods
    def get_domain_lpj_menu(self):
        domain = [('state', 'in', ('confirmed', 'settlement'))]

        user = self.env.user
        employee = user.employee_id
        job_obj = employee.job_id
        sales_force_id = job_obj.sales_force_id

        # TODO: Comment temporary for checking if LPJ menu only show based on ir.rule
        # if sales_force_id and sales_force_id.value in ('sales_coordinator', 'area_manager'):
        #     # Team members = subordinates in HR hierarchy
        #     team_ids = employee.child_ids.ids  # direct reports
        #     domain += [('pic_id', 'in', team_ids + [employee.id])]
        # else:
        #     # Regular employee: only own records
        #     domain += [('pic_id', '=', employee.id)]
        return domain

    def _check_rent_period(self):
        """Validate that rent period covers the activity period"""
        if not all([self.rent_start_date, self.rent_end_date, self.start_date, self.end_date]):
            return True
            
        rent_start = fields.Date.from_string(self.rent_start_date)
        rent_end = fields.Date.from_string(self.rent_end_date)
        act_start = fields.Date.from_string(self.start_date)
        act_end = fields.Date.from_string(self.end_date)
        
        if rent_start > act_start or rent_end < act_end:
            raise Warning("Periode sewa harus mencakup periode kegiatan (%s - %s)" % (self.start_date, self.end_date))
        if rent_start > rent_end:
            raise Warning("Tanggal mulai sewa tidak boleh setelah tanggal selesai sewa")

        return True

    def check_activity_open(self):
        activity = self.env['tw.activity.atl.btl.line'].sudo().search([
            ('activity_id','=',self.activity_id.id),
            ('state','in',('draft','open','confirmed'))])
        if not activity:
            self.activity_id.write({
                'state':'open',
                'open_uid':self._uid,
                'open_date':datetime.now()
            })
    
    def check_activity_done(self):
        activity = self.env['tw.activity.atl.btl.line'].sudo().search([
            ('activity_id', '=', self.activity_id.id),
            ('state', 'in', ('draft', 'open', 'confirmed'))])
        if not activity:
            self.activity_id.action_done_activity_atl_btl

    def _prepare_vals_location(self):
        location_type = self.env['tw.selection'].sudo().search([('type', '=', 'StockLocation'), ('value', '=', 'event')], limit=1)
        vals = {
            'company_id': self.company_id.id,
            'act_type_id': self.act_type_id.id,
            'type_id': location_type.id,
            'usage': 'internal',
            'active': True,
            'is_loc_btl': True,
            'description': self.activity_name,
            'effective_start_date': self.rent_start_date,
            'effective_end_date': self.rent_end_date,
        }
        return vals

    def _create_stock_location(self, vals):
        # TODO: terdapat method global untuk pembuatan stock_location
        """Create and return a BTL stock.location for this record.

        Responsibilities:
        - Resolve default source location from outgoing picking type for the company
        - Optionally set BTL location type when act_type_id is Pameran/Channel
        - Set location name
        - Create and return the stock.location record
        """
        self.ensure_one()
        picking_type = self.env['stock.picking.type'].suspend_security().search([
            ('company_id', '=', self.company_id.id),
            ('code', '=', 'outgoing')
        ], limit=1)
        if not picking_type or not picking_type.default_location_src_id:
            raise Warning(_('Outgoing picking type atau default source location tidak terkonfigurasi untuk dealer ini.'))

        create_vals = dict(vals)  # work on a copy
        create_vals['location_id'] = picking_type.default_location_src_id.id

        if self.act_type_id and self.act_type_id.name in ('Pameran', 'Channel'):
            type_obj = self.env['tw.selection'].suspend_security().search([
                ('type', '=', 'StockLocationBTL'),
                ('value', '=', self.act_type_id.name)
            ], limit=1)
            create_vals['btl_loc_type_id'] = type_obj.id if type_obj else False

        create_vals['name'] = self.name
        location = self.env['stock.location'].suspend_security().create(create_vals)

        return location
        