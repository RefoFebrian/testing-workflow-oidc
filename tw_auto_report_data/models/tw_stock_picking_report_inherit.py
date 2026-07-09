from odoo import models, fields, api


class TwStockPickingReportInherit(models.TransientModel):
    _inherit = "tw.stock.picking.report"
    
    def generate_stock_picking_report(self, kwargs):
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        division = kwargs.get('division')
        picking_type = kwargs.get('picking_type')
        company_ids = kwargs.get('company_ids')
        product_ids = kwargs.get('product_ids')
        partner_ids = kwargs.get('partner_ids')
        categ_ids = kwargs.get('categ_ids')

        report = self.create({
            'start_date': start_date,
            'end_date': end_date,
            'division': division,
            'picking_type': picking_type,
            'company_ids': company_ids,
            'product_ids': product_ids,
            'partner_ids': partner_ids,
            'categ_ids': categ_ids,
        })
        return report.action_export_report(return_fp = True)