# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritNrfsStockLot(models.Model):
    _inherit = "tw.nrfs"
    
    # 7: defaults methods

    # 8: fields
    chassis_number = fields.Char(string='Nomor Rangka')
    ship_list_number = fields.Char(string='No Shipping List')
    unit_receipt_date = fields.Date(string='Tanggal Penerimaan')

    # 9: relation fields
    lot_id = fields.Many2one('stock.lot', string='Nomor Mesin')
    stock_inbound_id = fields.Many2one('tw.stock.inbound', string='Stock Inbound')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
                
    @api.onchange('lot_id')
    def _onchange_lot_data(self):
        if self.lot_id:
            self.chassis_number = self.lot_id.chassis_number
            self.product_id = self.lot_id.product_id.id
            self.unit_receipt_date = self.lot_id.receive_date
            self.ship_list_number = self.lot_id.ship_list_number

    # 12: override methods

    # 13: action methods

    # 14: private methods
    
    