# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwAccountMoveFakturPajak(models.Model):
    """
    Inherit Account Move untuk menambahkan fitur Faktur Pajak.
    Field is_combined_tax, faktur_pajak_out_id, dan number_faktur_pajak sudah ada dari mixin.
    Hanya berlaku untuk Invoice (out_invoice, out_refund).
    """
    _name = "account.move"
    _inherit = ["account.move", "tw.faktur.pajak.mixin"]

    # Fields dari mixin: is_combined_tax, faktur_pajak_out_id, number_faktur_pajak
