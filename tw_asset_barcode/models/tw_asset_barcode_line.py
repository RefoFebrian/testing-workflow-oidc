# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwBarcodeLabelAssetLine(models.TransientModel):
    _name = "tw.barcode.label.asset.line"
    _description = 'TW Barcode Labelling Asset Line'

    label_id = fields.Many2one('tw.barcode.label.asset')
    asset_id = fields.Many2one('account.asset.asset', string='Asset Account')
    asset_name = fields.Char('Asset Description')
    asset_number = fields.Char('Asset Register Number')
    asset_code = fields.Char('Asset Code')
    asset_category = fields.Char('Asset Category')
    purchase_date = fields.Datetime('Effective Date')
    division = fields.Char('Division')
    partner = fields.Char('Partner Asset')
    is_print = fields.Boolean('Print?', default=False)
    qr_code_base64 = fields.Text(string="QR Code (Base64)")
    status = fields.Char('Status')