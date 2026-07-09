# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwAssetMutationLine(models.Model):
    _name = "tw.asset.mutation.line"
    _description = "Asset Mutation Line"

    # 7: defaults methods

    # 8: fields
    code = fields.Char('Asset Code',readonly=True) 
    amount = fields.Float('Harga Beli')
    amount_depreciated = fields.Float('Akumulasi Penyusutan')
    book_value = fields.Float('Nilai Buku')
    note = fields.Char('Keterangan')

    # 9: relation fields
    mutation_id = fields.Many2one('tw.asset.mutation','Mutation',ondelete='cascade')
    asset_id = fields.Many2one('account.asset.asset','Asset')
    category_id = fields.Many2one('account.asset.category', 'Asset Category')
    responsible_id = fields.Many2one(related='asset_id.employee_id',string="Penanggung Jawab",store=True)
    location_asset_id = fields.Many2one('stock.location','Lokasi Asset')
    new_employee_user_id = fields.Many2one("hr.employee", string="Pengguna Asset Baru", domain="[('company_id','=',parent.company_request_id)]")
    # 10: constraints & sql constraints
    _sql_constraints = [('unique_mutasi_asset', 'unique(mutation_id,asset_id)', 'Asset tidak boleh duplikat !')]

    # 11: compute/depends & on change methods
    @api.onchange('asset_id')
    def onchange_asset(self):
        self.category_id = False
        self.code = False
        self.amount = False
        self.amount_depreciated = False
        self.book_value = False
        self.location_asset_id = False
        if self.asset_id:
            if self.asset_id.category_id.is_cip:
                raise Warning('Jika Asset Category CIP maka tidak boleh di mutasi!')
            self._check_asset_in_mutation(self.asset_id)
            self.category_id = self.asset_id.category_id.id
            self.code = self.asset_id.code
            self.amount = self.asset_id.value
            self.amount_depreciated = self.asset_id.value - (self.asset_id.salvage_value + self.asset_id.value_residual)
            self.book_value = self.asset_id.value_residual
            self.location_asset_id = self.asset_id.location_id
            self.new_employee_user_id = self.asset_id.employee_user_id.id  # Pre-populate with current user

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _check_asset_in_mutation(self,asset):
        check_asset = self.search([('asset_id', '=', asset.id), ('mutation_id.state', '=', 'open')])
        if check_asset:
            message = ''
            for data in check_asset:
                message += data.mutation_id.name + '\n'
            raise Warning('Asset %s sudah ada di mutation (%s)!' % (asset.name, message))

    
            