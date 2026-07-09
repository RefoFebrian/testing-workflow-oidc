# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning    

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwStockReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    
    # 14: private methods

    def _prepare_move_default_values(self, new_picking):
        vals = super()._prepare_move_default_values(new_picking)
        if self.move_id.picking_id.work_order_id:
            vals['location_dest_id'] = self.move_id.location_id.id
        return vals