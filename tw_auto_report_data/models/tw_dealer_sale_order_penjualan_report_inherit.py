from odoo import models, fields, api

class DealerSaleOrderPenjualanReport(models.TransientModel):
    _inherit = "tw.dealer.sale.order.penjualan.report"

    def generate_penjualan_report(self,kwargs):
        report_type = kwargs.get('report_type')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        state_options = kwargs.get('state_options')
        company_ids = kwargs.get('company_ids')
        finco_ids = kwargs.get('finco_ids')
        product_ids = kwargs.get('product_ids')
        
        report = self.create({
            'report_type': report_type,
            'start_date': start_date,
            'end_date': end_date,
            'state_options': state_options,
            'company_ids': company_ids,
            'finco_ids': finco_ids,
            'product_ids': product_ids,
        })

        return report.action_export_report(return_fp=True)