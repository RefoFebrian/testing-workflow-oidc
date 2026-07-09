# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning    

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwStockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    
    # 14: private methods

    def _prepare_picking_default_values(self):
        vals = super()._prepare_picking_default_values()
        if self.picking_id.work_order_id:
            vals['location_dest_id'] = self.picking_id.location_id.id
        return vals