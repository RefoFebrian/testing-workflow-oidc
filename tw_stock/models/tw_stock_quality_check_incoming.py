# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TWStockQualityCheckIncoming(models.TransientModel):
    _name = "tw.stock.quality.check.incoming"
    _description = "Stock Quality Check Incoming"
    
    # 7: defaults methods
    initial_quantity = fields.Integer(string="Quantity Seharusnya")
    quantity = fields.Integer(string="Quantity")
    categ_tracking = fields.Selection(related='product_id.categ_id.tracking', string='Tracking by Category')

    # 8: fields
    company_id = fields.Many2one(comodel_name='res.company', string="Branch", help="Company for the package")
    picking_id = fields.Many2one(comodel_name='stock.picking', string="Picking", help="Picking for the package")
    move_line_id = fields.Many2one(comodel_name='stock.move.line', string="Move Line", help="Move Line for the package")
    result_package_id = fields.Many2one(comodel_name='stock.quant.package', string="Result Package", help="Result Package for the package")
    product_id = fields.Many2one(comodel_name='product.product', string="Product", help="Product for the package")
    lot_id = fields.Many2one(comodel_name='stock.lot', string="Lot", help="Lot for the package")
    location_dest_id = fields.Many2one(comodel_name='stock.location', string="Destination Location", help="Destination Location for the package")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
                
    # 13: action methods
    def action_confirm(self):
        if self.quantity <= 0:
            raise Warning("Quantity yang diinput harus lebih besar dari 0!")
        
        if self.quantity > self.initial_quantity:
            raise Warning("Quantity yang diinput tidak boleh lebih besar dari quantity seharusnya!")

        self.move_line_id.sudo().write({
            'lot_id': self.lot_id.id,
            'location_qc_id': self.location_dest_id.id,
            'supply_qty': self.quantity,
        })

    # 14: private methods
    
