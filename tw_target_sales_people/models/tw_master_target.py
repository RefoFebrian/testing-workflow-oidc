# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwMasterTarget(models.Model):
    _name = "tw.master.target"
    _description = "Master Target"

    name = fields.Char(string='Name', required=True)