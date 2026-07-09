# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwBranchSetting(models.Model):
    _inherit = "tw.branch.setting"
    
    # 7: defaults methods
    
    # 8: fields
    
    # 9: relation fields
    dgi_config_id = fields.Many2one(
        'tw.api.configuration', 'DGI Config',
        help="Field ini digunakan untuk mendapatkan harga jasa pada transaksi Work Order",
        ondelete="restrict",
        domain="[('api_type_value','=','DGI'), ('company_id', 'in', (company_id, False))]")
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods