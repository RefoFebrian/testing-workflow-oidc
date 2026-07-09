# -*- coding: utf-8 -*-

# 1: imports of python lib
import qrcode
import base64
import io
from datetime import date, datetime, timedelta,time

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TWPrintGenerateQRCodeLine(models.Model):
    _name = "tw.print.generate.qr.code.line"
    _description = "Print Generate QR Code Line"
    
    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Kode Unik')
    
    # 9: relation fields
    qr_code_id = fields.Many2one('tw.qr.code.unit', string='QR Code')
    print_qr_code_id = fields.Many2one('tw.print.generate.qr.code', string='Print QR Code')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    

    # 14: private methods
    
