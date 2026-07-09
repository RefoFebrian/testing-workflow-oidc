from odoo import models, fields, api, _

class ProductType(models.Model):
    _name = "tw.product.type"
    _description = 'Product Type'

    name = fields.Char(string='Product Type', required=True)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    sequence = fields.Integer('Sequence', default=1)

    _sql_constraints = [
       ('name_uniq', 'unique (name, division)', 'This name already exists !')
    ]
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'name' in vals:
                vals['name'] = vals['name'].upper()
        return super(ProductType,self).create(vals_list)

    def write(self,values):
        if 'name' in values:
            values['name'] = values['name'].upper()
        return super(ProductType,self).write(values)