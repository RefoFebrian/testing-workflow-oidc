#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class FirebaseContentTemplate(models.Model):

    _name = "tw.firebase.content.template"
    _description = "Firebase Content Template"
    _order = "name desc"

    # 7: defaults methods

    # 8: fields
    name = fields.Char( required=True, string="Name",  help="")
    content = fields.Html( string="Content",  help="")

    # 8: relation fields

    # 9: constraints & sql constraints

    # 10: compute/depends & on change methods

    # 11: override methods
    # 
    # def name_get(self, context=None):
        # return super(FirebaseContentTemplate, self).name_get(context)

    # @api.model
    # def name_search(self, name='', args=None, operator='ilike', limit=100):
        # return super(FirebaseContentTemplate, self).name_search(name, args, operator, limit)

    # @api.model
    # def create(self, vals):
        # return super(FirebaseContentTemplate, self).create(vals)

    # 
    # def write(self, vals):
        # return super(FirebaseContentTemplate, self).write(vals)

    # 
    # def unlink(self):
        # for x in self:
            # if x.state != 'draft':
                # raise Warning('Perhatian!\nData tidak bisa dihapus.')
                # return super(FirebaseContentTemplate, self).unlink()

    # 
    # def copy(self):
        # raise Warning('Perhatian!\nData tidak bisa diduplikasi.')
        # return super(FirebaseContentTemplate, self).copy()


    # 12: action methods

    # 13: private methods

