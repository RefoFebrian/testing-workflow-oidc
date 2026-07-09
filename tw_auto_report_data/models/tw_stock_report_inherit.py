from odoo import models, fields, api

class TwStockReportInherit(models.TransientModel):
    _inherit = "tw.stock.report"
    
    def generate_stock_report_unit(self,kwargs):
        location_ids = kwargs.get('location_ids')
        company_ids = kwargs.get('company_ids')
        product_ids = kwargs.get('product_ids')
        division = kwargs.get('division')
        options_unit = kwargs.get('options_unit')

        report = self.create({
            'location_ids': location_ids,
            'company_ids': company_ids,
            'product_ids': product_ids,
            'division': division,
            'options_unit': options_unit,
        })

        return report.action_export_report(return_fp=True)

    def generate_stock_report_sparepart(self,kwargs):
        location_status = kwargs.get('location_status')
        location_ids = kwargs.get('location_ids')
        company_ids = kwargs.get('company_ids')
        product_ids = kwargs.get('product_ids')
        division = kwargs.get('division')
        options_sparepart = kwargs.get('options_sparepart')

        report = self.create({
            'location_status': location_status,
            'location_ids': location_ids,
            'company_ids': company_ids,
            'product_ids': product_ids,
            'division': division,
            'options_sparepart': options_sparepart,
        })

        return report.action_export_report(return_fp=True)
        
        