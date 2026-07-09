# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools.sql import column_exists, create_column

# 5: local imports

# 6: Import of unknown third party lib


class StockRule(models.Model):
    _inherit = "stock.rule"


    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields += ['dealer_sale_order_line_id', 'partner_id', 'sequence', 'to_refund']
        return fields

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values):
        move_values = super(StockRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values)
        if values.get('location_src_id'):
            move_values['location_id'] = values['location_src_id']
        return move_values

