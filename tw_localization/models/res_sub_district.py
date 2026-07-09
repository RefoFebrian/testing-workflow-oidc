# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib

class ResSubDistrict(models.Model):
    _name = "res.sub.district"
    _description = 'Master Sub-District'
    _order = "sequence"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Kelurahan')
    zip_code = fields.Char(string='Zip Code', size=10, required=True) 
    code = fields.Char('Code', size=10, required=True) 
    sequence = fields.Integer('sequence')
    active = fields.Boolean(string='Active', default=True)

    # 9: relation fields
    district_id = fields.Many2one('res.district', 'Kecamatan', required=True)
    city_id = fields.Many2one(related='district_id.city_id', comodel_name='res.city', readonly=True, string='Kab/Kota')
    state_id = fields.Many2one(related='district_id.state_id', comodel_name='res.country.state', readonly=True, string='Provinsi')

    # 10: constraints & sql constraints
    @api.onchange('code')
    @api.constrains('code')
    def _check_sub_district_code(self):
        sub_district_obj = self.suspend_security().search([
            ('code','=',self.code)
        ])
        if len(sub_district_obj)>1:
            raise UserError(f'Kelurahan dengan Code {self.code} sudah terbuat.')

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = vals['name'].upper()
        return super(ResSubDistrict,self).create(vals_list)

    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(ResSubDistrict, self).write(vals)

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
    
    # 13: action methods
    @api.model
    def get_id_by_code(self, code):
        return self.search([('code', '=', code)], limit=1).id

    # 14: private methods