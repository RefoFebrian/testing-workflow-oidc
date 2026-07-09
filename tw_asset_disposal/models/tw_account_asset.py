# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
from datetime import datetime

# 2: import of known third party lib
from lxml import etree

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)

class TwAccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    # 7: defaults methods
    
    # 8: fields
    state = fields.Selection(selection_add=[('disposed', 'Disposed')], ondelete={'disposed': 'set default'})
    
    # 9: Relation fields
    disposal_id = fields.Many2one('tw.asset.disposal', string='Disposal')
   