from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.parser import parse


class PrintInvoiceSaleOrder(models.AbstractModel):
    _inherit = "report.tw_sale.invoice_sale_order_template"

    def get_dpp(self):
        amount_dpp = 0
        sale_order = self.env['tw.sale.order'].browse(self.env.context.get('active_ids', []))
        for line in sale_order.order_line:
            price = line.price_subtotal
            for tax in line.tax_id:
                price += price * tax.tax_base_amount
            amount_dpp += price
        return round(amount_dpp, 2)