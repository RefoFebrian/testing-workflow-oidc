# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib


class ResDistrict(models.Model):
    _name = "res.district"
    _description = 'Master District'

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Kecamatan', required=True)
    code = fields.Char(string='Code',size=128,required=True)
    active = fields.Boolean(string='Active',default=True)
    sequence = fields.Integer(string='sequence')
    
    # 9: relation fields
    city_id = fields.Many2one('res.city', string='City', required=True)
    state_id = fields.Many2one(related='city_id.state_id',comodel_name='res.country.state', readonly=True, string='Province')
    sub_district_ids = fields.One2many('res.sub.district','district_id',string='Kelurahan', readonly=True)

    # 10: constraints & sql constraints
    @api.onchange('code')
    @api.constrains('code')
    def _check_district_code(self):
        if self.code:
            district_obj = self.suspend_security().search([
                ('code','=',self.code)
            ])
            if len(district_obj)>1:
                raise UserError(f'Kecamatan dengan Code {self.code} sudah terbuat.')
    
    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = vals['name'].upper()
        return super(ResDistrict,self).create(vals_list)

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(ResDistrict, self).write(vals)

    @api.depends('name', 'code')
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
    
    # 13: action methods
    @api.model
    def get_id_by_code(self, code):
        return self.search([('code', '=', code)], limit=1).id
    
    # 14: private methods