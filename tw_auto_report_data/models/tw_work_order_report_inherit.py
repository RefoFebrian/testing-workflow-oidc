from odoo import models, fields, api

class TwAutoReportWorkshop(models.TransientModel):
    _inherit = "tw.report.workshop.wizard"

    def generate_workshop_report(self,kwargs):
        options = kwargs.get('options')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        state = kwargs.get('state')
        company_ids = kwargs.get('company_ids')
        product_ids = kwargs.get('product_ids')
        partner_ids = kwargs.get('partner_ids')
        
        report = self.create({
            'options': options,
            'start_date': start_date,
            'end_date': end_date,
            'state': state,
            'company_ids': company_ids,
            'product_ids': product_ids,
            'partner_ids': partner_ids,
        })

        data = report._print_excel_report()
        return self.env['web.report'].sudo().generate_report('Report Work Order',data, data_summary_header=False, start_date=start_date, end_date=end_date, return_fp=True)
