from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PaymentRequestTypeLine(models.Model):
    _name = "tw.payment.request.type.line"
    _description = "Payment Request Type Line"

    type_id = fields.Many2one('tw.payment.request.type', string='Type', ondelete='cascade')
    name = fields.Char('Name',index=True)
    account_id = fields.Many2one('account.account','Account')

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            self.name = self.name.upper()
            
    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            val['name'] = val['name'].upper()

        return super().create(vals_list)

    def write(self,vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super().write(vals)    
