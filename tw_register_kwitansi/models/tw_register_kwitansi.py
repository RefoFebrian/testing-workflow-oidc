# -*- coding: utf-8 -*-

# 1: imports of python lib
import itertools
from lxml import etree
from datetime import datetime, timedelta
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, RedirectWarning
import odoo.addons.decimal_precision as dp

# 5: local imports

# 6: Import of unknown third party lib
class TWRegisterKwitansi(models.Model):
    
    _name = "tw.register.kwitansi"
    _description = "Register Kwitansi Dealer"
    _order = "id asc"

    def _get_default_date(self):
        return self.env['res.company'].get_default_date()
            
    name = fields.Char(string='Register Kwitansi',compute='_compute_name',store=True)
    date = fields.Date(string='Date',required=True,default=_get_default_date)
    company_id = fields.Many2one('res.company', string ='Branch',required=True)
    prefix = fields.Char(string='Prefix',required=True)
    is_ekwitansi = fields.Boolean('Is E-Kwitansi?')
    nomor_awal = fields.Integer(string ='Nomor Awal',required=True,default=1)
    nomor_akhir = fields.Integer(string ='Nomor Akhir',required=True,default=2)
    padding = fields.Integer(string='Padding',required=True,default=8)
    state = fields.Selection([
        ('draft','Draft'),
        ('posted','Posted'),
    ],default='draft')
    register_kwitansi_ids = fields.One2many('tw.register.kwitansi.line','register_kwitansi_id', string='Kwitansi Line',readonly=True)
    confirm_uid = fields.Many2one('res.users',string="Posted by")
    confirm_date = fields.Datetime('Posted on')

    @api.depends('company_id','is_ekwitansi')
    def _compute_name(self):
        for item in self:
            if item.id and not item.name:
                code = 'REG/KWT'
                if item.is_ekwitansi:
                    code = 'REG/EKTW'
                item.name = self.env['ir.sequence'].get_sequence_code(code, str(item.company_id.code))

    def action_generate_ekwitansi(self):
        vals_ekwt = []
        padding ="{0:0"+str(self.padding)+"d}"
        prefix = self.prefix if self.prefix else ''
        for number in range(self.nomor_awal,self.nomor_akhir+1):
            vals_ekwt.append([0,0,{
                'name': prefix + padding.format(number),
                'state': 'open',
                'company_id': self.company_id.id,
                'type': 'ekwitansi'
            }])
        self.write({
            'date':datetime.today(),
            'register_kwitansi_ids': vals_ekwt,
            'state':'posted',
            'confirm_uid':self._uid,
            'confirm_date':datetime.now()
        })
        return True

    def action_post(self):
        if not self.is_ekwitansi:
            vals = []
            padding ="{0:0"+str(self.padding)+"d}"
            prefix = self.prefix if self.prefix else ''
            for number in range(self.nomor_awal,self.nomor_akhir+1):
                vals.append([0,0,{
                'name': prefix + padding.format(number),
                    'state': 'open',
                    'company_id': self.company_id.id,
                    'type': 'kwitansi'
                }])
            self.write({
                'date':datetime.today(),
                'register_kwitansi_ids': vals,
                'state':'posted',
                'confirm_uid':self._uid,
                'confirm_date':datetime.now()
            })
        else:
            self.action_generate_ekwitansi()
        return True
   
    @api.onchange('nomor_awal','nomor_akhir','company_id','is_ekwitansi')
    def nomor_awal_change(self):
        if self.nomor_awal <= 0:
            self.nomor_awal = 1
            self.nomor_akhir = self.nomor_awal+1
            return {'warning':{'title':'Perhatian!','message':'Nomor awal harus > 0'}}
        
        if self.nomor_akhir < self.nomor_awal:
            self.nomor_akhir = self.nomor_awal+1
        
        if self.padding <=0:
            return {'warning':{'title':'Perhatian!','message':'Padding harus > 0'}}
        
        if self.company_id:
            self.prefix = self.prefix = self.company_id.code+"/KWT/"

        if self.is_ekwitansi:
            if not self.prefix:
                raise Warning('Silahkan isi Prefix Terlebih dahulu.')
            self.prefix = self.prefix = self.company_id.code+"/EKWT/"
          
    def unlink(self):
        for item in self:
            if item.state != 'draft':
                raise Warning(('Perhatian !'), ("Register Kwitansi dan E-Kwitansi sudah diproses, data tidak bisa didelete !"))
        return super(TWRegisterKwitansi, self).unlink() 
            
class TWRegisterKwitansiLine(models.Model):
    _name = "tw.register.kwitansi.line"
    _description = "Register Kwitansi Dealer Line"
        
    register_kwitansi_id = fields.Many2one('tw.register.kwitansi')
    name = fields.Char(string='No. Register')
    transaction_id = fields.Integer(string='Transaction ID')
    model_name = fields.Char(string='Model Name')
    company_id = fields.Many2one('res.company',string='Branch')
    payment_id = fields.Many2one('tw.account.payment',string = 'Payment No.')
    state = fields.Selection([
        ('open','Open'),
        ('printed','Printed'),
        ('cancel','Canceled'),
    ],default='open')
    type = fields.Selection([
        ('kwitansi', 'Kwitansi'),
        ('ekwitansi', 'E-Kwitansi'),
    ], string='Type')
    reason = fields.Char('Reason')
    
    _sql_constraints = [
        ('unique_nomor_register', 'unique(name)', 'Nomor register sudah pernah dibuat !'),
    ]

    def get_available_ekwitansi(self,model_name,transaction_id):
        model_obj = self.env[model_name].suspend_security().browse(transaction_id)
        if not model_obj:
            raise Warning("Model %s tidak ada" % model_name)
        ekwitansi = self.env['tw.register.kwitansi.line'].search([
            ('type', '=', 'ekwitansi'),
            ('company_id', '=', model_obj.company_id),
            ('state', '=', 'open')], limit=1, order="name ASC")
        
        if not kwitansi:
            raise Warning("Kwitansi for %s is not available!" % model_obj.company_id.name)
        
        return kwitansi

    def get_available_kwitansi(self,model_name,transaction_id):
        model_obj = self.env[model_name].suspend_security().browse(transaction_id)
        kwitansi = self.env['tw.register.kwitansi.line'].search([
            ('type', '=', 'kwitansi'),
            ('company_id', '=', model_obj.company_id),
            ('state', '=', 'open')], limit=1, order="name ASC")
        
        if not ekwitansi:
            raise Warning("eKwitansi for %s is not available!" % model_obj.company_id.name)
        
        return ekwitansi

    def cancel_register_kwitansi(self,model_name,transaction_id,reason):
        kwitansi_obj = self.search([
            ('model_name','=',model_name),
            ('transaction_id','=',transaction_id)
        ], limit=1)
        if kwitansi_obj:
            kwitansi_obj.suspend_security().write({
                'state':'cancel',
                'reason':reason
            })
        else:
            raise Warning("Transaksi ini belum memiliki Register Kwitansi.")
