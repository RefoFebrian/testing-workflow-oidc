# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TWActMasterType(models.Model):
    _name = "tw.master.activity.type"
    _description = "Master Activity Type"

    # 7: defaults methods

    # 8: fields
    name = fields.Char('Activity Type')
    code = fields.Char('Code')

    is_btl = fields.Boolean('Activity ?')
    is_non_lampung = fields.Boolean('Non Lampung ?')
    is_location = fields.Boolean('Location ?')
    active = fields.Boolean('Active', default=True)
    
    # 9: relation fields

    # 10: constraints & sql constraints
    @api.constrains('code')
    def unique_code_master_activity_type(self):
        for record in self:
            if self.search_count([('code', '=', record.code)]) > 1:
                raise Warning(_(f"Master Activity Type with code ['{record.code}'] must not be duplicate !"))

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self,vals):
        if isinstance(vals, list): 
            vals = vals[0]
        
        vals['name'] = vals['name'].title()
        vals['code'] = vals['code'].upper()
        return super(TWActMasterType,self).create(vals)

    def write(self,vals):
        if vals.get('name',False):
            vals['name'] = vals['name'].title()
        if vals.get('code',False):
            vals['code'] = vals['code'].upper()
        return super(TWActMasterType,self).write(vals)

    # 13: action methods
    def action_activate(self):
        for rec in self:
            rec.active = True

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def action_deactivate(self):
        for rec in self:
            rec.active = False

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    # 14: private methods

