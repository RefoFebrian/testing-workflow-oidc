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
class TwBarcodeAccountAssetInherit(models.Model):
    _inherit = "account.asset.asset"

    is_labelled = fields.Boolean('Is Labelled?')
    labelled_date = fields.Datetime('Labelled on')
    labelled_uid = fields.Many2one('res.users', string='Labelled by')
