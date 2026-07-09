from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountPaymentLineInherit(models.Model):
    _name = "tw.advance.payment.line"
    _inherit = "tw.account.payment.line"
    _description = "Advance Payment Line"
    
    payment_id = fields.Many2one('tw.advance.payment', 'Advance Payment', required=True, ondelete='cascade')
    