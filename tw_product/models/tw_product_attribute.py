from odoo import models, fields, api, _

class TWProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    code = fields.Char('Code')

    _sql_constraints = [
        ('value_company_uniq', 'Check(1=1)', 'This attribute value already exists !'),
        ('code_uniq', 'unique (code,attribute_id)', 'This attribute code already exists !')
    ]

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if 'name' in vals:
                vals['name'] = vals['name'].upper()
            if 'code' in vals:
                vals['code'] = vals['code'].upper()
        return super(TWProductAttributeValue,self).create(vals_list) 
    
    def write(self,values):
        if 'name' in values:
            values['name'] = values['name'].upper()
        if 'code' in values:
            values['code'] = values['code'].upper()
        return super(TWProductAttributeValue,self).write(values)
    
    @api.depends('name','code')
    def _compute_display_name(self):
        for record in self:
            name = record.name
            if record.code:
                name = f"[{record.code}] {name} "
            record.display_name = name
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = ['|',('name', operator, name),('code', operator, name)] + args
        records = self.search_fetch(args, ['display_name'], limit=limit)
        return [(record.id, record.display_name) for record in records.sudo()]

    @api.model
    def name_get(self):
        res = []
        for record in self:
            res.append((record.id, f"{record.attribute_id.name} : [{record.code}] {record.name}"))
        return res