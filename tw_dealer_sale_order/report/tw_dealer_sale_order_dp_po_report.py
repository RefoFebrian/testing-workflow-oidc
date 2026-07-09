from odoo import models, api, _
from . import fungsi_terbilang


class PrintDpPoDealerSaleOrder(models.AbstractModel):
    _name = "report.tw_dealer_sale_order.dp_po_dso_template"
    _description = "Dealer Sale Order Report DP PO"
    
    def time_date(self, date):
        return date.strftime("%d-%m-%Y")
    
    def terbilang(self, amount):
        return fungsi_terbilang.terbilang(amount, "idr", 'id')
    
    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['tw.dealer.sale.order'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'tw.dealer.sale.order',
            'docs': docs,
            'time_date': self.time_date,
            'terbilang': self.terbilang,
        }