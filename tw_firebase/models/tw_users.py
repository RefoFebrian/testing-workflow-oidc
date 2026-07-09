#!/usr/bin/python
#-*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class ResUsers(models.Model):
    
    _inherit = "res.users"
    _description = "Res Users"

    firebase_user_ids = fields.One2many(comodel_name="tw.firebase.user",  inverse_name="user_id",  string="Firebase users",  help="")


