# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwPaymentRequestFakturPajak(models.Model):
    """
    Inherit Payment Request untuk menambahkan fitur Faktur Pajak.
    Field is_combined_tax dan faktur_pajak_out_id sudah ada dari mixin.
    """
    _name = "tw.payment.request"
    _inherit = ["tw.payment.request", "tw.faktur.pajak.mixin"]

    # Fields dari mixin: is_combined_tax, faktur_pajak_out_id, no_faktur_pajak, tgl_faktur_pajak
