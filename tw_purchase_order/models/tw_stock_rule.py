# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date 

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwStockRule(models.Model):
    _inherit = "stock.rule"

    def _push_prepare_move_copy_values(self, move_to_copy, new_date):
        new_move_vals = super()._push_prepare_move_copy_values(move_to_copy, new_date)
        if move_to_copy.purchase_line_id:
            new_move_vals.update({
                'purchase_line_id': move_to_copy.purchase_line_id.id,
            })
        return new_move_vals