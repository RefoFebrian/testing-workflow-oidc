from odoo import models, api

class PrintInvoiceDealerSaleOrderVoucher(models.AbstractModel):
    _inherit = "report.tw_dealer_sale_order.invoice_dso_template"

    def get_voucher(self):
        dso = self.env['tw.dealer.sale.order'].browse(self.env.context.get('active_ids', []))
        nominal_voucher = 0
        for line in dso.order_line:
            for vc in line.voucher_ids:
                nominal_voucher += vc.amount
        return nominal_voucher

    @api.model
    def _get_report_values(self, docids, data=None):
        res = super(PrintInvoiceDealerSaleOrderVoucher, self)._get_report_values(docids, data)
        res['total_voucher'] = self.get_voucher
        return res
