# 1: imports of python lib
from datetime import date, datetime, timedelta, time

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class StockRule(models.Model):
    _inherit = "stock.rule"
    # 7: default methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    
    # Update WO Line location, if hotline then use Hotline location
    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values):
        res = super(StockRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_dest_id, name, origin, company_id, values)

        # Check dari transaksi WO
        if values.get('work_order_line_id'):
            work_order_line_id = self.env['tw.work.order.line'].sudo().search([('id','=',values['work_order_line_id'])],limit=1)
            if work_order_line_id:
                res.update({
                    'location_id': work_order_line_id.location_id.id
                })

        # Check dari transaksi PS
        if values.get('part_sales_line_id'):
            part_sales_line_id = self.env['tw.part.sales.line'].sudo().search([('id','=',values['part_sales_line_id'])],limit=1)
            if part_sales_line_id:
                res.update({
                    'location_id': part_sales_line_id.location_id.id
                })
        return res