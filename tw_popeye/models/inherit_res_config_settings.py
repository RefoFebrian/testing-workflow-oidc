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
    is_check_account_popeye = fields.Boolean('Is check account to Popeye?', config_parameter='tw_popeye.is_check_account_popeye')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def set_values(self):
        """
        Setting True to check account to Popeye
        """
        super().set_values()
        is_check_account_popeye = self.env.ref('tw_popeye.is_check_account_popeye', False)
        if not is_check_account_popeye:
            self.write({
                'is_check_account_popeye': True
            })
    # 13: action methods

    # 14: private methods
