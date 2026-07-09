# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import datetime

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockLot(models.Model):
    _inherit = "stock.lot"
    
    dgi_spk_number = fields.Char(string='DGI SPK Number', help='Nomor SPK dari DGI')