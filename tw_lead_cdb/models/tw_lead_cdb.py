from odoo import models, fields, api
from datetime import date,timedelta,datetime


class twLeadCdb(models.Model):
    _inherit = "tw.lead"
    _description = 'Lead CDB'

    ethnic_group = fields.Char('Suku')
    jabatan = fields.Char('Jabatan')
    address = fields.Char(string='Address')
    rt = fields.Char(string='RT',size=3)
    rw = fields.Char(string='RW',size=3)
    is_sesuai_ktp = fields.Boolean('Sesuai KTP ?',default=True)    
    domisili_street = fields.Char(string='Domisili Address')
    domisili_rt = fields.Char(string='Domisili RT',size=3)
    domisili_rw = fields.Char(string='Domisili RW',size=3)

    email = fields.Char('Email')
    facebook = fields.Char(string='Facebook')
    instagram = fields.Char(string='Instagram')
    twitter = fields.Char(string='Twitter')
    youtube = fields.Char(string='Youtube')
    is_hc = fields.Boolean('Is HC ?')
    discount_hc = fields.Float('Diskon HC')    

    state_id = fields.Many2one(comodel_name='res.country.state',  string='Provinsi',  help='')
    city_id = fields.Many2one(comodel_name='res.city', domain="[('state_id','=',state_id)]",  string='Kabupaten',  help='')
    district_id = fields.Many2one(comodel_name='res.district', domain="[('city_id','=',city_id)]",  string='Kecamatan',  help='')
    sub_district_id = fields.Many2one(comodel_name='res.sub.district', domain="[('district_id','=',district_id)]",  string='Kelurahan',  help='')
    domisili_state_id = fields.Many2one(comodel_name='res.country.state',   string='Domisili provinsi',  help='')
    domisili_city_id = fields.Many2one(comodel_name='res.city', domain="[('state_id','=',domisili_state_id)]", string='Domisili kabupaten',  help='')
    domisili_district_id = fields.Many2one(comodel_name='res.district', domain="[('city_id','=',domisili_city_id)]", string='Domisili kecamatan',  help='')
    domisili_sub_district_id = fields.Many2one(comodel_name='res.sub.district', domain="[('district_id','=',domisili_district_id)]", string='Domisili kelurahan',  help='')

    gender_id = fields.Many2one('tw.selection','Jenis Kelamin',domain=[('type','=','Gender')])
    religion_id = fields.Many2one('tw.selection','Religion',domain=[('type','=','Religion')])
    blood_type_id = fields.Many2one('tw.selection','Golongan Darah',domain=[('type','=','BloodType')])
    education_id = fields.Many2one('tw.selection','Education',domain=[('type','=','Education')])
    job_id = fields.Many2one('tw.selection','Occupation',domain=[('type','=','Occupation')])
    expense_id = fields.Many2one('tw.selection','Expense',domain=[('type','=','Expense')])
    hobby_id = fields.Many2one('tw.selection','Hobby',domain=[('type','=','Hobby')])
    mobile_plan_status_id = fields.Many2one('tw.selection','Status HP',domain=[('type','=','StatusMobilePhone')])
    house_ownership_id = fields.Many2one('tw.selection','Status Rumah',domain=[('type','=','HousingTenure')])
    
    penggunaan_id = fields.Many2one('tw.selection','MotorUtilization',domain=[('type','=','MotorUtilization')])
    pengguna_id = fields.Many2one('tw.selection','MotorUser',domain=[('type','=','MotorUser')])
    merkmotor_id = fields.Many2one('tw.selection','Merk Motor',domain=[('type','=','MotorBrand')])
    jenismotor_id = fields.Many2one('tw.selection','Jenis Motor',domain=[('type','=','MotorType')])