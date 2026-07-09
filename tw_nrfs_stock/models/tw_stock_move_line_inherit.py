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

class InheritStockMoveLineNrfs(models.Model):
    _inherit = "stock.move.line"
    
    # 7: defaults methods

    # 8: fields
    unit_position_id = fields.Many2one('tw.selection', string='Posisi Unit', domain=[('type','=','PositionUnitExpedition')], help='Position of Unit in Expedition Vehicle')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    
    