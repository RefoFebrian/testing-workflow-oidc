# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime
import calendar

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools import float_is_zero, OrderedSet

# 5: local imports

# 6: Import of unknown third party lib

class TwStockMove(models.Model):
    _inherit = "stock.move"
    # 7: defaults methods

    # 8: fields
    bom_line_id = fields.Many2one('mrp.bom.line', 'BoM Line', check_company=False)
	
    # 9: relation fields
	
    # 10: constraints & sql constraints
	
    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_explode(self):
        """Override to handle extras BoM explosion with idempotent aggregation.

        Ensures that extras moves are never duplicated when ``action_explode``
        is triggered multiple times on the same picking (e.g. separate SIPB
        commits each calling ``picking.action_confirm()``).

        Strategy:
        1. Aggregate BOM explosion results by ``(picking_id, extras_product_id)``.
        2. Before creating a new extras move, check if the picking already has
           an extras move for the same product (from a prior ``action_confirm``).
        3. If found → **update** its ``product_uom_qty`` (add the new qty).
        4. If not  → **create** a new phantom move as usual.
        """
        move_ids = super(TwStockMove, self).action_explode()
        moves_ids_to_return = OrderedSet()

        # --- Phase 1: Collect BOM data & aggregate by (picking, bom) ----------
        picking_bom_data = {}

        for move in move_ids:
            if not move._is_generate_bom():
                moves_ids_to_return.add(move.id)
                continue

            bom = self.env['mrp.bom'].sudo()._bom_find(
                move.product_id, company_id=move.company_id.id, bom_type='extras',
            )[move.product_id]
            if not bom:
                moves_ids_to_return.add(move.id)
                continue

            if (not move.picking_type_id and not move.env.context.get('is_scrap')) \
                    or (move.production_id and move.production_id.product_id == move.product_id):
                moves_ids_to_return.add(move.id)
                continue

            # Calculate factor for this move
            if float_is_zero(move.product_uom_qty,
                             precision_rounding=move.product_uom.rounding):
                factor = (move.product_uom._compute_quantity(
                    move.quantity, bom.product_uom_id) / bom.product_qty)
            else:
                factor = (move.product_uom._compute_quantity(
                    move.product_uom_qty, bom.product_uom_id) / bom.product_qty)

            picking_id = move.picking_id.id if move.picking_id else 0
            key = (picking_id, bom.id)

            if key not in picking_bom_data:
                picking_bom_data[key] = {
                    'bom': bom,
                    'first_move': move,
                    'total_factor': 0,
                }
            picking_bom_data[key]['total_factor'] += factor
            moves_ids_to_return.add(move.id)

        # --- Phase 2: Explode BOMs & aggregate extras by product_id -----------
        extras_by_product = {}  # {(picking_id, product_id): {'bom_line', 'qty', 'first_move'}}

        for key, data in picking_bom_data.items():
            picking_id = key[0]
            bom = data['bom']
            move = data['first_move']
            total_factor = data['total_factor']

            _dummy, lines = bom.sudo().explode(
                move.product_id, total_factor,
                picking_type=bom.picking_type_id,
                never_attribute_values=move.never_product_template_attribute_value_ids,
            )

            for bom_line, line_data in lines:
                pid = bom_line.product_id.id
                agg_key = (picking_id, pid)
                if agg_key not in extras_by_product:
                    extras_by_product[agg_key] = {
                        'bom_line': bom_line,
                        'qty': 0,
                        'first_move': move,
                    }
                extras_by_product[agg_key]['qty'] += line_data['qty']

        # --- Phase 3: Create or update extras moves (idempotent) --------------
        phantom_moves_vals_list = []

        for (picking_id, pid), extra_data in extras_by_product.items():
            bom_line = extra_data['bom_line']
            new_qty = extra_data['qty']
            move = extra_data['first_move']
            is_scrap_or_zero = (
                float_is_zero(move.product_uom_qty,
                              precision_rounding=move.product_uom.rounding)
                or self.env.context.get('is_scrap')
            )

            # Guard: check if an extras move for this product already exists
            existing_extras = self.env['stock.move']
            if picking_id:
                existing_extras = self.env['stock.move'].search([
                    ('picking_id', '=', picking_id),
                    ('product_id', '=', pid),
                    ('bom_line_id', '!=', False),
                ], limit=1)

            if existing_extras:
                # Update existing move qty instead of creating a duplicate
                if is_scrap_or_zero:
                    existing_extras.write({
                        'quantity': existing_extras.quantity + new_qty,
                    })
                else:
                    existing_extras.write({
                        'product_uom_qty': existing_extras.product_uom_qty + new_qty,
                    })
                moves_ids_to_return.add(existing_extras.id)
            else:
                # Create new phantom move
                if is_scrap_or_zero:
                    phantom_moves_vals_list += move._generate_move_phantom(
                        bom_line, 0, new_qty)
                else:
                    phantom_moves_vals_list += move._generate_move_phantom(
                        bom_line, new_qty, 0)

        if phantom_moves_vals_list:
            phantom_moves = self.env['stock.move'].create(phantom_moves_vals_list)
            phantom_moves._adjust_procure_method()
            for new_id in phantom_moves.ids:
                moves_ids_to_return.add(new_id)

        return self.env['stock.move'].browse(list(moves_ids_to_return))

    def _is_generate_bom(self):
        self.ensure_one()
        if self.picking_type_id.code == 'internal':
            return False
        if self.env.context.get('bypass_entire_pack'):
            # ? When create backorder from entire pack skip this move (Don't Create Extras Again)
            return False
        if not self._is_first_move_from_route():
            return False
        if (not self.picking_type_id and not self.env.context.get('is_scrap')) or (self.production_id and self.production_id.product_id == self.product_id):
            return False
        elif self.picking_type_id.code == 'mrp_operation':
            return False
        return True
