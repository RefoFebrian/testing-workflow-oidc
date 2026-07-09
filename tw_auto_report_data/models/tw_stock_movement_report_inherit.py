from odoo import models, fields, api


class StockMovementReport(models.TransientModel):
    _inherit = "tw.stock.movement.report"

    def generate_stock_movement_report(self,kwargs):
        options = kwargs.get('options')
        division = kwargs.get('division')
        picking_type = kwargs.get('picking_type')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        company_ids = kwargs.get('company_ids')
        categ_ids = kwargs.get('categ_ids')
        product_ids = kwargs.get('product_ids')
        partner_ids = kwargs.get('partner_ids')

        report = self.create({
            'options': options,
            'division': division,
            'picking_type': picking_type,
            'start_date': start_date,
            'end_date': end_date,
            'company_ids': company_ids,
            'categ_ids': categ_ids,
            'product_ids': product_ids,
            'partner_ids': partner_ids,
        })

        return report.action_export_report(return_fp=True)

    