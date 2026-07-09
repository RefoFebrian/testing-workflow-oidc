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

class TwStockOpnameAssetOther(models.Model):
    _name = "tw.stock.opname.asset.other"
    _description = "TW Stock Opname Asset Other"
    
    opname_id = fields.Many2one('tw.stock.opname.asset','Stock Opname',ondelete='cascade')
    
    name = fields.Char('Nama Asset')
  
    physical_location = fields.Selection([
        ('Di Cabang','Di Cabang'),
        ('Dipinjam PIC','Dipinjam PIC'),
        ('Tidak diketahui','Tidak diketahui'),
        ('Hilang','Hilang'),
        ('Tidak Ada','Tidak Ada'),
        ('-','-')],string='Status Asset')

    physical_condition = fields.Selection([
        ('Baik','Baik'),
        ('Rusak','Rusak'),
        ('Mati','Mati'),
        ('-','-')],string="Kondisi Fisik Asset")

    engine_no = fields.Char('No Mesin')
    description = fields.Char('Keterangan')
    
    pic_asset_id = fields.Many2one('hr.employee','PIC Asset')