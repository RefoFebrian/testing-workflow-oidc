# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib



MANDATORY_DESCRIPTION = """
    This data must be informed on the proof of
    the transaction provided to the customer
"""

class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    # 7: defaults methods

    # 8: fields
    """
        several merchant info that could be handled by res.partner by default
        city        :: # already available as city / city_id
        country     :: # already available as res_country_id
        email       :: # already available as email
        name        :: # already available as name / name related
        postal_code :: # already available as zip_code
    """
    merchant_id = fields.Char(string='Merchant', help='Merchant ID from clients')
    merchant_pan = fields.Char(string='Merchant Pan', help=MANDATORY_DESCRIPTION)
    payment_channel_name = fields.Char(string='Payment Channel Name')
    terminal_id = fields.Char(string='Terminal ID', size=8)
    is_bank = fields.Boolean(string='Bank?')
    is_fintech = fields.Boolean(string='Fintech?')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods