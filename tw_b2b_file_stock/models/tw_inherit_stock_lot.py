# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib


class TwB2bFileStockLot(models.Model):
    _inherit = "stock.lot"
    # INFO : Override from B2b File and Connected to Stock Lot

    # 7: defaults methods  

    # 8: fields
    supplier_invoice_number = fields.Char(string='Supplier Invoice Number', help='Invoice Number derived from supplier data')
    sipb_number = fields.Char(string='SIPB Number', help='Shipping Number for Goods Pickup Permit derived from supplier data')
    ship_list_number = fields.Char(string='SL Number', help='Shipping List Number derived from supplier data')
    ship_list_date = fields.Date(string='SL Date', help='Shipping List Date derived from supplier data')
    expedition_ship = fields.Char(string='Expedition Ship', help='Name of the ship that transports the expedition car')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    # @api.model
    # def create(self, vals_list):
    #     create = super(TwSaleBranch, self).create(vals_list)
       
    #     return create

    # def write(self,vals):
       
    #     return super(TwSaleBranch, self).write(vals)

    # 13: action methods
    