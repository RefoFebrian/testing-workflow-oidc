from odoo import models, api, _

class PrintInvoiceDealerSaleOrderInherit(models.AbstractModel):
    _inherit = "report.tw_dealer_sale_order.invoice_dso_template"
    
    def get_total_bbn_amount(self, dso):
        return sum([line.bbn_amount for line in dso.order_line.filtered(lambda l: l.product_id)])
    
    def get_total_pricelist_bbn(self):
        valprice = 0
        dso = self.env['tw.dealer.sale.order'].browse(self.env.context.get('active_ids', []))
        harga_unit = self.get_total(dso)
        total_harga = harga_unit + self.get_total_bbn_amount(dso)

        return total_harga
    
    @api.model
    def _get_report_values(self, docids, data=None):
        values = super()._get_report_values(docids, data=data)
        values.update({
            'total_pricelist_bbn': self.get_total_pricelist_bbn,
            'total_bbn_amount': self.get_total_bbn_amount,
        })
        
        return values