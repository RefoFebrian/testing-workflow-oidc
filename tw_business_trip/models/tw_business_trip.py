# -*- coding: utf-8 -*-

# 1: imports of python lib
import difflib
import json
import os
import logging
import re
import io
import base64

# 2: import of known third party lib
from datetime import date, timedelta, datetime
from PyPDF2 import PdfMerger

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)

class TwBusinessTrip(models.Model):
    _name = "tw.business.trip"
    _inherit = ["tw.attachment.mixin"]
    _description = "Business Trip / Perjalanan Dinas"
    _order = "id desc"

    def _get_default_date(self):
        return self.env['res.company'].get_default_date()
    
    def _get_default_pic_id(self):
        employee_obj = self.env['hr.employee'].sudo().search([
            ('user_id', '=', self.env.user.id)
        ], limit=1)

        if not employee_obj:
            raise Warning("Employee not found for current user.")

        return employee_obj.id

    def _get_default_company_id(self):
        employee_obj = self.env['hr.employee'].sudo().search([
            ('user_id', '=', self.env.user.id)
        ], limit=1)

        if not employee_obj or not employee_obj.company_id:
            raise Warning("Company not found for current user.")

        return employee_obj.company_id.id
    
    def _get_default_plafon_food(self):
        in_values = [u.id for u in self.env.user.groups_id]
        plafon_obj = self.env['tw.business.trip.plafon'].sudo().search([('name', '=', 'uang_saku'), ('group_id', 'in', in_values)], order='nominal_domestic DESC', limit=1)
        if not plafon_obj:
            raise Warning("Plafon not found for current user.")
        return plafon_obj.id

    def _get_default_plafon_accommodation(self):
        in_values = [u.id for u in self.env.user.groups_id]
        plafon_obj = self.env['tw.business.trip.plafon'].sudo().search([('name', '=', 'accommodation'), ('group_id', 'in', in_values)], order='nominal_domestic DESC', limit=1)
        if not plafon_obj:
            raise Warning("Plafon not found for current user.")
        return plafon_obj.id
   
    # 8: fields
    name = fields.Char(string="Nomor Perjalanan Dinas")
    date = fields.Date(string='Tanggal', default=_get_default_date)
    objective = fields.Text(string="Tujuan")
    necessary = fields.Text(string="Keperluan")
    revisi_reason = fields.Text(string='Alasan Revisi')
    lumpsum = fields.Boolean(string="Lumpsum", default=False) # pembayaran sekaligus dalam satu waktu untuk biaya tertentu
    is_domestic = fields.Boolean(string="Dalam Negeri", default=True)
    previous_state = fields.Char(string="Previous State")
    merged_pdf = fields.Binary("PDF", attachment=True)

    region = fields.Selection(selection=[
        ('asia', 'Asia'),
        ('non_asia', 'Non Asia')
    ], string="Wilayah", default='asia')
    type = fields.Selection(selection=[
        ("actual", "Actual"), 
        ("planning", "Planning")
    ], default="planning")
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('upload_ticket', 'Proses Upload Tiket'),
        ('selesai_upload_ticket', 'Selesai Upload Tiket'),
        ('departed', 'Berangkat'),
        ('arrived', 'Kembali'),
        ('advance_payment', 'Advance Payment'),
        ('settlement', 'Settlement'),
        ('payment_request', 'Payment Requested'),
        ('supplier_payment', 'Supplier Payment'),
        ('done', 'Done'),
        ('revisi', 'Revisi'),
    ], default='draft', string='Status')
    state_payment_request = fields.Selection(related="payment_request_id.state", string='Status Payment Request')
    state_supplier_payment = fields.Selection(related="supplier_payment_id.state", string='Status Supplier Payment')
    state_advance_payment = fields.Selection(related="advance_payment_id.state", string='Status Advance Payment')
    state_settlement = fields.Selection(related="settlement_id.state", string='Status Settlement')
    
    is_bs = fields.Selection(selection=[
        ('ya', 'Ya'),
        ('tidak', 'Tidak')
    ], string="Apakah BS ?")
    
    is_airplane = fields.Selection(selection=[
        ('ya', 'Ya'),
        ('tidak', 'Tidak')
    ], string="Pakai Pesawat ?")

    actual_departure_date = fields.Date(string="Tanggal Berangkat Actual")
    actual_arrival_date = fields.Date(string="Tanggal Kembali Actual")

    planning_departure_date = fields.Date(string="Tanggal Berangkat Planning")
    planning_arrival_date = fields.Date(string="Tanggal Kembali Planning")

    actual_food_days = fields.Integer(string="Hari Actual Uang makan / Saku")
    actual_food_cost = fields.Integer(string="Biaya Uang makan / Saku Actual", compute="_compute_actual_food_cost", store=True)

    planning_food_days = fields.Integer(string="Hari Planning Uang makan / Saku")
    planning_food_cost = fields.Integer(string="Biaya Uang makan / Saku Planning", compute="_compute_planning_food_cost", store=True)

    selisih_food_days = fields.Integer(string="Selish Hari Uang makan / Saku", compute="_compute_selisih_food_days", store=True)
    selisih_food_cost = fields.Integer(string="Selisih Biaya Uang makan / Saku", compute="_compute_selisih_food_cost", store=True)

    actual_accommodation_days = fields.Integer(string="Malam Actual Akomodasi / Penginapan Actual", default=0)
    actual_accommodation_cost = fields.Integer(string="Biaya Akomodasi / Penginapan Actual", default=0)

    planning_accommodation_days = fields.Integer(string="Malam Planning Akomodasi / Penginapan Actual")
    planning_accommodation_cost = fields.Integer(string="Biaya Akomodasi / Penginapan Actual", compute="_compute_planning_accommodation_cost", store=True)

    selisih_accommodation_days = fields.Integer(string="Selisih Malam Akomodasi / Penginapan", compute="_compute_selisih_accommodation_days", store=True)
    selisih_accommodation_cost = fields.Integer(string="Selisih  Biaya Akomodasi / Penginapan", compute="_compute_selisih_accommodation_cost", store=True)

    # Amounts
    actual_amount_total = fields.Integer(string="Total Actual", compute="_compute_actual_amount_total", store=True)
    planning_amount_total = fields.Integer(string="Total Planning", compute="_compute_planning_amount_total", store=True)
    selisih_amount_total = fields.Integer(string="Total Selisih", compute="_compute_selisih_amount_total", store=True)

    # Pesawat
    airline_id = fields.Many2one('tw.selection',string='Maskapai Berangkat', domain=[('type','=','Maskapai Penerbangan')])
    airline_return_id = fields.Many2one('tw.selection',string='Maskapai Kembali', domain=[('type','=','Maskapai Penerbangan')])
    scheduled_departure_time = fields.Datetime('Jadwal Penerbangan Berangkat')
    scheduled_return_time = fields.Datetime('Jadwal Kembali Berangkat')
    ticket_departure_time = fields.Datetime('Jadwal Penerbangan Berangkat di Tiket')
    ticket_return_time = fields.Datetime('Jadwal Penerbangan Kembali di Tiket')
    
    files_upload_flight_departure = fields.Binary("Upload Berkas Tiket Berangkat")
    filename_upload_flight_departure = fields.Char("Nama Berkas Tiket Berangkat")
    files_flight_departure = fields.Binary("Download Berkas Tiket Berangkat", compute='_compute_files_flight_departure')  # , store=False
    filename_flight_departure = fields.Char("Nama Berkas Tiket Berangkat")
    
    files_upload_flight_return = fields.Binary("Upload Berkas Tiket Kembali")
    filename_upload_flight_return = fields.Char("Nama Berkas Tiket Kembali")
    files_flight_return = fields.Binary("Download Berkas Tiket Kembali", compute='_compute_files_flight_return')  # , store=False
    filename_flight_return = fields.Char("Nama Berkas Tiket Kembali")

    # Doc
    files_upload_objective = fields.Binary("Upload Berkas")
    filename_upload_objective = fields.Char("Nama Berkas")
    files_objective = fields.Binary("Download Berkas", compute='_compute_files_objective')  # , store=False
    filename_objective = fields.Char("Nama Berkas")

    files_upload_accommodation = fields.Binary("Upload Berkas")
    filename_upload_accommodation = fields.Char("Nama Berkas")
    files_accommodation = fields.Binary("Download Berkas", compute='_compute_files_accommodation')  # , store=False
    filename_accommodation = fields.Char("Nama Berkas")
    
    # Audit Trail
    rfa_uid = fields.Many2one('res.users', string='RFA by', readonly=True)
    rfa_date = fields.Datetime(string='RFA on', readonly=True)
    done_uid = fields.Many2one('res.users', string='Done by', readonly=True)
    done_date = fields.Datetime(string='Done on', readonly=True)

    # 9: relation fields
    pic_id = fields.Many2one(string="PIC", comodel_name="hr.employee", ondelete='restrict', default=_get_default_pic_id)
    company_id = fields.Many2one("res.company", 'Branch', ondelete='restrict', default=_get_default_company_id)

    plafon_food_id = fields.Many2one(string="Plafon Uang Makan", comodel_name="tw.business.trip.plafon", domain=[('plafon_food_id.name', '=', 'uang_saku')], default=_get_default_plafon_food)
    plafon_accommodation_id = fields.Many2one(string="Plafon Akomondasi / Penginapan", comodel_name="tw.business.trip.plafon", domain=[('plafon_food_id.name', '=', 'accommodation')], default=_get_default_plafon_accommodation)
    payment_request_id = fields.Many2one('tw.payment.request', string='Payment Request')
    supplier_payment_id = fields.Many2one('tw.account.payment', string='Supplier Payment')
    advance_payment_id = fields.Many2one('tw.advance.payment', string='Advance Payment')
    settlement_id = fields.Many2one('tw.settlement', string='Settlement')

    transportation_line_ids = fields.One2many(string="Transportations", comodel_name="tw.business.trip.transport", inverse_name="business_trip_id")
    detail_activity_line_ids = fields.One2many(string="Detail Kegiatan", comodel_name="tw.business.trip.detail", inverse_name="business_trip_id")
    approval_ids = fields.One2many('tw.approval.line', 'transaction_id', string='Budget Approval', domain=[('model_id', '=', _name)])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('planning_food_days', 'actual_food_days')
    def _compute_selisih_food_days(self):
        for record in self:
            record.selisih_food_days = abs(record.planning_food_days - record.actual_food_days)

    @api.depends('is_domestic', 'actual_food_cost', 'planning_food_cost')
    def _compute_selisih_food_cost(self):
        for record in self:
            record.selisih_food_cost = record.actual_food_cost - record.planning_food_cost

    @api.depends('is_domestic', 'planning_accommodation_days', 'actual_accommodation_days')
    def _compute_selisih_accommodation_days(self):
        for record in self:
            record.selisih_accommodation_days = abs(record.planning_accommodation_days - record.actual_accommodation_days)

    @api.depends('planning_accommodation_cost', 'actual_accommodation_cost')
    def _compute_selisih_accommodation_cost(self):
        for record in self:
            record.selisih_accommodation_cost = record.actual_accommodation_cost - record.planning_accommodation_cost

    @api.depends('is_domestic', 'actual_food_cost', 'actual_accommodation_cost', 'transportation_line_ids.actual_cost')
    def _compute_actual_amount_total(self):
        for record in self:
            record.actual_amount_total = sum(x.actual_cost for x in record.transportation_line_ids) + sum([record.actual_food_cost, record.actual_accommodation_cost])

    @api.depends('is_domestic', 'planning_food_cost', 'planning_accommodation_cost', 'transportation_line_ids.planning_cost')
    def _compute_planning_amount_total(self):
        for record in self:
            record.planning_amount_total = sum(x.planning_cost for x in record.transportation_line_ids) + sum([record.planning_accommodation_cost, record.planning_food_cost])

    @api.depends('actual_amount_total', 'planning_amount_total')
    def _compute_selisih_amount_total(self):
        for record in self:
            record.selisih_amount_total = record.actual_amount_total - record.planning_amount_total

    @api.depends('is_domestic', 'region', 'planning_food_days')
    def _compute_planning_food_cost(self):
        for record in self:
            nominal = record.planning_food_days * record.plafon_food_id.nominal_domestic
            if not record.is_domestic:
                if record.region == 'asia':
                    nominal = record.planning_food_days * (record.plafon_food_id.nominal_asia * record.plafon_food_id.dollar_rate)
                else:
                    nominal = record.planning_food_days * (record.plafon_food_id.nominal_non_asia * record.plafon_food_id.dollar_rate)

            record.planning_food_cost = nominal

    @api.depends('is_domestic', 'region', 'actual_food_days')
    def _compute_actual_food_cost(self):
        for record in self:
            nominal = record.actual_food_days * record.plafon_food_id.nominal_domestic
            if not record.is_domestic:
                if record.region == 'asia':
                    nominal = record.actual_food_days * (record.plafon_food_id.nominal_asia * record.plafon_food_id.dollar_rate)
                else:
                    nominal = record.actual_food_days * (record.plafon_food_id.nominal_non_asia * record.plafon_food_id.dollar_rate)

            record.actual_food_cost = nominal

    @api.depends('is_domestic', 'region', 'planning_accommodation_days')
    def _compute_planning_accommodation_cost(self):
        for record in self:
            nominal = record.planning_accommodation_days * record.plafon_accommodation_id.nominal_domestic
            if not record.is_domestic:
                if record.region == 'asia':
                    nominal = record.planning_accommodation_days * (record.plafon_accommodation_id.nominal_asia * record.plafon_accommodation_id.dollar_rate)
                else:
                    nominal = record.planning_accommodation_days * (record.plafon_accommodation_id.nominal_non_asia * record.plafon_accommodation_id.dollar_rate)

            record.planning_accommodation_cost = nominal

    def _compute_files_objective(self):
        for x in self:
            x.files_objective = False
            if x.filename_objective:
                x.files_objective = self.env['tw.config.files'].suspend_security().get_file(x.filename_objective)

    def _compute_files_accommodation(self):
        for x in self:
            x.files_accommodation = False
            if x.filename_accommodation:
                x.files_accommodation = self.env['tw.config.files'].suspend_security().get_file(x.filename_accommodation)
                
    def _compute_files_flight_departure(self):
        for x in self:
            x.files_flight_departure = False
            if x.filename_flight_departure:
                x.files_flight_departure = self.env['tw.config.files'].suspend_security().get_file(x.filename_flight_departure)
                
    def _compute_files_flight_return(self):
        for x in self:
            x.files_flight_return = False
            if x.filename_flight_return:
                x.files_flight_return = self.env['tw.config.files'].suspend_security().get_file(x.filename_flight_return)

    @api.onchange('company_id')
    def _onchange_company_id_warning(self):
        employee = self.env['hr.employee'].sudo().search(
            [('user_id', '=', self.env.user.id)],
            limit=1
        )

        if employee and employee.company_id:
            if employee.company_id not in self.env.companies:
                self.company_id = False
                if employee.company_id.id not in self.env.companies.ids:
                    return {
                        'warning': {
                            'title': 'Akses Company',
                            'message': (
                                'Anda tidak memiliki akses ke company %s.\n'
                                'Silakan aktifkan company tersebut terlebih dahulu.'
                            ) % employee.company_id.name
                        }
                    }
                

    @api.onchange('actual_accommodation_cost')
    def _onchange_actual_accommodation_cost(self):
        self._check_accommodation_cost(self.is_domestic, self.region, self.actual_accommodation_cost, self.actual_accommodation_days, self.plafon_accommodation_id.nominal_domestic, self.plafon_accommodation_id.nominal_asia, self.plafon_accommodation_id.nominal_non_asia, self.plafon_accommodation_id.dollar_rate)

    @api.onchange('actual_arrival_date', 'actual_departure_date')
    def _onchange_selisih_hari_actual(self):
        arrived_date = self.actual_arrival_date
        deparature_date = self.actual_departure_date

        if arrived_date and deparature_date:
            tgl_berangkat = datetime.strptime(str(deparature_date), '%Y-%m-%d').date()
            tgl_kembali = datetime.strptime(str(arrived_date), '%Y-%m-%d').date()
            selisih = (tgl_kembali - tgl_berangkat).days

            self.actual_accommodation_days = selisih
            self.actual_food_days = selisih

    @api.onchange('planning_arrival_date', 'planning_departure_date')
    def _onchange_selisih_hari_planning(self):
        arrived_date = self.planning_arrival_date
        deparature_date = self.planning_departure_date

        if arrived_date and deparature_date:
            tgl_berangkat = datetime.strptime(str(deparature_date), '%Y-%m-%d').date()
            tgl_kembali = datetime.strptime(str(arrived_date), '%Y-%m-%d').date()
            selisih = (tgl_kembali - tgl_berangkat).days

            self.planning_accommodation_days = selisih
            self.planning_food_days = selisih

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            for transport_line in vals.get("transportation_line_ids", []):
                attach = transport_line[2]
                if vals.get('state') in ('draft','revisi') and attach.get('planning_cost', 0) <= 0:
                    raise Warning("Perjalanan Dinas harus mengisi biaya planning tranportasi")

            company_code = self.env['res.company'].sudo().browse(vals.get('company_id')).code
            vals['name'] = self.env['ir.sequence'].get_sequence_code('PD', str(company_code))

            now = date.today().strftime("%Y-%m-%d")

            create = super(TwBusinessTrip, self).create(vals)
            if create:
                # cek extensi file objective
                files_upload_objective = vals.get('files_upload_objective')
                if files_upload_objective:
                    filename_upload_objective_tokens = str(vals.get('filename_upload_objective')).split('.')
                    if filename_upload_objective_tokens[len(filename_upload_objective_tokens) - 1] != 'pdf':
                        raise Warning('Extensi File yg di upload harus PDF sesuai dengan Extensi yang telah ditentukan')
                    
                    filename_objective = str('tw_business_trip-objective-')+str(create.id)+now+'.'+filename_upload_objective_tokens[len(filename_upload_objective_tokens) - 1]

                    self.env['tw.config.files'].suspend_security().upload_file(filename_objective, files_upload_objective)
                    create.files_upload_objective = False
                    create.filename_upload_objective = filename_objective
                    create.files_objective = False
                    create.filename_objective = filename_objective

                # cek extensi file accommodation
                files_upload_accommodation = vals.get('files_upload_accommodation')
                if files_upload_accommodation:
                    filename_upload_accommodation_tokens = str(vals.get('filename_upload_accommodation')).split('.')
                    if filename_upload_accommodation_tokens[len(filename_upload_accommodation_tokens) - 1] != 'pdf':
                        raise Warning('Extensi File yg di upload harus PDF sesuai dengan Extensi yang telah ditentukan')
                    
                    filename_accommodation = str('tw_business_trip-accommodation-')+str(create.id)+now+'.'+filename_upload_accommodation_tokens[len(filename_upload_accommodation_tokens) - 1]

                    self.env['tw.config.files'].suspend_security().upload_file(filename_accommodation, files_upload_accommodation)
                    create.files_upload_accommodation = False
                    create.filename_upload_accommodation = filename_accommodation
                    create.files_accommodation = False
                    create.filename_accommodation = filename_accommodation

                # upload flight departure
                files_upload_flight_departure = vals.get('files_upload_flight_departure')
                if files_upload_flight_departure:
                    filename_upload_flight_departure_tokens = str(vals.get('filename_upload_flight_departure')).split('.')
                    if filename_upload_flight_departure_tokens[len(filename_upload_flight_departure_tokens) - 1] != 'pdf':
                        raise Warning('Extensi File yg di upload harus PDF sesuai dengan Extensi yang telah ditentukan')

                    filename_flight_departure = str('tw_business_trip-flight_departure-')+str(create.id)+now+'.'+filename_upload_flight_departure_tokens[len(filename_upload_flight_departure_tokens) - 1]

                    self.env['tw.config.files'].suspend_security().upload_file(filename_flight_departure, files_upload_flight_departure)
                    create.files_upload_flight_departure = False
                    create.filename_upload_flight_departure = filename_flight_departure
                    create.files_flight_departure = False
                    create.filename_flight_departure = filename_flight_departure

                # upload flight return
                files_upload_flight_return = vals.get('files_upload_flight_return')
                if files_upload_flight_return:
                    filename_upload_flight_return_tokens = str(vals.get('filename_upload_flight_return')).split('.')
                    if filename_upload_flight_return_tokens[len(filename_upload_flight_return_tokens) - 1] != 'pdf':
                        raise Warning('Extensi File yg di upload harus PDF sesuai dengan Extensi yang telah ditentukan')
                    
                    filename_flight_return = str('tw_business_trip-flight_return-')+str(create.id)+now+'.'+filename_upload_flight_return_tokens[len(filename_upload_flight_return_tokens) - 1]

                    self.env['tw.config.files'].suspend_security().upload_file(filename_flight_return, files_upload_flight_return)
                    create.files_upload_flight_return = False
                    create.filename_upload_flight_return = filename_flight_return
                    create.files_flight_return = False
                    create.filename_flight_return = filename_flight_return
            return create

    def write(self, vals):
        now = date.today().strftime("%Y-%m-%d")

        # cek extensi file objective
        files_upload_objective = vals.get('files_upload_objective')
        if files_upload_objective:
            filename_upload_objective_tokens = str(vals.get('filename_upload_objective')).split('.')
            if filename_upload_objective_tokens[len(filename_upload_objective_tokens) - 1] != 'pdf':
                raise Warning('Extensi File yg di upload harus PDF sesuai dengan Extensi yang telah ditentukan')
            
            filename_objective = str('tw_business_trip-objective-')+str(self.id)+now+'.'+filename_upload_objective_tokens[len(filename_upload_objective_tokens) - 1]

            self.env['tw.config.files'].suspend_security().upload_file(filename_objective, files_upload_objective)
            vals['files_upload_objective'] = False
            vals['filename_upload_objective'] = filename_objective
            vals['files_objective'] = False
            vals['filename_objective'] = filename_objective

        # cek extensi file accommodation
        files_upload_accommodation = vals.get('files_upload_accommodation')
        if files_upload_accommodation:
            filename_upload_accommodation_tokens = str(vals.get('filename_upload_accommodation')).split('.')
            if filename_upload_accommodation_tokens[len(filename_upload_accommodation_tokens) - 1] != 'pdf':
                raise Warning('Extensi File yg di upload harus PDF sesuai dengan Extensi yang telah ditentukan')
            
            filename_accommodation = str('tw_business_trip-accommodation-')+str(self.id)+now+'.'+filename_upload_accommodation_tokens[len(filename_upload_accommodation_tokens) - 1]

            self.env['tw.config.files'].suspend_security().upload_file(filename_accommodation, files_upload_accommodation)
            vals['files_upload_accommodation'] = False
            vals['filename_upload_accommodation'] = filename_accommodation
            vals['files_accommodation'] = False
            vals['filename_accommodation'] = filename_accommodation

        # upload flight departure
        files_upload_flight_departure = vals.get('files_upload_flight_departure')
        if files_upload_flight_departure:
            filename_upload_flight_departure_tokens = str(vals.get('filename_upload_flight_departure')).split('.')
            if filename_upload_flight_departure_tokens[len(filename_upload_flight_departure_tokens) - 1] != 'pdf':
                raise Warning('Extensi File yg di upload harus PDF sesuai dengan Extensi yang telah ditentukan')
            
            filename_flight_departure = str('tw_business_trip-flight_departure-')+str(self.id)+now+'.'+filename_upload_flight_departure_tokens[len(filename_upload_flight_departure_tokens) - 1]
            
            self.env['tw.config.files'].suspend_security().upload_file(filename_flight_departure, files_upload_flight_departure)
            vals['files_upload_flight_departure'] = False
            vals['filename_upload_flight_departure'] = filename_flight_departure
            vals['files_flight_departure'] = False
            vals['filename_flight_departure'] = filename_flight_departure

        # upload flight return
        files_upload_flight_return = vals.get('files_upload_flight_return')
        if files_upload_flight_return:
            filename_upload_flight_return_tokens = str(vals.get('filename_upload_flight_return')).split('.')
            if filename_upload_flight_return_tokens[len(filename_upload_flight_return_tokens) - 1] != 'pdf':
                raise Warning('Extensi File yg di upload harus PDF sesuai dengan Extensi yang telah ditentukan')
            
            filename_flight_return = str('tw_business_trip-flight_return-')+str(self.id)+now+'.'+filename_upload_flight_return_tokens[len(filename_upload_flight_return_tokens) - 1]

            self.env['tw.config.files'].suspend_security().upload_file(filename_flight_return, files_upload_flight_return)
            vals['files_upload_flight_return'] = False
            vals['filename_upload_flight_return'] = filename_flight_return
            vals['files_flight_return'] = False
            vals['filename_flight_return'] = filename_flight_return

        write = super(TwBusinessTrip, self).write(vals)

        for transport_line in self.transportation_line_ids:
            if self.state in ('draft') and transport_line.planning_cost <= 0:
                raise Warning("Perjalanan Dinas harus mengisi biaya planning tranportasi")

        return write
    
    def unlink(self):
        for x in self:
            if x.state != 'draft':
                raise Warning('Business Trip / Perjalan Dinas selain status Draft tidak bisa dihapus!')
        return super(TwBusinessTrip, self).unlink()

    # 13: action methods
    def action_business_trip_list(self):
        tree_id = self.env.ref('tw_business_trip.view_tw_business_trip_list').id
        form_id = self.env.ref('tw_business_trip.view_tw_business_trip_form').id
        search_view_id = self.env.ref('tw_business_trip.view_tw_business_trip_filter').id

        emp = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        cek_group = self.env.user.has_group('tw_business_trip.group_tw_business_trip_all_employee')

        domain = []
        if not cek_group:
            domain += [('pic_id', '=', emp.id)]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Perjalanan Dinas',
            'view_mode': 'list,form',
            'res_model': 'tw.business.trip',
            'domain': domain,
            'views': [(tree_id, 'list'), (form_id, 'form')],
            'search_view_id': search_view_id,
            'context': {'readonly_by_pass': 1, 'search_default_not_done': 1}
        }
    
    def action_create_payment_request(self):
        if self.state == 'arrived':
            if self.actual_food_days == 0:
                raise Warning("Hari Aktual Uang Makan harus diisi terlebih dahulu!")
            if len(self.detail_activity_line_ids) <= 0:
                raise Warning('Perhatian!\nDetail Kegiatan harus diisi.')
            
        for transport in self.transportation_line_ids:
            if transport.actual_cost > 0 and not transport.filename:
                raise Warning("Upload berkas transportasi jika biaya aktual lebih dari 0")
            
        if self.actual_accommodation_cost > 0 and not self.filename_accommodation:
            raise Warning("Upload berkas Penginapan / Akomodasi jika biaya aktual lebih dari 0")
            
        if not self.payment_request_id:
            branch_setting_obj = self.env['tw.branch.setting'].get_branch_setting(self.company_id)
            account_setting_id = branch_setting_obj.account_setting_id

            if not account_setting_id:
                raise Warning(
                    "Account setting is not set for branch %s.\n"
                    "- Go to the Master Branch Setting.\n"
                    "- Set the 'Account Setting' to proceed.\n"
                    "This configuration is required to create accounting entries." 
                    % self.company_id.name
                )
            if not account_setting_id.journal_payment_request_id:
                raise Warning(
                        "Journal Payment Request is not set for branch %s.\n"
                        "- Go to the Account Setting.\n"
                        "- Set the 'Journal Payment Request'.\n"
                        "This configuration is required to create Accrue Payment Request." 
                        % self.company_id.name
                    )
            journal = account_setting_id.journal_payment_request_id
            journal_id = journal.id

            liquidity_amount_currency = -self.actual_amount_total
            liquidity_balance = self.company_id.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            account = journal.default_debit_account_id if liquidity_balance > 0.0 else journal.default_credit_account_id
            account_id = account.id if account else journal.default_account_id.id

            account_uang_saku_id = account_setting_id.account_payment_request_saku_id.id
            account_akomodasi_id = account_setting_id.account_payment_request_akomondasi_id.id

            if self.pic_id.department_id.complete_name == 'Sparepart':
                division = 'Sparepart'
            else:
                division = 'Unit'

            line_dr_ids = []

            if self.actual_food_cost and self.actual_food_cost > 0:
                line_dr_ids.append((0, 0, {
                    'beneficiary_company_id': self.company_id.id,
                    'account_id': account_uang_saku_id,
                    'name': 'Saku Perjalanan Dinas - ' + str(self.name),
                    'amount': self.actual_food_cost,
                }))

            akomodasi_amount = self.actual_amount_total - self.actual_food_cost
            if akomodasi_amount and akomodasi_amount > 0:
                line_dr_ids.append((0, 0, {
                    'beneficiary_company_id': self.company_id.id,
                    'account_id': account_akomodasi_id,
                    'name': 'Akomodasi Perjalanan Dinas - ' + str(self.name),
                    'amount': akomodasi_amount,
                }))
        
            vals = {
                'company_id': self.company_id.id,
                'transaction_type': 'non_recurring',
                'partner_id': self.pic_id.work_contact_id.id,
                'division':division,
                'memo': 'Payment Request Perjalanan Dinas - '+str(self.name),
                'due_date': self.date,
                'type': 'payment_request',
                'payment_type': 'outbound',
                'journal_id': journal_id,
                'account_id': account_id,
                'line_dr_ids': line_dr_ids
            }
            payment_request = self.env['tw.payment.request'].suspend_security().create(vals)
            self.payment_request_id = payment_request.id

        self.suspend_security().write({'state': 'payment_request'})

    def action_view_payment_request(self):
        payment_request_id = self.payment_request_id.id
        if not payment_request_id:
            raise Warning("Payment Request Tidak Ditemukan")
        form_id = self.env.ref('tw_payment_request.view_payment_request_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': ('Payment Request'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'tw.payment.request',
            'res_id': payment_request_id,
            'views': [(form_id, 'form')]
        }
    
    def action_create_supplier_payment(self):
        if not self.supplier_payment_id:
            journal = self.env['account.journal'].sudo().search([
                *self.env['account.journal'].sudo()._check_company_domain(self.company_id),
                ('type', 'in', ['bank', 'cash', 'credit']),
            ], limit=1)

            journal_id = journal.id

            liquidity_amount_currency = -self.actual_amount_total
            liquidity_balance = self.company_id.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
            account = journal.default_debit_account_id if liquidity_balance > 0.0 else journal.default_credit_account_id
            account_id = account.id if account else journal.default_account_id.id

            currency_id = self.company_id.currency_id.id

            if self.pic_id.department_id.complete_name == 'Sparepart':
                division = 'Sparepart'
            else:
                division = 'Unit'

            # Line
            move_line = self.env['account.move.line'].sudo().search([
                ('ref','=',self.payment_request_id.name),
                ('account_id.account_type','=','liability_payable')
            ],limit=1)

            ttype = 'dr' if move_line.credit else 'cr'
            currency_id = journal.company_id.currency_id.id

            if move_line.currency_id and currency_id == move_line.currency_id.id:
                amount_original = abs(move_line.amount_currency)
                amount_unreconciled = abs(move_line.amount_residual_currency)
            else:
                amount_original = move_line.company_id.currency_id._convert(
                    move_line.credit or move_line.debit or 0.0,
                    self.company_id.currency_id,
                    self.company_id,
                    self.date,
                )
                amount_unreconciled = move_line.company_id.currency_id._convert(
                    abs(move_line.amount_residual),
                    self.company_id.currency_id,
                    self.company_id,
                    self.date,
                )
        
            vals = {
                'company_id': self.company_id.id,
                'partner_id': self.pic_id.work_contact_id.id,
                'division':division,
                'type': 'supplier_payment',
                'payment_type': 'outbound',
                'partner_type': 'supplier',
                'amount': self.actual_amount_total,
                'journal_id': journal_id,
                'account_id': account_id,
                'currency_id': currency_id,
                'memo': 'Supplier Payment Perjalanan Dinas - '+str(self.name),
                'line_dr_ids': [
                    (0, 0, {
                        'move_line_id': move_line.id,
                        'name': move_line.move_id.name,
                        'amount_original': amount_original,
                        'amount': amount_unreconciled,
                        'date_original': move_line.date,
                        'date_due': move_line.date_maturity,
                        'amount_unreconciled': amount_unreconciled,
                        'account_id': move_line.account_id.id,
                        'type': ttype,
                        'is_reconciled': True,
                        'currency_id': move_line.currency_id.id or move_line.company_id.currency_id.id,
                    })
                ]
            }
            supplier_payment = self.env['tw.account.payment'].suspend_security().create(vals)
            self.supplier_payment_id = supplier_payment.id

        self.suspend_security().write({'state': 'supplier_payment'})

    def action_view_supplier_payment(self):
        supplier_payment_id = self.supplier_payment_id.id
        if not supplier_payment_id:
            raise Warning("Supplier Payment Tidak Ditemukan")
        form_id = self.env.ref('tw_payment.tw_account_payment_form_view').id
        return {
            'type': 'ir.actions.act_window',
            'name': ('Supplier Payment'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'tw.account.payment',
            'res_id': supplier_payment_id,
            'views': [(form_id, 'form')]
        }
    
    def action_create_advance_payment(self):
        if not self.advance_payment_id:
            employee = self.pic_id

            if employee.department_id.complete_name == 'Sparepart':
                division = 'Sparepart'
            else:
                division = 'Unit'

            branch_setting_obj = self.env['tw.branch.setting'].get_branch_setting(self.company_id)
            account_setting_id = branch_setting_obj.account_setting_id

            if not account_setting_id:
                raise Warning(
                    "Account setting is not set for branch %s.\n"
                    "- Go to the Master Branch Setting.\n"
                    "- Set the 'Account Setting' to proceed.\n"
                    "This configuration is required to create accounting entries." 
                    % self.company_id.name
                )
            
            journal = account_setting_id.journal_avp_id
            if not journal:
                raise Warning(
                    "Journal Advance Payment is not set for branch %s.\n"
                    "- Go to the Account Setting.\n"
                    "- Set the 'Journal Advance Payment'.\n"
                    "This configuration is required to create Advance Payment." 
                    % self.company_id.name
                )
            
            partner = employee.user_id.partner_id if employee.user_id else False
            employee_bank = employee.sudo().bank_account_id
            if not employee_bank:
                raise Warning(_('Informasi Bank pada Employee %s Kosong !\nMohon Hubungi HR untuk Melengkapi Data Di HR Employee.') % employee.name)

            no_rek_tujuan = "[" + employee_bank.acc_number +" " + employee_bank.bank_id.name + "] " + employee.name + " " +  self.company_id.name
        
            vals = {
                'company_id': self.company_id.id,
                'employee_id': employee.id,
                'partner_id': partner.id if partner else False,
                'partner_bank_id': employee_bank.id if employee_bank else False,
                'division': division,
                'type': 'advance_payment',
                'payment_type': 'outbound',
                'amount': self.planning_amount_total,
                'due_date': self.date,
                'journal_id': journal.id,
                'account_avp_id': journal.default_debit_account_id.id,
                'email': getattr(employee, 'work_email', False) or False,
                'account_number': no_rek_tujuan,
                'description': 'Advance Payment Perjalanan Dinas - '+str(self.name)
            }

            advance_payment = self.env['tw.advance.payment'].suspend_security().create(vals)
            self.advance_payment_id = advance_payment.id

        self.suspend_security().write({'state': 'advance_payment'})

    def action_view_advance_payment(self):
        advance_payment_id = self.advance_payment_id.id
        if not advance_payment_id:
            raise Warning("Advance Payment Tidak Ditemukan")
        form_id = self.env.ref('tw_advance_payment.tw_advance_payment_form_view').id
        return {
            'type': 'ir.actions.act_window',
            'name': ('Advance Payment'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'tw.advance.payment',
            'res_id': advance_payment_id,
            'views': [(form_id, 'form')]
        }
    
    def action_create_settlement(self):
        if self.state == 'arrived':
            if self.actual_food_days == 0:
                raise Warning("Hari Aktual Uang Makan harus diisi terlebih dahulu!")
            if len(self.detail_activity_line_ids) <= 0:
                raise Warning('Perhatian!\nDetail Kegiatan harus diisi.')
            
        for transport in self.transportation_line_ids:
            if transport.actual_cost > 0 and not transport.filename:
                raise Warning("Upload berkas transportasi jika biaya aktual lebih dari 0")
            
        if self.actual_accommodation_cost > 0 and not self.filename_accommodation:
            raise Warning("Upload berkas Penginapan / Akomodasi jika biaya aktual lebih dari 0")

        if not self.settlement_id:
            employee = self.pic_id

            if employee.department_id.complete_name == 'Sparepart':
                division = 'Sparepart'
            else:
                division = 'Unit'

            if not self.advance_payment_id:
                raise Warning(_('Advance Payment tidak terhubung dengan activity line ini.'))
            if self.advance_payment_id.state != 'confirm':
                raise Warning(_('Advance Payment harus berada pada status Confirm sebelum membuat Settlement.'))

            branch_conf = self.company_id.branch_setting_id.account_setting_id if self.company_id.branch_setting_id else False
            if not branch_conf or not branch_conf.journal_settlement_id:
                raise Warning(_(f"Konfigurasi Journal Settlement belum dibuat pada Cabang {self.company_id.name} !"))
                
            # Determine settlement type based on gap vs AVP
            actual = float(self.actual_amount_total)
            avp_amount = float(self.advance_payment_id.amount)
            stl_type = False
            if actual < avp_amount:
                stl_type = 'kembali'
            elif actual > avp_amount:
                stl_type = 'tambah'
            
            # Build one settlement line using the settlement journal default debit account
            line_vals = [
                (0, 0, {
                    'company_id': self.company_id.id,
                    'account_id': branch_conf.journal_settlement_id.default_credit_account_id.id,
                    'amount': actual,
                })
            ]
        
            vals = {
                'advance_payment_id': self.advance_payment_id.id,
                'employee_id': employee.id,
                'company_id': self.company_id.id,
                'division': division,
                'amount_avp': self.advance_payment_id.amount,
                'account_avp_id' : self.advance_payment_id.account_avp_id.id,
                'description': 'Settlement Perjalanan Dinas - '+str(self.name),
                'email': getattr(employee, 'work_email', False) or False,
                'type': stl_type,
                'settlement_line_ids': line_vals,
            }

            settlement = self.env['tw.settlement'].suspend_security().create(vals)
            self.settlement_id = settlement.id

        self.suspend_security().write({'state': 'settlement'})

    def action_view_settlement(self):
        settlement_id = self.settlement_id.id
        if not settlement_id:
            raise Warning("Settlement Tidak Ditemukan")
        form_id = self.env.ref('tw_settlement.view_tw_settlement_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': ('Settlement'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'tw.settlement',
            'res_id': settlement_id,
            'views': [(form_id, 'form')]
        }
    
    def action_done(self):
        if self.state == 'arrived':
            if self.actual_food_days == 0:
                raise Warning("Hari Aktual Uang Makan harus diisi terlebih dahulu!")
            if len(self.detail_activity_line_ids) <= 0:
                raise Warning('Perhatian!\nDetail Kegiatan harus diisi.')
            
        for transport in self.transportation_line_ids:
            if transport.actual_cost > 0 and not transport.filename:
                raise Warning("Upload berkas transportasi jika biaya aktual lebih dari 0")
            
        if self.actual_accommodation_cost > 0 and not self.filename_accommodation:
            raise Warning("Upload berkas Penginapan / Akomodasi jika biaya aktual lebih dari 0")

        self.write({
            'state':'done',
            'done_uid': self._uid,
            'done_date': self._get_default_date()
        })

    def action_reject(self):
        form_id = self.env.ref('tw_approval.tw_approval_reject_wizard_form_view').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.approval',
            'name': 'Reject Perjalanan Dinas',
            'views': [(form_id, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'target': 'new',
            'context': {
                'model_name': 'tw.business.trip',
                'update_value': {'state': 'reject'}
            },
        }
    
    def action_revisi_form(self):
        form_id = self.env.ref('tw_business_trip.view_tw_business_trip_revisi_wizard_form').id
        return {
            'name': 'Revisi Perjalanan Dinas',
            'res_model': 'tw.business.trip',
            'type': 'ir.actions.act_window',
            'views': [(form_id, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'target': 'new',
            'res_id': self.id,
            'context': {
                'readonly_by_pass': True,
            },
            'return': True
        }
    
    def action_revisi(self):
        self.write({
            'previous_state': self.state,
            'state': 'revisi',
        })
        
    def action_selesai_revisi(self):
        if self.previous_state:
            self.write({
                'state': self.previous_state,
                'previous_state': False,
            })

    def action_upload_ticket(self):
        self.write({
            'state': 'upload_ticket',
        })

    def action_upload_flight_ticket_form(self):
        form_id = self.env.ref('tw_business_trip.view_tw_business_trip_flight_ticket_wizard_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.business.trip',
            'name': 'Tiket Pesawat Perjalanan Dinas',
            'views': [(form_id, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': {
                'readonly_by_pass': True,
            }
        }
    
    def action_save_flight_ticket(self):
        if self.is_bs == 'tidak':
            if self.is_airplane == 'ya' and self.state == 'upload_ticket':
                self.suspend_security().action_departed()
        else:
            if self.state == 'upload_ticket':
                self.suspend_security().write({'state': 'selesai_upload_ticket'})
    
    def action_departed(self):
        if self.is_airplane == 'ya':
            if not self.filename_flight_departure:
                raise Warning('Tiket Berangkat Harus di Upload terlebih dahulu!')
            if not self.ticket_departure_time:
                raise Warning('Waktu Tiket Berangkat Harus di Isi terlebih dahulu!')
        
        self.suspend_security().write({
            'state': 'departed',
            'actual_departure_date': self.ticket_departure_time if self.ticket_departure_time else self.planning_departure_date
        })

    def action_arrived(self):
        if self.is_airplane == 'ya':
            if not self.filename_flight_return:
                raise Warning('Tiket Kembali Harus di Upload terlebih dahulu!')
            if not self.ticket_return_time:
                raise Warning('Waktu Tiket Kembali Harus di Isi terlebih dahulu!')
            
        self.suspend_security().write({
            'state': 'arrived',
            'actual_arrival_date': self.ticket_return_time if self.ticket_return_time else datetime.now()
        })

    def action_print_business_trip(self):
        active_ids = self.env.context.get('active_ids', [])
        user = self.env['res.users'].sudo().browse(self._uid).name
        datas = {
            'id': self.id,
            'ids': active_ids,
            'model': 'tw.business.trip',
            'form': self.read()[0],
            'user': user,
            'active_ids': [self.id]
        }

        business_trip_pdf, _ = self.env['ir.actions.report']._render_qweb_pdf('tw_business_trip.action_print_business_trip_pdf', data=datas)
        
        merge_pdf = PdfMerger()
        
        if business_trip_pdf:
            pdf_file = io.BytesIO(business_trip_pdf)
            merge_pdf.append(pdf_file)

        # merge all attachment
        if self.files_objective:
            pdf = io.BytesIO(base64.b64decode(self.files_objective))
            if pdf:
                merge_pdf.append(pdf)

        if self.files_accommodation:
            pdf = io.BytesIO(base64.b64decode(self.files_accommodation))
            if pdf:
                merge_pdf.append(pdf)

        for transport in self.transportation_line_ids:
            if transport.files:
                pdf = io.BytesIO(base64.b64decode(transport.files))
                if pdf:
                    merge_pdf.append(pdf)

        # finally merge all
        merged_pdf_file = io.BytesIO()
        merge_pdf.write(merged_pdf_file)
        merge_pdf.close()

        merged_pdf_data = merged_pdf_file.getvalue()
        merged_pdf_data_base64 = base64.b64encode(merged_pdf_data).decode('utf-8')
        filename = 'Print {file_name}.pdf'.format(file_name=self.name.replace('/', '-'))

        if merged_pdf_data_base64 and filename:
            self.suspend_security().write({
                'merged_pdf': merged_pdf_data_base64
            })

        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': f'/web/content/tw.business.trip/{self.id}/merged_pdf/{filename}?download=true'
        }

    # 14: private methods
    def _check_accommodation_cost(self, is_domestic, region, accommodation_cost, accommodation_days, plafon_nominal_domestic, plafon_nominal_asia, plafon_nominal_non_asia, dollar_rate):
        nominal_input, maximal = self._calculate_maximal(is_domestic, region, accommodation_cost, accommodation_days, plafon_nominal_domestic, plafon_nominal_asia, plafon_nominal_non_asia, dollar_rate)
        
        if accommodation_days <= self.planning_accommodation_days and accommodation_cost > self.planning_accommodation_cost:
            raise Warning(
                "Biaya melebihi planning, maksimal untuk {hari} hari adalah {nominal}".format(hari=accommodation_days, nominal="{:,.0f}".format(self.planning_accommodation_cost)))
        
        if nominal_input > maximal:
            raise Warning(
                "Biaya melebihi plafon, maksimal untuk {hari} hari adalah {nominal}".format(hari=accommodation_days, nominal="{:,.0f}".format(maximal)))

    def _calculate_maximal(self, is_domestic, region, cost, days, nominal_domestic, nominal_asia, nominal_non_asia, dollar_rate):
        nominal_input = cost
        maximal = days * nominal_domestic
        if not is_domestic:
            if region == 'asia':
                maximal = days * (nominal_asia * dollar_rate)
            else:
                maximal = days * (nominal_non_asia * dollar_rate)

        return nominal_input, maximal
