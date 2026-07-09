# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports
import logging

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)

class TwReturnAssetLine(models.Model):
    _name = "tw.asset.return.line"
    _description = "Return Asset Line"


    # 8: Fields
    asset_code = fields.Char(string='Kode Aset')
    asset_engine_no = fields.Char(string='Nomor Mesin') # Jika aset berupa Unit RT
    asset_chassis_no = fields.Char(string='Nomor Rangka') # Jika aset berupa Unit RT
    asset_year = fields.Char(string='Tahun', size=4)
    rent_date = fields.Date(string='Tanggal Pinjam')
    return_date = fields.Date(string='Tanggal Kembali')
    condition_rent = fields.Selection([
        ('good','Good'),
        ('not_good','Not Good'),
    ], string='Kondisi saat Dipinjam')
    condition_return = fields.Selection([
        ('good','Good'),
        ('not_good','Not Good'),
    ], string='Kondisi saat Dikembalikan')
    note = fields.Text(string='Keterangan')


    # 9: Relation Fields
    return_id = fields.Many2one('tw.asset.return', string='No Pengembalian', ondelete='cascade')
    rent_id = fields.Many2one('tw.asset.lending', string='No Peminjaman', domain="[('company_id','=',parent.company_id), ('state','in',['open','partially_returned'])]")
    rent_line_id = fields.Many2one('tw.asset.lending.line', string='Aset yang Dipinjam', domain="[('rent_id','=',rent_id), ('state','in',['open'])]")
    asset_id = fields.Many2one('account.asset.asset', string='Aset')
    asset_location_id = fields.Many2one('stock.location', string='Lokasi Aset')
    employee_user_id = fields.Many2one("hr.employee",string="Pengguna Asset")

    _sql_constraints = [('return_asset_unique', 'unique(return_id,asset_id)', 'Aset yang dikembalikan tidak boleh duplikat.')]

    @api.onchange('rent_line_id')
    def _onchange_asset(self):
        self.asset_id = False
        self.asset_code = False
        self.asset_location_id = False
        self.asset_year = False
        self.asset_engine_no = False
        self.asset_chassis_no = False
        self.rent_date = False
        self.condition_rent = False
        self.condition_return = False
        self.note = False
        if self.rent_line_id:
            self.asset_id = self.rent_line_id.asset_id.id
            self.asset_code = self.rent_line_id.asset_code
            self.asset_location_id = self.rent_line_id.asset_location_id.id
            self.asset_year = self.rent_line_id.asset_year
            self.asset_engine_no = self.rent_line_id.asset_engine_no
            self.asset_chassis_no = self.rent_line_id.asset_chassis_no
            self.rent_date = self.rent_line_id.rent_date
            self.condition_rent = self.rent_line_id.condition_rent
            self.condition_return = self.rent_line_id.condition_return
            self.note = self.rent_line_id.note
            self.employee_user_id = self.rent_line_id.asset_id.employee_user_id.id