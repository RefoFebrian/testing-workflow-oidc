from odoo import models, fields, api

class TwAssetReportInherit(models.TransientModel):
    _inherit = "tw.asset.report"

    def generate_asset_report(self, kwargs):
        option = kwargs.get('option')
        status = kwargs.get('status')
        company_ids = kwargs.get('company_ids')
        category_ids = kwargs.get('category_ids')
       
        report = self.create({
            'option': option,
            'status': status,
            'company_ids': company_ids,
            'category_ids': category_ids,
        })

        return report.action_export_report(return_fp=True)