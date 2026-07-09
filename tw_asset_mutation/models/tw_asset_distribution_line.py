# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwAssetDistributionLine(models.Model):
    _name = "tw.asset.distribution.line"
    _description = "Asset Distribution Line"

    # 7: defaults methods

    # 8: fields
    
    code = fields.Char('Asset Code') 
    amount = fields.Float('Harga Beli')
    amount_depreciated = fields.Float('Akumulasi Penyusutan')
    book_value = fields.Float('Nilai Buku')
    note = fields.Char('Keterangan')
    
    # 9: relation fields
    mutation_id = fields.Many2one('tw.asset.distribution','Mutation',ondelete='cascade')
    product_id = fields.Many2one(related='asset_id.product_id',store=True)
    asset_adjusment_id = fields.Many2one('tw.asset.adjustment','Asset Adjusment')
    location_asset_id = fields.Many2one('stock.location','Lokasi Asset',domain="[('type_id.value','=','asset'),('company_id','=',parent.company_id)]")
    location_source_id = fields.Many2one(related='asset_id.location_id', string='Lokasi Asal Asset', store=True, readonly=True)
    location_mutation_id = fields.Many2one('stock.location','Lokasi Mutasi',domain="[('type_id.value','=','asset')]")
    location_dest_id = fields.Many2one('stock.location','Lokasi Tujuan')
    asset_id = fields.Many2one('account.asset.asset','Asset')
    employee_user_id = fields.Many2one("hr.employee", string="Pengguna Asset Lama")
    new_employee_user_id = fields.Many2one("hr.employee", string="Pengguna Asset Baru")
    category_id = fields.Many2one('account.asset.category', 'Asset Category')

    # 10: constraints & sql constraints
    _sql_constraints = [('unique_mutasi_asset', 'unique(mutation_id,asset_id)', 'Asset tidak boleh duplikat !')]

    # 11: compute/depends & on change methods
    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        for record in self:
            record.category_id = False
            record.code = False
            record.amount = False
            record.amount_depreciated = False
            record.book_value = False
            record.note = False
            record.product_id = False
            if record.asset_id:
                record.category_id = record.asset_id.category_id.id
                record.code = record.asset_id.code
                record.amount = record.asset_id.value
                record.amount_depreciated = record.asset_id.value - (record.asset_id.salvage_value + record.asset_id.value_residual)
                record.book_value = record.asset_id.value
                record.note = record.asset_id.note
                record.product_id = record.asset_id.product_id.id
                record.location_asset_id = record.asset_id.location_id
                record.employee_user_id = record.asset_id.employee_user_id.id
