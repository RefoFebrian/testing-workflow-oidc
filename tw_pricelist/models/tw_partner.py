# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import api, fields, models, _

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class Partner(models.Model):
    _inherit = "res.partner"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    pricelist_type_id =  fields.Many2one(comodel_name='tw.selection', string='Pricelist Type' , domain=[('type','=','PricelistCategory')], help="Pricelist that can be used for supplier cost.")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
