from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountPaymentLineInherit(models.Model):
    _name = "tw.other.receivable.line"
    _inherit = "tw.account.payment.line"
    _description = "Other Receivable Line"
    
    payment_id = fields.Many2one('tw.other.receivable', 'Other Receivable', required=True, ondelete='cascade')
    