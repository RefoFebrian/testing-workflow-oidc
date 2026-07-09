from odoo import models, fields, api

class TwReportOrderFulfillment(models.TransientModel):
    _inherit = "tw.report.order.fulfillment.wizard"

    def generate_order_fulfillment_report(self, kwargs):
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        trx_type = kwargs.get('trx_type')
        division = kwargs.get('division')
        company_ids = kwargs.get('company_ids')

        report = self.create({
            'start_date': start_date,
            'end_date': end_date,
            'trx_type': trx_type,
            'division': division,
            'company_ids': company_ids,
        })

        return report.excel_report(return_fp=True)
        