# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.osv import expression

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 5: local imports

# 6: Import of unknown third party lib

class StockPickingInherit(models.Model):
    _inherit = "stock.picking"
    
    # 7: defaults methods
    
    # 8: fields
    # 9: relation fields
    

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_confirm(self):
        res = super(StockPickingInherit,self).action_confirm()
        for picking in self:
            #? Cek costing method karena default nya kita hapus supaya tidak ada bug costing method berubah sendiri saat membuat company baru
            for move_line in picking.move_ids:
                if not move_line.product_id.categ_id.property_cost_method:
                    raise Warning("Costing Method is not set in Product Category %s. Please configure it first " % (move_line.product_id.categ_id.name))
        return res

    # 14: private methods