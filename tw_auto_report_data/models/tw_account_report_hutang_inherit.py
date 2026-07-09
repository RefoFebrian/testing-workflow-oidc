from odoo import models, fields, api

class TwAccountReportHutang(models.TransientModel):
    _inherit = "tw.account.report.hutang"

    def generate_account_hutang_report(self,kwargs):
        option = kwargs.get('option')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        status = kwargs.get('status')
        date = kwargs.get('date')

        report = self.create({
            'option': option,
            'start_date': start_date,
            'end_date': end_date,
            'status': status,
            'date': date,
        })
        return report._get_detail_report(return_fp=True)
        
        