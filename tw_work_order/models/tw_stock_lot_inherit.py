# -*- coding: utf-8 -*-

# 1: imports of python lib
import time
from datetime import datetime
import string

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
class StockLot(models.Model):
    _inherit = "stock.lot"

    # 7: defaults methods

    # 8: fields
    qr_code = fields.Char(string="QR Code")

    # 9: relation fields
    driver_id = fields.Many2one('res.partner','Driver', domain=[('category_id.name','=','Driver')])
    work_order_ids = fields.One2many('tw.work.order','lot_id',string="Work Orders",readonly=True)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('name', 'product_id')
    def onchange_name(self):
        dom = {}
        product_ids = self.env['product.category'].get_child_ids('Unit')
        dom['product_id']=[('categ_id','in',product_ids)]
        if self.name :
            self.name = self.name.replace(' ', '').upper()
            return {'value' : {'name':self.name,'state':'workshop'},'domain':dom }
        
    @api.onchange('chassis_number')
    def onchange_chassis(self):
        if self.chassis_number :
            self.chassis_number = self.chassis_number.replace(' ', '').upper()
            return {'value' : {'chassis_number':self.chassis_number}}
        
    @api.onchange('plate_number')
    def onchange_plate_number(self):
        if self.plate_number :
            self.plate_number = self.plate_number.replace(' ', '').upper()
            return {'value' : {'plate_number':self.plate_number}}
        
    def _compute_display_name(self):
        for record in self:
            name = record.name
            record.display_name = name

    # 12: override methods    