# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class State(models.Model):
    _inherit = "res.country.state"
    _description = "Res Country State Inherit"
    _order = "sequence"

    # 7: defaults methods
    
    # 8: fields
    code = fields.Char('Code',size=7)
    sequence = fields.Integer('sequence')

    # 9: relation fields
    country_id = fields.Many2one(comodel_name='res.country',string="Country")
    city_ids = fields.One2many('res.city', 'state_id', string='City', readonly=True)

    # 10: constraints & sql constraints
    # TODO: Cause an error when install due to constraints for code and country id in the superclass
    # _sql_constraints = [
    #    ('code_unique', 'unique(code)', 'Kode State tidak boleh ada yang sama.')  
    # ] 
    
    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = vals['name'].title()
        return super(State,self).create(vals_list)

    
    def write(self, vals):
        if vals.get('name'):
            vals['name'] = vals['name'].title()
        return super(State, self).write(vals)

    
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
