# -*- coding: utf-8 -*-

# 1: imports of python lib
import difflib
import json
import os
import logging
import re

# 2: import of known third party lib
from datetime import date, timedelta, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwProgressiveTax(models.Model):
    _name = "tw.progressive.tax"
    _description = "TW Progressive Tax"
   
    # 8: fields
    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed')
    ]

    def _get_default_date(self):
        return datetime.now()

    @api.depends('company_id')
    def _compute_available_biro_jasa_ids(self):
        for order in self:
            birojasa = []
            if order.company_id:
                birojasa_srch = self.env['tw.branch.setting.birojasa'].suspend_security().search([
                ('branch_setting_id.company_id','=', self.company_id.id)])
                for val in birojasa_srch:
                    if val.biro_jasa_id:
                        birojasa.append(val.biro_jasa_id.id)
                    else:
                        raise Warning(_("Warning!\nBiro Jasa belum di tentukan pada account setting %s") % val.branch_setting_id.name)
            order.available_biro_jasa_ids = birojasa

    def action_confirm_invoice(self):
        for line in self.progressive_tax_line_ids:
            line.create_invoice_line(self.name,self.company_id,self.division,self.date)

        self.suspend_security().write({'state':'confirmed','confirm_uid':self.env.uid,'confirm_date':self._get_default_date()})

    name = fields.Char('No Reference',size=20, readonly=True)
    state = fields.Selection(STATE_SELECTION, 'State', readonly=True, default='draft')
    company_id = fields.Many2one('res.company', string='Branch', required=True, domain=[('is_progressive_tax','=',True)])
    biro_jasa_id = fields.Many2one('res.partner', 'Biro Jasa', domain="[('id', 'in', available_biro_jasa_ids)]")
    available_biro_jasa_ids = fields.Many2many('res.partner',string='Available Biro Jasa',compute='_compute_available_biro_jasa_ids')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options('Unit'),string='Division',default='Unit',required=True,readonly=True)
    date = fields.Date('Tanggal', default = _get_default_date, readonly=True)
    progressive_tax_line_ids = fields.One2many('tw.progressive.tax.line', 'progressive_tax_id', string='Tabel Pajak Progressive')
    confirm_uid = fields.Many2one('res.users', string="Confirmed by")
    confirm_date = fields.Datetime('Confirmed on')

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if not vals['progressive_tax_line_ids']:
                raise Warning(_("Perhatian !\nTidak ada proses pajak progressive"))    
            branch_src = self.env['res.company'].suspend_security().search([('id','=',vals['company_id'])],limit=1)
            vals['name'] = self.env['ir.sequence'].with_company(branch_src).get_sequence_code('PPR', branch_src.code)

            vals['date'] = self._get_default_date()

        progressive_tax_id = super(TwProgressiveTax, self.suspend_security()).create(vals_list)
        return progressive_tax_id

    def write(self,vals):
        res = super(TwProgressiveTax, self.suspend_security()).write(vals)
        if not self.progressive_tax_line_ids:
            raise Warning(_("Perhatian !\nTidak ada proses pajak progressive")) 
        return res

    def unlink(self):
        if self.state != 'draft':
            raise Warning(_("Invalid action !\nTidak bisa dihapus jika state bukan Draft !"))
        return super(TwProgressiveTax, self.suspend_security()).unlink()