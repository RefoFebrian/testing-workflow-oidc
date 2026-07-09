from odoo import models, fields, api

class TwPurchaseOrderReport(models.TransientModel):
    _inherit = "tw.purchase.order.report"

    def generate_purchase_order_report(self,kwargs):
        division = kwargs.get('division')
        state = kwargs.get('state')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        options = kwargs.get('options')
        company_ids = kwargs.get('company_ids')
        product_ids = kwargs.get('product_ids')
        partner_ids = kwargs.get('partner_ids')
        
        report = self.create({
            'division': division,
            'state': state,
            'start_date': start_date,
            'end_date': end_date,
            'options': options,
            'company_ids': company_ids,
            'product_ids': product_ids,
            'partner_ids': partner_ids,
        })
        
        return report.action_generate_report(return_fp=True)