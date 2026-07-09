# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.osv import expression
from datetime import date

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
import logging
_logger = logging.getLogger(__name__)
# 5: local imports

# 6: Import of unknown third party lib

class InheritStockPickingBatchLineNRFS(models.Model):
    _inherit = "tw.stock.picking.batch.line"

    unit_position_id = fields.Many2one(comodel_name='tw.selection', string='Posisi Unit', domain=[('type','=','PositionUnitExpedition')], help='Position of Unit in Expedition Vehicle')
    
    # 13: action methods
      