# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models


# 4:  imports from odoo modules


class SaleStockRule(models.Model):
    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        fields = super(SaleStockRule, self)._get_custom_move_fields()
        fields += ['sale_order_line_id']
        return fields
