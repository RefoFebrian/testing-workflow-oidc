# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import datetime

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockMoveLineQRCode(models.Model):
    _inherit = "stock.move.line"
    
    # 7: defaults methods

    # 8: fields
    qr_code = fields.Char(string='QR Code', help='QR Code Unit')

    # 9: relation fields
    
    # 10: constraints & sql constraints
    _sql_constraints = [
        ('qr_code_unique', 'unique(picking_id,qr_code)', 'QR Code must be unique!')
    ]

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('qr_code'):
                self.env['tw.qr.code.unit']._check_qr_code(vals.get('qr_code'), vals.get('company_id'))
        return super(InheritStockMoveLineQRCode,self).create(vals_list)
    
    def write(self,vals):
        if vals.get('qr_code'):
            self.env['tw.qr.code.unit']._check_qr_code(vals.get('qr_code'), vals.get('company_id'))
        return super(InheritStockMoveLineQRCode,self).write(vals)

    # 13: action methods

    # 14: private methods

