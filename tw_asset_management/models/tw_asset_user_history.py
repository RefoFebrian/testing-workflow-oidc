# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
from datetime import date,datetime

# 2: import of known third party lib
from lxml import etree

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError as Warning
from odoo.osv import expression

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)

class TwAssetUserHistory(models.Model):
    _name = "tw.asset.user.history"
    _description = "History Asset Pengguna"

    # 7: Default Methods
    def _get_default_date(self):
        return datetime.now()
    
    # 8: Fields
    date = fields.Datetime('Date',default=_get_default_date)
    transaction_name = fields.Char('Transaction')

    # 9: Relation Fields
    asset_id = fields.Many2one(comodel_name='account.asset.asset',string='Asset', ondelete='cascade')
    employee_id = fields.Many2one(comodel_name='hr.employee',string='Pengguna Asset')