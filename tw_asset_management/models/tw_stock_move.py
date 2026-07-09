# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command
from odoo.osv import expression

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, OrderedSet, groupby

# 5: local imports

# 6: Import of unknown third party lib
# TODO: DElete this file

class InheritGoodReceiveAsset(models.Model):
    _inherit = "stock.move"

    qty_available = fields.Integer(string='Qty Available')
    
    purchase_line_asset_id = fields.Many2one('purchase.order.asset.line', string='Purchase Line Asset')