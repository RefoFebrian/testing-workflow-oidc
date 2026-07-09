# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwStockOpnameAssetLine(models.Model):
    _name = "tw.stock.opname.asset.line"
    _description = "TW Stock Opname Asset Line"

    opname_id = fields.Many2one('tw.stock.opname.asset','Stock Opname',ondelete='cascade')
    
    code = fields.Char('Kode Asset')
    register_no = fields.Char('Register No')

    name = fields.Char('Nama Asset')
    category = fields.Char('Kategory')
    description = fields.Char('Description')
    
    physical_validation = fields.Selection([
        ('fisik_ada','Fisik Ada'),
        ('fisik_tidak_ada','Fisik Tidak Ada')],string='Validasi Fisik')
    physical_condition = fields.Selection([
        ('Baik','Baik'),
        ('Rusak','Rusak'),
        ('Mati','Mati'),
        ('-','-')],string="Kondisi Fisik Asset")
    asset_status = fields.Selection([
        ('di_cabang','Di Cabang'),
        ('dipinjam_pic','Dipinjam PIC'),
        ('tidak_diketahui','Tidak Diketahui'),],string='Status Asset')


    engine_no = fields.Char('No Mesin')
    description = fields.Char('Keterangan')
    upload_image = fields.Binary(string='Upload Gambar', help="Select image here")
    filename_image = fields.Char(string='Filename Gambar')
    
    pic_validation_id = fields.Many2one('hr.employee','PIC Asset')
    validation_location_id = fields.Many2one('stock.location','Lokasi Validasi')

    # Compute / Onchange method

    @api.model_create_multi
    def create(self,vals_list):
        return super(TwStockOpnameAssetLine,self).create(vals_list)

    def write(self,vals):
        return super(TwStockOpnameAssetLine,self).write(vals)

    @api.onchange('category')
    def onchange_category(self):
        if self.category:
            if self.category != 'V':
                self.engine_no = '-'

    @api.onchange('engine_no','physical_validation','asset_status')
    def onchange_engine_no(self):
        if self.engine_no or self.physical_validation or self.asset_status:
            if (self.physical_validation != 'fisik_tidak_ada' and self.asset_status != 'tidak_diketahui' and self.engine_no and self.engine_no != '-' and len(self.engine_no) != 12):
                self.engine_no = False
                raise Warning('No Mesin harus 12 digit !')
            elif self.physical_validation == 'fisik_tidak_ada' or self.asset_status == 'tidak_diketahui':
                self.engine_no = '-' 
    
    @api.onchange('physical_validation','asset_status')
    def onchange_validasi_lokasi(self):
        self.pic_validation_id = False
        self.physical_condition = False
        self.engine_no = False
        if self.physical_validation or self.asset_status:
            if self.physical_validation == 'fisik_tidak_ada' or self.asset_status == 'tidak_diketahui':
                self.engine_no = '-' 