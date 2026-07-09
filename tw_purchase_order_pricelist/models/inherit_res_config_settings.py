# -*- coding: utf-8 -*-

# 1: imports of python lib


# 2: import of known third party lib

# 3:  imports of odoo
from odoo import _, api, fields, models

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # 7: defaults methods

    # 8: fields
    is_only_use_pricelist = fields.Boolean('Is only use pricelist?', config_parameter='tw_pricelist.is_only_use_pricelist')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def set_values(self):
        """
        Setting True to use Pricelist in Purchase Order
        """
        super().set_values()
        is_only_use_pricelist = self.env.ref('tw_pricelist.is_only_use_pricelist', False)
        if not is_only_use_pricelist:
            self.write({
                'is_only_use_pricelist': True
            })
    # 13: action methods

    # 14: private methods
