# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

# 5: local imports

# 6: Import of unknown third party lib

class TWStockPickingInherit(models.Model):
    _inherit = "stock.picking"
    
    # 8: fields
    
    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    def button_validate(self):
        if self.picking_line_ids:
            company_obj = self.env['res.company'].get_default_main_dealer()
            picking_line_nrfs_obj = self.picking_line_ids.filtered(lambda line: not line.is_rfs and self.division == 'Unit' and self.company_id.id == company_obj.id)
            if picking_line_nrfs_obj:
                for picking_line in picking_line_nrfs_obj:
                    move_obj = self.env['stock.move'].suspend_security().search([
                        ('picking_id', '=', self.id),
                        ('product_id', '=', picking_line.product_id.id)
                    ], limit=1)
                    if move_obj:
                        self._create_nrfs(move_obj, picking_line.lot_id, 'LKUAS')
                        if picking_line.lot_id.ready_for_sale != 'not_good':
                            picking_line.lot_id.suspend_security().write({'ready_for_sale': 'not_good'})

        return super(TWStockPickingInherit, self).button_validate()
    
    # 13: action methods

    # 14: private methods
