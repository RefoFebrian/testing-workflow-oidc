# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockLotPartner(models.Model):
    _inherit = "stock.lot"
    # INFO : Override from Stock Lot and Connected to Partner
    
    # 7: defaults methods

    # 8: fields
    sales_md_date = fields.Date(string='Sales MD Date ',help='Distribution Date to Dealers')

    # 9: relation fields
    supplier_id = fields.Many2one(comodel_name='res.partner', string='Supplier', help='Vehicle Supplier')
    stock_inbound_id = fields.Many2one(comodel_name='tw.stock.inbound', string="Shipping Expedition", help='Shipping Expedition for Vehicle')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    
