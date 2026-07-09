from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.parser import parse



class PrintInvoicePartSales(models.AbstractModel):
    _inherit = "report.tw_part_sales.invoice_part_sales_template"

    def get_dpp(self):
        amount_dpp = 0
        part_sales = self.env['tw.part.sales'].browse(self.env.context.get('active_ids', []))
        for line in part_sales.order_line:
            price = line.price_subtotal
            for tax in line.tax_id:
                price += price * tax.tax_base_amount
            amount_dpp += price
        return round(amount_dpp, 2)

