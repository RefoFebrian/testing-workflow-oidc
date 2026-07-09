# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib

class ApkVersion(models.Model):
    _name = "tw.app.version"
    _description = 'APK Version'

    name = fields.Char(string='Version')
    app_type_id = fields.Many2one('tw.selection', string="Type", domain="[('type','=','APPType')]")