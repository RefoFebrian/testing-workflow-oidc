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


class TwRentAssetLine(models.Model):
    _name = "tw.asset.lending.line"
    _description = "Rent Asset Line"
    _rec_name = "asset_id"


    # 8: Fields
    asset_code = fields.Char(string='Kode Asset')
    asset_engine_no = fields.Char(string='Nomor Mesin') # Jika aset berupa Unit RT
    asset_chassis_no = fields.Char(string='Nomor Rangka') # Jika aset berupa Unit RT
    asset_year = fields.Char(string='Tahun', size=4)
    
    rent_date = fields.Date(related='rent_id.date', string='Tanggal Pinjam')
    condition_rent = fields.Selection([
        ('good','Good'),
        ('not_good','Not Good'),
    ], string='Kondisi saat dipinjam')
    return_date = fields.Date(string='Tanggal Kembali')
    condition_return = fields.Selection([
        ('good','Good'),
        ('not_good','Not Good'),
    ], string='Kondisi saat dikembalikan')
    note = fields.Char(string='Keterangan')
    state = fields.Selection([
        ('draft','Draft'),
        ('open','Running'),
        ('done','Returned')
    ], string="Status", default="draft")

    # 9: relation Fields
    rent_id = fields.Many2one('tw.asset.lending', string='No Peminjaman', ondelete='cascade')
    # asset_id = fields.Many2one('account.asset.asset', string='Asset', domain="[('company_id','=',parent.inter_company_id), ('state','in',['open','close']), ('category_id.type','=','asset_fixed'), ('rent_id','=',False)]", index=True)
    asset_id = fields.Many2one('account.asset.asset', string='Asset', index=True)
    reason_id = fields.Many2one('tw.master.rent.reason.asset', string='Alasan Pinjam')
    asset_location_id = fields.Many2one('stock.location', string='Lokasi Asset')
    employee_user_id = fields.Many2one("hr.employee",string="Pengguna Asset Baru")
    employee_id = fields.Many2one("hr.employee",string="Pengguna Asset")
    original_employee_user_id = fields.Many2one("hr.employee", string="Pengguna Asset Sebelumnya", help="Stores the original asset user before lending")


    # 10: constraints & sql constraints
    _sql_constraints = [('rent_asset_asset_unique', 'unique(rent_id,asset_id)', 'Asset yang dipinjam tidak boleh duplikat.')]

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.onchange('asset_id')
    def _onchange_asset(self):
        self.asset_code = False
        self.asset_location_id = False
        self.asset_year = False
        if self.asset_id:
            self.asset_code = self.asset_id.code
            self.asset_location_id = self.asset_id.location_id
            if self.asset_id.date:
                self.asset_year = self.asset_id.date.strftime('%Y')

