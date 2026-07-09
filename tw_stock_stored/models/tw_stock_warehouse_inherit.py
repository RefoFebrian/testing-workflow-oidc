# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwStockStoredStockWarehouseInherit(models.Model):
    _inherit = "stock.warehouse"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def _get_picking_type_update_values(self):
        data = super(TwStockStoredStockWarehouseInherit, self)._get_picking_type_update_values()
        temporary_location = self.env.ref('tw_stock_stored.tw_stock_location_temporary_location', raise_if_not_found=False)
        if temporary_location:
            in_type_id = data.get('in_type_id')
            if in_type_id and isinstance(in_type_id, dict):
                in_type_id['temporary_location_id'] = temporary_location.id
        return data

