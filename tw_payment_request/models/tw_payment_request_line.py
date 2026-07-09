from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountPaymentLineInherit(models.Model):
    _name = "tw.payment.request.line"
    _inherit = "tw.account.payment.line"
    _description = "Payment Request Line"
    
    is_recurring = fields.Boolean('Recurring?', compute='_compute_is_recurring')
    
    payment_id = fields.Many2one('tw.payment.request', 'Payment Request', required=True, ondelete='cascade')
    payment_request_line_type_id = fields.Many2one('tw.payment.request.type.line','Transaksi Detail')
    employee_id = fields.Many2one('hr.employee', string='Employee')

    @api.depends('payment_id', 'payment_id.transaction_type')
    def _compute_is_recurring(self):
        for record in self:
            record.is_recurring = record.payment_id.transaction_type == 'recurring'

    @api.onchange('payment_request_line_type_id')
    def _onchange_payment_request_line_type_id(self):
        if self.payment_request_line_type_id:
            self.account_id = self.payment_request_line_type_id.account_id
        else:
            self.account_id = False
    
    @api.onchange('payment_request_line_type_id','note')
    def onchange_payment_request_name(self):
        if self.payment_request_line_type_id:
            name = str(self.payment_request_line_type_id.name)
            if self.note:
                self.note = self.note.upper()
                name += ' '
                name += self.note
            self.name = name.upper()
        else:
            self.name = False
