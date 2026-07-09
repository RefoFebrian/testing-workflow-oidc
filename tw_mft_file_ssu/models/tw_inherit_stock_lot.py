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

    # 7: defaults methods  

    # 8: fields
    filename_ssu_md_receive = fields.Char(string='SSU MD Receive file name', help='File name of SSU MD Receive')
    actual_ssu_md_receive_date = fields.Datetime(string='Actual SSU MD Receive Send Date', help='MD Admission SSU Receive Date')
    filename_ssu_md_send = fields.Char(string='SSU Send Dealer file name', help='File name of SSU Send Dealer')
    actual_ssu_md_send_date = fields.Datetime(string='Actual SSU MD Send Dealer Delivery Date', help='MD Admission SSU Send Dealer Delivered Date')

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
    