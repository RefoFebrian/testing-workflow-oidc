from odoo import models, fields, api, _


class PrintWorkOrderInvoiceInherit(models.AbstractModel):
    _inherit = "report.tw_work_order.print_wo_invoice"

    def get_total_voucher(self):
        wo_obj = self.env['tw.work.order'].suspend_security().browse(self.env.context.get('active_ids', []))
        total_voucher = 0
        if wo_obj.sales_voucher_ids:
            total_voucher = sum([wo_voc.used_amount or 0 for wo_voc in wo_obj.sales_voucher_ids])
            
        return total_voucher
    
    @api.model
    def _get_report_values(self, docids, data=None):
        report_values = super()._get_report_values(docids, data=data)
        if isinstance(report_values, dict):
            report_values.update({
                'total_voucher': self.get_total_voucher
            })
        
        return report_values