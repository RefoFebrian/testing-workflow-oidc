# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwAssetDisposalFakturPajak(models.Model):
    """Inherit Asset Disposal untuk menambahkan fitur Faktur Pajak.

    Field is_combined_tax dan faktur_pajak_out_id sudah ada dari mixin.
    """
    _name = "tw.asset.disposal"
    _inherit = ["tw.asset.disposal", "tw.faktur.pajak.mixin"]

    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & onchange methods

    # 12: override methods
    def action_confirm(self):
        """Override confirm to generate faktur pajak for sold-type disposals."""
        if self.type == 'sold' and not self.is_combined_tax:
            self.get_number_faktur_pajak()
        return super().action_confirm()

    # 13: action methods

    # 14: private methods
