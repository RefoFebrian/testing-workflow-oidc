# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import fields, models

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class ResConfigSettings(models.TransientModel):
    """Inherit res.config.settings untuk setting Coretax."""

    _inherit = "res.config.settings"

    # 7: defaults methods

    # 8: fields
    use_coretax = fields.Boolean( string="Tax Use Coretax Format", config_parameter="tw_faktur_pajak_core_tax.use_coretax", help="Jika diceklis, generate Faktur Pajak dan report menggunakan format Coretax.")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def set_values(self):
        """Save Coretax setting values and ensure all menus are active."""
        super().set_values()
        # Ensure all eFaktur menus are always visible (no toggle)
        all_menus = [
            'tw_faktur_pajak.tw_faktur_pajak_menuitem',
            'tw_efaktur_pajak.menu_tw_efaktur_pajak',
            'tw_faktur_pajak_core_tax.menu_efaktur_pajak',
        ]
        for xmlid in all_menus:
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            if menu:
                menu.sudo().write({'active': True})

    # 13: action methods

    # 14: private methods
