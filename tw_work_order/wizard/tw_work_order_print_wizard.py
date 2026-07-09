from odoo import models, fields

class TwWorkOrderPrintWizard(models.TransientModel):
    _name = "tw.work.order.print.wizard"
    _description = "Work Order Print Options Wizard"

    work_order_ids = fields.Many2many('tw.work.order', string="Work Orders", default=lambda self: self.env.context.get('active_ids'))
    
    # We use a computed state based on the first record just for the UI logic to avoid errors, 
    # but actual print methods will apply to all valid records
    state = fields.Selection(related='work_order_ids.state', readonly=True)

    def action_print_wo_thermal(self):
        return self.work_order_ids.action_print_wo_thermal()

    def action_print_picking_wo_thermal(self):
        return self.work_order_ids.action_print_picking_wo_thermal()

    def action_print_wo_thermal_invoice(self):
        return self.work_order_ids.action_print_wo_thermal_invoice()
    
    def action_print_wo_invoice(self):
        return self.work_order_ids.action_print_wo_invoice()

    def action_print_wo(self):
        return self.work_order_ids.action_print_wo()

