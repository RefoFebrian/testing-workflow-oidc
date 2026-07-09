# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockQuantPackage(models.Model):
    _inherit = "stock.quant.package"
    _description = "Stock Quant Package"
    
    # 7: defaults methods
    quantity = fields.Integer(string="Quantity")
    current_quantity = fields.Integer(string="Current Quantity")

    # 8: fields
    product_id = fields.Many2one(comodel_name='product.product', string="Product", help="Product for the package")
    picking_id = fields.Many2one(comodel_name='stock.picking', string="Picking", help="Picking for the package")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
        
    @api.model_create_multi
    def create(self,vals_list):
        return super(InheritStockQuantPackage, self).create(vals_list)
    
    def write(self,vals):
        return super(InheritStockQuantPackage, self).write(vals)
                
    # 13: action methods

    # 14: private methods
    
