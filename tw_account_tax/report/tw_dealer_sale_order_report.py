from odoo import models, fields, api, _
from datetime import datetime, timedelta
from dateutil.parser import parse

import pytz
class PrintInvoiceDealerSaleOrder(models.AbstractModel):
    _inherit = "report.tw_dealer_sale_order.invoice_dso_template"

    def get_dpp(self):
        amount_dpp = 0
        dso = self.env['tw.dealer.sale.order'].browse(self.env.context.get('active_ids', []))
        for line in dso.order_line:
            price = line.price_subtotal
            for tax in line.tax_id:
                price += price * tax.tax_base_amount
            amount_dpp += price
        return round(amount_dpp, 2)