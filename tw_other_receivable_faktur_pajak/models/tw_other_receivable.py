# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwOtherReceivableFakturPajak(models.Model):
    """
    Inherit Other Receivable untuk menambahkan fitur Faktur Pajak.
    Field is_combined_tax dan faktur_pajak_out_id sudah ada dari mixin.
    """
    _name = "tw.other.receivable"
    _inherit = ["tw.other.receivable", "tw.faktur.pajak.mixin"]

    # Fields dari mixin: is_combined_tax, faktur_pajak_out_id


    def action_post(self):
        if self.type == 'other_receivable' and not self.is_combined_tax:
            self.get_number_faktur_pajak()
        return super().action_post()
