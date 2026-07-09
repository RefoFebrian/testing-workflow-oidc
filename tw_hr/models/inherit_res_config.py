# 1: imports of python lib
import threading

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError

# 5: local imports

# 6: Import of unknown third party lib

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # 7: defaults methods

    # 8: fields
    # TODO: untuk bahan diskusi
    """
    jika employee butuh branch tinggal ceklis Branches pada menu Settings - > Employee
    apakah secara fungtional / teknis bagus untuk diterapkan seperti itu?

    secara teknis, jika ceklis maka akan melakukan install pada module TW HR Branch 
    dan jika unceklis maka akan melakukan uninstall pada module tsb juga.
    """
    module_tw_hr_branch = fields.Boolean(string="Branches")
    
    