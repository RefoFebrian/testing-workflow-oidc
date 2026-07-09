from odoo import models, fields, api

class TwMainDealerSalesReport(models.TransientModel):
    _inherit = "tw.main.dealer.sales.report"

    def generate_main_dealer_sales_report(self,kwargs):
        division = kwargs.get('division')
        product_ids = kwargs.get('product_ids')
        options = kwargs.get('options')
        start_date = kwargs.get('start_date')
        end_date = kwargs.get('end_date')
        state = kwargs.get('state')
        branch_ids = kwargs.get('branch_ids')
        dealer_ids = kwargs.get('dealer_ids')
        type_file = kwargs.get('type_file')
        

        report = self.create({
            'division': division,
            'product_ids': product_ids,
            'options': options,
            'start_date': start_date,
            'end_date': end_date,
            'state': state,
            'company_ids': branch_ids,
            'dealer_ids': dealer_ids,
            'type_file': type_file,
        })
        
        return report._print_excel_report(return_fp=True)