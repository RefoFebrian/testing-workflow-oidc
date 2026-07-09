# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import api, fields, models, _

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritResPartner(models.Model):
    _inherit = "res.partner"

    # 7: defaults methods

    # 8: fields
    is_send_to_dms = fields.Boolean(string="Send To DMS", help="Send to DMS if checked")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
