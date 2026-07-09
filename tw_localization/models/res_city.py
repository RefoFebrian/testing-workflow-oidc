# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib


class ResCity(models.Model):
    _name = "res.city"
    _description = 'Master City'

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Kab/Kota')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')
    code = fields.Char(string='Code')

    active = fields.Boolean(string='Active',default=True)
    sequence = fields.Integer('sequence')

    # 9: relation fields
    state_id = fields.Many2one(comodel_name='res.country.state',string='Province')
    district_ids = fields.One2many('res.district', 'city_id', 'District')

    # 10: constraints & sql constraints
    @api.onchange('code')
    @api.constrains('code')
    def _check_city_code(self):
        city_obj = self.suspend_security().search([
            ('code','=',self.code)
        ])
        if len(city_obj)>1:
            raise UserError(f'Kota dengan Code {self.code} sudah terbuat.')

    # 11: compute/depends & on change methods

    # 12: override methods

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = vals['name'].upper()
        return super(ResCity,self).create(vals_list)

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(ResCity, self).write(vals)

 
    @api.depends('name','code')
    def _compute_display_name(self):
        for record in self:
            name = record.name
            if record.code:
                name = f"{record.code} - {name} "
            record.display_name = name
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args = ['|',('name', operator, name),('code', operator, name)] + args
        records = self.search_fetch(args, ['display_name'], limit=limit)
        return [(record.id, record.display_name) for record in records.sudo()]
    
    # 13: action methods
    @api.model
    def get_id_by_code(self, code):
        return self.search([('code', '=', code)], limit=1).id

    # 14: private methods