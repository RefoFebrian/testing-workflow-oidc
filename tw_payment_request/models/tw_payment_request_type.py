from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PaymentRequestType(models.Model):
    _name = "tw.payment.request.type"
    _description = "Payment Request Type"

    name = fields.Char('Name',index=True)
    active = fields.Boolean('Active', default=True)
    
    line_ids = fields.One2many('tw.payment.request.type.line', 'type_id', string='Lines')

    @api.onchange('name')
    def onchange_name(self):
        if self.name:
            self.name = self.name.upper()
            
    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            val['name'] = val['name'].upper()
        create = super().create(vals_list)
        create.check_duplicate()
        return create

    def write(self,vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        write = super().write(vals)
        self.check_duplicate()
        return write
    
    def unlink(self):
        for type in self:
            type.active = False
        return True
    
    def check_duplicate(self):
        existed_name = []
        for line in self.line_ids:
            if line.name in existed_name:
                raise UserError('Duplicate name found in payment request type line')
            existed_name.append(line.name)
