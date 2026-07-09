from odoo import models, fields, api, _

class InheritAccountAssetAssetRentReturn(models.Model):
    _inherit = "account.asset.asset"

    rent_id = fields.Many2one('tw.asset.lending','No Peminjaman')
    lending_asset_ids = fields.One2many('tw.asset.lending.line', 'asset_id', string='History Peminjaman')