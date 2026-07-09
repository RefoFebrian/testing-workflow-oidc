# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class InheritStockPickingBatch(models.Model):
    _inherit = "stock.picking.batch"

    # 7: defaults methods

    # 8: fields
    is_only_extras = fields.Boolean(string='Is Only Extras', default=False, compute='_compute_is_only_extras', store=True, help="checklist jika hanya ingin terima Extrasnya saja.")

    # 9: relation fields
    batch_extras_line_ids = fields.One2many(comodel_name='tw.stock.picking.batch.line', inverse_name="batch_id", string="Batch Extras Line", domain=[('division', '=', 'Extras')], help="Batch Extras Line for the operation")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('source_picking_ids')
    def _onchange_source_picking_ids(self):
        self.batch_extras_line_ids = False
        return super()._onchange_source_picking_ids()

    @api.depends('company_id', 'source_picking_ids', 'batch_line_ids')
    def _compute_is_only_extras(self):
        """Compute is_only_extras based on whether any line has 'Unit' division.
        
        If no line has 'Unit' division filled, is_only_extras is True.
        """
        for batch in self:
            if (not batch.batch_line_ids and not batch.source_picking_ids) or batch.division != 'Unit':
                batch.is_only_extras = False
            elif not batch.batch_line_ids and batch.source_picking_ids and not batch._get_lot_ids():
                batch.is_only_extras = True
            else:
                has_unit = any(line.division == 'Unit' for line in batch.batch_line_ids)
                batch.is_only_extras = not has_unit

    @api.depends('picking_ids', 'picking_ids.move_line_ids', 'batch_line_ids.lot_id', 'batch_line_ids.lot_name')
    def _compute_move_line_ids(self):
        """Override to include batch_extras_line_ids in lot_id matching."""
        super()._compute_move_line_ids()
        for batch in self:
            if batch.batch_line_ids:
                batch_lot_ids = (batch.batch_line_ids | batch.batch_extras_line_ids).mapped('lot_id')
                matching_move_lines = batch.picking_ids.move_line_ids.filtered(
                    lambda ml: ml.lot_id in batch_lot_ids or ml.lot_name or (ml.move_id.division in ('Extras', 'Sparepart') and ml.quantity > 0)
                )
                batch.move_line_ids = matching_move_lines

    # 12: override methods

    # 13: action methods
    def action_generate_extras(self):
        """Generate extras lines based on batch lines or source picking documents."""
        self.ensure_one()
        if self.division != 'Unit':
            return
        
        # Clear existing extras first
        self.batch_extras_line_ids = [(5, 0, 0)]

        if self.batch_line_ids:
            self._generate_extras_from_batch_lines()
        else:
            self._generate_extras_from_source_picking()

    # 14: private methods
    def _process_after_batch_lines(self, picking_ids):
        """Override hook to process extras lines after batch lines.
        
        Called by tw_stock's action_confirm between _process_batch_lines 
        and Odoo base action_confirm, maintaining original execution order.
        
        :param picking_ids: list of picking ids from _process_batch_lines
        """
        super()._process_after_batch_lines(picking_ids)
        self._process_confirm_batch_extras_lines(self.batch_extras_line_ids, picking_ids)
        
    def _validate_confirm_prerequisites(self):
        """Validate batch lines before confirm."""
        if self.has_batch_line and not self.batch_line_ids and not self.batch_extras_line_ids and not self.picking_ids:
            raise Warning('Batch Line atau Batch Line Extras tidak boleh kosong!')
        
        for line in self.batch_extras_line_ids:
            # Default tracking ('serial', 'lot') atau custom tracking ('serial_chassis')
            is_tracked = False
            if line.categ_tracking in ('serial', 'serial_chassis'):
                is_tracked = True
            elif line.product_id.tracking in ('serial', 'lot'):
                is_tracked = True

            if is_tracked:
                if not line.lot_id:
                    raise Warning(_("Permintaan Validasi Ditolak!\nProduk '%s' memerlukan input Serial Number / Lot, namun belum ditentukan.", line.product_id.display_name))
                    
        return super()._validate_confirm_prerequisites()

    def _process_batch_lines(self):
        """Override to include batch_extras_line_ids in move lines processing."""
        picking_ids = super()._process_batch_lines()
        
        if not self.batch_extras_line_ids:
            return picking_ids
        
        # Process Move lines from batch_extras_line_ids (with move_id)
        extras_move_lines = self.batch_extras_line_ids.filtered(lambda line: line.move_id)
        
        if extras_move_lines:
            self._process_confirm_move_lines(extras_move_lines)
            if self.division == 'Unit' and self.type == 'Retail':
                picking_ids.extend(self.source_picking_ids.ids)
        
        return picking_ids

    def _process_confirm_batch_extras_lines(self, batch_extras_line_ids, picking_ids):
        """Process batch extras lines in the batch.

        Optimized: uses bulk queries instead of per-line searches.
        Per-picking quantities are calculated from each picking's unit moves × BOM.

        :param batch_extras_line_ids: recordset of tw.stock.picking.batch.line
        :param picking_ids: list of picking ids to process
        :return: None
        """
        pickings = self.env['stock.picking']
        if picking_ids:
            pickings = self.env['stock.picking'].suspend_security().search([
                ('id', 'in', picking_ids)
            ])
        else:
            if not self.source_picking_ids and not self.picking_ids:
                raise Warning("Wajib input source document!")
            pickings = self.source_picking_ids if self.source_picking_ids else self.picking_ids

        # --- Clear ALL existing extras move lines on pickings ---
        # Prevents auto-assigned Odoo move lines from being validated
        for picking in pickings:
            for move in picking.extras_move_ids:
                self._remove_move_line(move)

        move_lines_to_create = []

        # === Process non-serial extras ===
        non_serial_lines = batch_extras_line_ids.filtered(
            lambda line: line.product_id.product_tmpl_id.tracking != 'serial'
        )
        if non_serial_lines:
            move_lines_to_create += self._process_non_serial_extras(
                non_serial_lines, pickings
            )

        # === Process serial extras ===
        serial_lines = batch_extras_line_ids.filtered(
            lambda line: line.product_id.product_tmpl_id.tracking == 'serial'
            and line.lot_id
        )
        if serial_lines:
            move_lines_to_create += self._process_serial_extras(
                serial_lines, pickings
            )

        # --- Execute bulk create ---
        if move_lines_to_create:
            self.env['stock.move.line'].suspend_security().create(move_lines_to_create)

        self._link_pickings_to_batch(pickings)

    def _process_non_serial_extras(self, valid_lines, pickings):
        """Process non-serial tracked extras lines.

        :param valid_lines: batch extras lines with tracking != serial
        :param pickings: stock.picking recordset
        :return: list of move line vals dicts
        """
        valid_product_ids = valid_lines.mapped('product_id').ids

        # Calculate per-picking extras qty
        per_picking_qty = {}
        if self.batch_line_ids:
            per_picking_qty = self._calculate_extras_from_batch_lines(pickings)
        else:
            per_picking_qty = self._calculate_extras_from_picking_moves(pickings)

        # Bulk fetch moves (1 query)
        all_moves = self.env['stock.move'].suspend_security().search([
            ('picking_id', 'in', pickings.ids),
            ('product_id', 'in', valid_product_ids),
        ])

        move_map = {}
        for move in all_moves:
            key = (move.picking_id.id, move.product_id.id)
            if key not in move_map:
                move_map[key] = move

        vals_list = []
        for picking in pickings:
            for line in valid_lines:
                move = move_map.get((picking.id, line.product_id.id))
                if not move:
                    continue

                qty = per_picking_qty.get((picking.id, line.product_id.id), 0)
                if qty <= 0:
                    continue

                vals_list.append(
                    self._prepare_extras_move_line_vals(picking, move, qty)
                )

        return vals_list

    def _process_serial_extras(self, serial_lines, pickings):
        """Process serial tracked extras lines.

        Each line has a lot_id and qty=1. Finds the matching move
        in a picking and creates a move line with the lot_id.

        :param serial_lines: batch extras lines with tracking == serial and lot_id
        :param pickings: stock.picking recordset
        :return: list of move line vals dicts
        """
        serial_product_ids = serial_lines.mapped('product_id').ids

        # Bulk fetch serial extras moves (1 query)
        all_moves = self.env['stock.move'].suspend_security().search([
            ('picking_id', 'in', pickings.ids),
            ('product_id', 'in', serial_product_ids),
        ])

        # Build mapping: {(picking_id, product_id): move}
        move_map = {}
        for move in all_moves:
            key = (move.picking_id.id, move.product_id.id)
            if key not in move_map:
                move_map[key] = move

        vals_list = []
        for line in serial_lines:
            # Find the move in any picking for this product
            for picking in pickings:
                move = move_map.get((picking.id, line.product_id.id))
                if move:
                    vals_list.append(
                        self._prepare_extras_move_line_vals(
                            picking, move, 1, lot_id=line.lot_id.id
                        )
                    )
                    break

        return vals_list

    def _link_pickings_to_batch(self, pickings):
        """Link all unlinked pickings to this batch.

        :param pickings: stock.picking recordset
        """
        for picking in pickings:
            if not picking.batch_id:
                self._link_picking_to_batch(picking)

    def _calculate_extras_from_batch_lines(self, pickings):
        """Calculate per-picking extras qty from batch_extras_line_ids.

        Builds an extras qty map from batch_extras_line_ids, then resolves
        the picking per (picking_id, extras_product_id) via move search.

        :param pickings: stock.picking recordset
        :return: dict {(picking_id, extras_product_id): qty}
        """
        per_picking_qty = {}

        # Build extras qty map directly from batch_extras_line_ids
        extras_qty_map = {
            line.product_id.id: line.quantity
            for line in self.batch_extras_line_ids
        }
        if not extras_qty_map:
            return per_picking_qty

        # Find moves for extras products in pickings (1 query)
        all_moves = self.env['stock.move'].suspend_security().search([
            ('picking_id', 'in', pickings.ids),
            ('product_id', 'in', list(extras_qty_map.keys())),
        ])

        for move in all_moves:
            # Mendistribusikan extras ke setiap move dari picking2 yang di input.
            extras_pid = move.product_id.id
            key = (move.picking_id.id, extras_pid)
            extras_batch_qty = extras_qty_map.get(extras_pid, 0)
            # Jika qty di extras sudah habis, stop
            if extras_batch_qty > 0:
                # Jika QTY extras di batch 3 tetapi qty di move hanya 2, maka pilih yang lebih kecil (2)
                # Dan QTY sisanya akan di masukkan ke move lain.
                # Jika QTY di move lebih besar, masukkan semua qty nya
                qty_to_add = min(move.product_uom_qty, extras_batch_qty)
                new_qty = (per_picking_qty.get(key, 0) + qty_to_add)
                per_picking_qty[key] = new_qty
                extras_qty_map[extras_pid] = extras_qty_map.get(extras_pid, 0) - qty_to_add
        
        # Check if there are any remaining extras
        if any(qty > 0 for qty in extras_qty_map.values()):
            overqty_products = {k: v for k, v in extras_qty_map.items() if v > 0}
            products = self.env['product.product'].search([('id', 'in', list(overqty_products.keys()))])
            product_names = ', '.join(products.mapped('name'))
            raise Warning(_("Quantity Extras untuk product %s melebihi total qty seharusnya, silahkan periksa kembali inputan anda!"%(product_names)))

        return per_picking_qty

    def _calculate_extras_from_picking_moves(self, pickings):
        """Calculate per-picking extras qty from user input.

        Uses batch_extras_line_ids qty (user-editable) as source of truth,
        then distributes across pickings based on each picking's
        extras_move_ids capacity.

        :param pickings: stock.picking recordset
        :return: dict {(picking_id, extras_product_id): qty}
        """
        per_picking_qty = {}

        # Build user input map: {extras_product_id: qty}
        user_input = {}
        for line in self.batch_extras_line_ids:
            if line.product_id.product_tmpl_id.tracking == 'serial':
                continue
            user_input[line.product_id.id] = line.quantity

        if not user_input:
            return per_picking_qty

        # Build picking capacity: {product_id: [(picking_id, capacity), ...]}
        picking_capacity = {}
        for picking in pickings:
            for move in picking.extras_move_ids:
                pid = move.product_id.id
                if pid not in user_input:
                    continue
                if pid not in picking_capacity:
                    picking_capacity[pid] = []
                picking_capacity[pid].append((picking.id, move.product_uom_qty))

        # Distribute user input across pickings by capacity
        for product_id, total_qty in user_input.items():
            remaining = total_qty
            for picking_id, capacity in picking_capacity.get(product_id, []):
                if remaining <= 0:
                    break
                pick_qty = min(remaining, capacity)
                remaining -= pick_qty

                key = (picking_id, product_id)
                per_picking_qty[key] = per_picking_qty.get(key, 0) + pick_qty

        return per_picking_qty

    def _prepare_extras_move_line_vals(self, picking, move, qty, lot_id=False):
        """Prepare values for creating extras move line.

        :param picking: stock.picking record
        :param move: stock.move record
        :param qty: calculated quantity for this picking
        :param lot_id: optional int, lot_id for serial tracked products
        :return: dict of values for move line creation
        """
        vals = {
            'picking_id': picking.id,
            'move_id': move.id,
            'product_id': move.product_id.id,
            'company_id': picking.company_id.id,
            'location_id': picking.picking_type_id.default_location_src_id.id,
            'location_dest_id': picking.picking_type_id.default_location_dest_id.id,
            'quantity': qty,
            'quantity_product_uom': qty,
            'picked': True,
        }
        if lot_id:
            vals['lot_id'] = lot_id
        return vals

    def _generate_extras_from_batch_lines(self):
        """Generate extras from batch lines with product_id.
        
        Logic:
        1. Count how many times each product_id appears in batch_line_ids
        2. Get picking_objs via stock.move search
        3. Generate extras using shared logic
        """
        lines_with_product = self.batch_line_ids.filtered(
            lambda line: line.product_id.product_tmpl_id.tracking == 'serial'
        )
        if not lines_with_product:
            return
        
        # Step 1: Count how many times each product_id is inputted
        product_counts = {}
        for line in lines_with_product:
            product_id = line.product_id.id
            if product_id in product_counts:
                product_counts[product_id] += 1
            else:
                product_counts[product_id] = 1

        # Step 2: Get picking_objs via stock.move search
        picking_objs = self._get_pickings_from_batch_lines(lines_with_product, product_counts)
        
        # Step 3: Generate extras using shared logic
        self._generate_extras_lines(product_counts, picking_objs)

    def _generate_extras_from_source_picking(self):
        """Generate extras from source picking when batch_line_ids is empty.

        Reads extras_move_ids directly from each source picking and
        creates batch_extras_line_ids (split serial, consolidate non-serial).
        """
        if not self.source_picking_ids:
            return

        extras_line_vals = []
        for picking in self.source_picking_ids:
            for move in picking.extras_move_ids:
                pid = move.product_id.id
                qty = move.product_uom_qty
                
                is_serial = move.product_id.product_tmpl_id.tracking == 'serial'
                
                if is_serial:
                    # Create N separate lines with qty=1
                    for _i in range(int(qty)):
                        extras_line_vals.append(
                            (0, 0, {'product_id': pid, 'quantity': 1})
                        )
                else:
                    # Consolidate non-serial
                    existing = next(
                        (v for v in extras_line_vals if v[2]['product_id'] == pid),
                        None
                    )
                    if existing:
                        existing[2]['quantity'] += qty
                    else:
                        extras_line_vals.append(
                            (0, 0, {'product_id': pid, 'quantity': qty})
                        )

        if extras_line_vals:
            self.batch_extras_line_ids = extras_line_vals

    def _get_pickings_from_batch_lines(self, lines_with_product, product_counts):
        """Get picking recordset from batch lines via stock.move search.
        
        :param lines_with_product: batch_line_ids filtered by serial tracking
        :param product_counts: dict {product_id: count}
        :return: stock.picking recordset
        """
        all_pickings = self.env['stock.picking']
        
        for product_id in product_counts.keys():
            move_search_domain = [
                ('product_id', '=', product_id),
                ('state', 'in', ['assigned', 'confirmed'])
            ]
            shipping_list_numbers = lines_with_product.filtered(
                lambda batch_line: batch_line.product_id.id == product_id
            ).mapped('lot_id.ship_list_number')
            # Check if mft_reference field exists on stock.picking model
            has_mft_reference = 'mft_reference' in self.env['stock.picking']._fields
            if shipping_list_numbers and has_mft_reference and self.type == 'MD':
                move_search_domain.append(('picking_id.mft_reference', 'in', shipping_list_numbers))
            elif self.source_picking_ids:
                move_search_domain.append(('picking_id', 'in', self.source_picking_ids.ids))
            
            moves = self.env['stock.move'].suspend_security().search(move_search_domain)
            if not moves:
                product = self.env['product.product'].browse(product_id)
                raise Warning(f"Move with product '{product.default_code}' Not Found!")
            
            all_pickings |= moves.mapped('picking_id')
        
        return all_pickings

    def _generate_extras_lines(self, product_counts, picking_objs):
        """Shared logic to generate extras lines.

        Phases:
        1. Collect BOM extras for each product_id (unit) in product_counts.
        2. Filter: only include extras that still have outstanding moves in pickings.
           If a BOM extras product is not found in any picking, it is skipped
           (assumed already received before).
        3. Generate batch_extras_line_ids with qty = min(move_qty, bom_calculated_qty).
           - move_qty: sum of product_uom_qty from outstanding extras moves.
           - bom_calculated_qty: sum of (unit_count × bom_qty) for this extras product.

        :param product_counts: dict {product_id: quantity}
        :param picking_objs: stock.picking recordset
        """
        # --- Phase 1: Collect all BOM extras per product ---
        product_bom_map = {}  # {product_id: {extras_product_id: bom_qty}}
        all_bom_extras_ids = set()

        for product_id in product_counts:
            product = self.env['product.product'].browse(product_id)

            bom = self.env['mrp.bom'].sudo()._bom_find(
                product, company_id=self.company_id.id, bom_type='extras',
            )[product]
            if not bom:
                continue

            bom_extras_map = {
                line.product_id.id: line.product_qty
                for line in bom.bom_line_ids
            }
            product_bom_map[product_id] = bom_extras_map
            all_bom_extras_ids.update(bom_extras_map.keys())

        # --- Phase 2: Build move qty map and BOM-calculated qty map ---
        # move_qty_map   : sum of product_uom_qty from outstanding extras moves per product.
        # bom_calc_map   : (unit_count × bom_qty) summed across all unit products per extras product.
        # BOM extras not found in any picking are silently skipped (already received before).
        move_qty_map = {}  # {extras_product_id: total_product_uom_qty}
        for picking in picking_objs:
            for move in picking.extras_move_ids:
                pid = move.product_id.id
                if pid not in all_bom_extras_ids:
                    continue
                move_qty_map[pid] = move_qty_map.get(pid, 0) + move.product_uom_qty

        bom_calc_map = {}  # {extras_product_id: total_bom_calculated_qty}
        for product_id, input_qty in product_counts.items():
            bom_extras_map = product_bom_map.get(product_id, {})
            for extras_product_id, bom_qty in bom_extras_map.items():
                bom_calc_map[extras_product_id] = (
                    bom_calc_map.get(extras_product_id, 0) + int(input_qty) * bom_qty
                )

        # --- Phase 3: Generate extras lines ---
        # Final qty = min(outstanding move qty, BOM-calculated qty).
        # Serial: N lines × qty=1 | Non-serial: 1 consolidated line.
        # Iterate over unique extras products from bom_calc_map to avoid
        # duplicating lines when multiple unit products share the same extras.
        extras_line_vals = []

        for extras_product_id, bom_calc_qty in bom_calc_map.items():
            move_qty = move_qty_map.get(extras_product_id, 0)
            final_qty = min(move_qty, bom_calc_qty)
            if final_qty <= 0:
                # Already received or no outstanding move — skip silently
                continue

            extras_product = self.env['product.product'].browse(extras_product_id)
            is_serial = extras_product.product_tmpl_id.tracking == 'serial'

            if is_serial:
                # Create N separate lines with qty=1
                for _i in range(int(final_qty)):
                    extras_line_vals.append(
                        (0, 0, {'product_id': extras_product_id, 'quantity': 1})
                    )
            else:
                extras_line_vals.append(
                    (0, 0, {'product_id': extras_product_id, 'quantity': final_qty})
                )

        if extras_line_vals:
            self.batch_extras_line_ids = extras_line_vals

    def _additional_cancelable_lines(self, picking_obj=False):
        """Process cancelable lines."""
        super()._additional_cancelable_lines(picking_obj)
        move_extras_lines = picking_obj.mapped('extras_move_ids.move_line_ids')
        return move_extras_lines
