# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockPickingNrfsSparepart(models.Model):
    _inherit = "stock.picking"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def _group_move_lines_by_product(self, move_lines):
        """Helper method to group move lines by product_id and sum quantities
        
        Args:
            move_lines: recordset of stock.move.line
            
        Returns:
            dict: {product_id: total_quantity}
        """
        grouped = {}
        for move_line in move_lines:
            product_id = move_line.product_id.id
            if product_id not in grouped:
                grouped[product_id] = 0
            grouped[product_id] += move_line.quantity
        
        return grouped

    def _process_validate_move(self,move):
        res = super(InheritStockPickingNrfsSparepart, self)._process_validate_move(move)
        # Filter and group move lines
        line_ids = []
        picking_type_incoming = self._get_picking_type_incoming(move.picking_id.company_id)
        move_lines = move.move_line_ids.filtered(
            lambda l: l.move_id._is_last_move_from_route() and 
            l.move_id.picking_id.picking_type_id.id in picking_type_incoming and 
            not l.is_rfs and l.move_id.picking_id.division == 'Sparepart'
        )
        if move_lines:
            grouped_moves = self._group_move_lines_by_product(move_lines)
            for product_id,qty in grouped_moves.items():
                line_ids.append((0, 0, {
                    'product_sparepart_id': product_id,
                    'qty': qty
                }))
            self.suspend_security()._create_nrfs(move,lot_obj=False,nrfs_type=False,line_ids=line_ids)

        return res

