from odoo import models

class TwWorkOrderPrintWizard(models.TransientModel):
    _inherit = "tw.work.order.print.wizard"

    def action_print_kwitansi(self):
        return self.work_order_ids.action_print_kwitansi()
