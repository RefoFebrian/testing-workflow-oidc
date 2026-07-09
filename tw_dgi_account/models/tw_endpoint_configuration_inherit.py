# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwEndpointConfigurationDgia(models.Model):
    _inherit = "tw.endpoint.configuration"

    # 7: defaults methods
    
    # 8: fields
    input_template = fields.Json(
        string="Input Template (Request Body)",
        help="Define JSON structure to send for ADD mode.\n\n"
             "Usage:\n"
             "{ 'idInvoice': 'name', 'idCustomer': 'partner_id.default_code', 'caraBayar': 'Cash' }\n"
             "You can map to Odoo fields or use string literals.",
    )

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
