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


class TwProduct(models.Model):
    _inherit = "product.product"
    
    def get_category_name(self):
        if self.categ_id:
            categ = self.categ_id
            while categ:
                if categ.name in ('Unit', 'Sparepart', 'Umum', 'Extras'):
                    return categ.name
                categ = categ.parent_id
            return False

    def get_uom_pajak(self):
        # ? Penyesuaian UOM dengan Referensi pada Core Tax Pajak
        category_name = self.get_category_name()
        if category_name == 'Unit':
            return 'UM.0018'
        elif category_name == 'Sparepart':
            return 'UM.0021'
        elif category_name == 'Umum':
            return 'UM.0033'
        else:
            return 'UM.0033'

    
    def get_kode_barang_pajak(self):
        if self.type == 'product':
            return 'A'
        else:
            return 'B'