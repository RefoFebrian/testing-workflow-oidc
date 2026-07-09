# -*- coding: utf-8 -*-

# 1: imports of python lib
import pytz
from datetime import datetime
from ast import literal_eval
from lxml import etree

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import frozendict
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class InheritTwFakturPajakMixin(models.AbstractModel):
    _inherit = "tw.faktur.pajak.mixin"

    
    # 10: private method
    def get_number_faktur_pajak(self):
        faktur_pajak_out = self.env['tw.faktur.pajak.out'].sudo().get_number_faktur_pajak(self)
        return faktur_pajak_out
