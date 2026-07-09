# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwApiConfigurationDGI(models.Model):
    """Extend tw.api.configuration with DGI-specific request body configuration.

    The dealer_id_source field controls how the 'dealerId' field is populated
    in the DGI API request body for all endpoints under this config.
    This is useful for ASP branches whose DGI dealer code differs from
    the branch's own atpm_code.
    """

    _inherit = "tw.api.configuration"

    # -------------------------------------------------------------------------
    # FIELDS
    # -------------------------------------------------------------------------
    dealer_id_source = fields.Selection(
        selection=[
            ("atpm_code", "ATPM Code (company_id.atpm_code)"),
            ("code", "Branch Code (company_id.code)"),
            ("parent_atpm_code", "Parent ATPM Code (company_id.parent_id.atpm_code)"),
        ],
        string="Dealer ID Source",
        default="atpm_code",
        required=True,
        help="Determines the source of 'dealerId' field in the DGI API request body.\n\n"
             "- ATPM Code: Uses the branch's own atpm_code (default, standard behavior).\n"
             "- Branch Code: Uses the branch's 'code' field.\n"
             "- Parent ATPM Code: Uses the parent company's atpm_code. "
             "Useful for ASP branches that need to report under their Main Dealer's DGI code.",
    )
