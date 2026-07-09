# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
from odoo.tools.float_utils import float_compare, float_is_zero

class InheritStockQuant(models.Model):
    _inherit = "stock.quant"
    _description = "Stock Quant"
    
    # 7: defaults methods

    # 8: fields
    # TODO : Kemungkinan tidak di gunakan, karena untuk stock yang belum consolidate akan kita taruh di lokasi berbeda.
    consolidated_date = fields.Datetime(string='Consolidated Date', help="Tanggal Pengakuan Stock")

    # 9: relation fields
    reservation_ids = fields.Many2many(comodel_name='stock.move', relation='tw_stock_quant_stock_move_rel',
                                  column1='quant_id', column2='move_id', string='Reserved for Move', help="The move the quant is reserved for")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        res = super(InheritStockQuant, self).create(vals_list)
        for vals in vals_list:
            if 'location_id' in vals:
                self._validate_location(vals['location_id'])
        return res
    
    def write(self, vals):
        res = super(InheritStockQuant, self).write(vals)
        if 'location_id' in vals:
            self._validate_location(vals['location_id'])
        return res

    @api.model
    def _clean_reservations(self):
        """Override to also rebuild reservation_ids after native reserved_quantity sync.

        Odoo's native _clean_reservations only works at aggregate qty level (product x location x lot ...)
        and has no knowledge of individual move IDs.  After the native sync finishes we rebuild
        reservation_ids from the real ground truth: active stock.move.line records.
        """
        super()._clean_reservations()
        self._sync_reservation_ids()

    @api.model
    def _sync_reservation_ids(self):
        """Rebuild reservation_ids on all quants from active stock.move.line records.

        Source of truth: move lines with state in (assigned, partially_available, waiting, confirmed)
        grouped by (product_id, location_id, lot_id, package_id, owner_id) -> move_ids.

        For each matching quant we set reservation_ids to exactly the set of moves
        that are actually reserving QTY against it.  Quants with reserved_quantity = 0
        get their reservation_ids cleared.
        """
        # --- Build move lookup from active move lines ---
        # Group by the same key used by _clean_reservations to match quants
        active_move_lines = self.env['stock.move.line']._read_group(
            [
                ('state', 'in', ['assigned', 'partially_available', 'waiting', 'confirmed']),
                ('quantity_product_uom', '!=', 0),
                ('product_id.is_storable', '=', True),
            ],
            ['product_id', 'location_id', 'lot_id', 'package_id', 'owner_id'],
            ['move_id:recordset'],
        )
        # Build dict: key -> move recordset
        move_by_key = {
            (product.id, location.id, lot.id, package.id, owner.id): moves
            for product, location, lot, package, owner, moves in active_move_lines
        }

        # --- Fetch all quants that have reserved_quantity > 0 or reservation_ids set ---
        quants_to_sync = self.sudo().search([
            '|',
            ('reserved_quantity', '!=', 0),
            ('reservation_ids', '!=', False),
        ])

        for quant in quants_to_sync:
            key = (
                quant.product_id.id,
                quant.location_id.id,
                quant.lot_id.id,
                quant.package_id.id,
                quant.owner_id.id,
            )
            expected_moves = move_by_key.get(key, self.env['stock.move'])
            current_moves = quant.reservation_ids

            to_add = expected_moves - current_moves
            to_remove = current_moves - expected_moves

            write_vals = []
            if to_add:
                write_vals += [(4, m.id) for m in to_add]
            if to_remove:
                write_vals += [(3, m.id) for m in to_remove]

            if write_vals:
                quant.sudo().write({'reservation_ids': write_vals})

    # 13: action methods
    def get_stock_available(self, product_id, company_id, usage='internal', location_id=False, lot_state='stock', include_reserved=False, is_include_sublocations=True, location_dest_id=False):
        if not location_id:
            location_obj = self.env['stock.location'].suspend_security().search([('usage','=',usage),'|',('company_id','=',company_id),('company_id','=',False)])
            location_ids = str(tuple([location.id for location in location_obj])).replace(',)', ')')
        elif location_id:
            if is_include_sublocations:
                location_obj = self.env['stock.location'].suspend_security().search([('location_id', 'child_of', location_id)])
            else:
                location_obj = self.env['stock.location'].suspend_security().search([('location_id', '=', location_id)])
            location_ids = str(tuple([location.id for location in location_obj]+[location_id])).replace(',)', ')')
        if not location_ids:
            raise Warning("Location not found")
        
        loc_dest_where_clause = ""
        if location_dest_id:
            loc_dest_where_clause = "AND sq.location_id != %d" % location_dest_id
        

        query = f"""
            SELECT 
                CASE WHEN {include_reserved} IS TRUE 
                    THEN COALESCE(SUM(sq.quantity),0) 
                    ELSE COALESCE(SUM(sq.quantity),0) - COALESCE(SUM(sq.reserved_quantity),0) 
                END as quantity
            FROM stock_quant sq
            LEFT JOIN stock_lot sl ON sl.id = sq.lot_id
            WHERE 1=1
                AND sq.company_id = {company_id}
                AND sq.product_id = {product_id} 
                AND sq.location_id IN {location_ids}
                AND (sq.lot_id IS NULL OR sl.state = '{lot_state}')
                {loc_dest_where_clause}
        """
        self._cr.execute(query)
        return self._cr.fetchall()[0][0]

    def compare_stock_on_transaction(self, company_id, division, product_id, qty, location_id=None):
        avb_stock = self.get_stock_available(product_id, company_id, location_id=location_id, include_reserved=True)
        compare_stock = self._prepare_compare_stock(company_id=company_id,product_id=product_id, location_id=location_id, division=division)
        # If the sum of stock in process and ordered quantity exceeds available stock, raise a warning
        if (compare_stock+qty) > avb_stock:
            product_name = self.env['product.product'].browse(product_id).name
            location_text = ""
            if location_id:
                location_text = f"\nLocation : {self.env['stock.location'].browse(location_id).complete_name}"
            raise Warning(f"Stock for Product : {product_name} is insufficient.\nAvailable Stock: {avb_stock}, Stock in Process : {compare_stock}, Ordered quantity: {qty}{location_text}")
        return avb_stock-(compare_stock)
    
    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity=False, reserved_quantity=False, lot_id=None, package_id=None, owner_id=None, in_date=None):
        """ Increase or decrease `quantity` or 'reserved quantity' of a set of quants for a given set of
        product_id/location_id/lot_id/package_id/owner_id.

        :param product_id:
        :param location_id:
        :param quantity:
        :param lot_id:
        :param package_id:
        :param owner_id:
        :param datetime in_date: Should only be passed when calls to this method are done in
                                 order to move a quant. When creating a tracked quant, the
                                 current datetime will be used.
        :return: tuple (available_quantity, in_date as a datetime)
        """
        if not (quantity or reserved_quantity) and not self.env.context.get('inventory_mode'):
            raise ValidationError(_('Quantity or Reserved Quantity should be set.'))
        self = self.sudo()
        
        # Ensure parameters are recordsets, not False/None (prevents AttributeError: 'bool' object has no attribute 'id')
        lot_id = lot_id or self.env['stock.lot']
        package_id = package_id or self.env['stock.quant.package']
        owner_id = owner_id or self.env['res.partner']

        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
        if lot_id:
            if float_compare(quantity, 0, precision_rounding=product_id.uom_id.rounding) > 0:
                quants = quants.filtered(lambda q: q.lot_id)
            else:
                # Don't remove quantity from a negative quant without lot
                quants = quants.filtered(lambda q: float_compare(q.quantity, 0, precision_rounding=q.product_uom_id.rounding) > 0 or q.lot_id)

        if location_id.should_bypass_reservation():
            incoming_dates = []
        else:
            incoming_dates = [quant.in_date for quant in quants if quant.in_date and
                              float_compare(quant.quantity, 0, precision_rounding=quant.product_uom_id.rounding) > 0]
        if in_date:
            incoming_dates += [in_date]
        # If multiple incoming dates are available for a given lot_id/package_id/owner_id, we
        # consider only the oldest one as being relevant.
        if incoming_dates:
            in_date = min(incoming_dates)
        else:
            in_date = fields.Datetime.now()

        quant = None
        if quants:
            # see _acquire_one_job for explanations
            self._cr.execute("SELECT id FROM stock_quant WHERE id IN %s ORDER BY lot_id LIMIT 1 FOR NO KEY UPDATE SKIP LOCKED", [tuple(quants.ids)])
            stock_quant_result = self._cr.fetchone()
            if stock_quant_result:
                quant = self.browse(stock_quant_result[0])

        if quant:
            vals = {}
            if quantity:
                vals['in_date'] = in_date
                vals['quantity'] = quant.quantity + quantity
            if reserved_quantity:
                vals['reserved_quantity'] = max(0, quant.reserved_quantity + reserved_quantity)
                # Add move to reservation_ids when reserving
                move_id = self.env.context.get('reservation_move_id')
                if reserved_quantity > 0 and move_id:
                    vals['reservation_ids'] = [(4, move_id)]
                # Remove move from reservation_ids only when fully unreserved
                elif reserved_quantity < 0 and quant.reservation_ids:
                    new_reserved = max(0, quant.reserved_quantity + reserved_quantity)
                    if new_reserved == 0:
                        vals['reservation_ids'] = [(3, reservation_id.id) for reservation_id in quant.reservation_ids]
            if vals:
                quant.write(vals)

        else:
            vals = {
                'product_id': product_id.id,
                'location_id': location_id.id,
                'lot_id': lot_id and lot_id.id,
                'package_id': package_id and package_id.id,
                'owner_id': owner_id and owner_id.id,
                'in_date': in_date,
            }
            if quantity:
                vals['quantity'] = quantity
            if reserved_quantity:
                vals['reserved_quantity'] = reserved_quantity
            self.create(vals)
        return self._get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True, allow_negative=True), in_date

    def _prepare_compare_stock(self, company_id, product_id, location_id=None, division=None):
        """
        Prepare the stock comparison data for a transaction.
        """
        qty_in_picking = self.env['stock.picking']._get_qty_picking(company_id, division, product_id)
        qty_on_transaction = self._get_reserve_by_transaction(company_id, division, product_id, location_id)
        return qty_in_picking + qty_on_transaction
    
    # Dummy method to be overridden in child classes
    def _get_reserve_by_transaction(self, company_id, division, product_id, location_id=None):
        return 0
    
    def get_available_lot_stock(self, product_id, company_id, location_id=False, is_include_sublocations=True, usage='internal', lot_state='stock', include_reserved=False, location_dest_id=False):
        domain = [('company_id', '=', company_id), ('product_id', '=', product_id),('quantity','=',1), ('reserved_quantity','=',0)]
        if location_id:
            if is_include_sublocations:
                stock_location = self.env['stock.location'].search([('location_id', 'child_of', location_id)])
            else:
                stock_location = self.env['stock.location'].search([('id', '=', location_id)])
        else:
            stock_location = self.env['stock.location'].search([
                ('usage', '=', usage),
                '|', ('company_id', '=', company_id), ('company_id', '=', False)
            ])

        if location_dest_id:
            domain.append(('location_id', '!=', location_dest_id))

        domain.append(('location_id', 'in', stock_location.ids))

        if not include_reserved:
            domain.append(('reservation_ids', '=', False))
            domain.append(('reserved_quantity', '=', 0))

        lot_ids = self.env['stock.lot']
        quants = self.search(domain)
        if quants:
            avb_quant = quants.filtered(lambda q: q.lot_id.state == lot_state or not q.lot_id)
            lot_ids = avb_quant.lot_id
        return lot_ids    

    def _get_location_available_by_product(self, product, company_id, parent_location_id=False):
        """
        Mencari lokasi available berdasarkan product, dengan spesifik warna jika Unit.
        Jika tidak ditemukan, akan mencari berdasarkan product template.
        
        :param product: product.product record
        :param company_id: ID perusahaan
        :return: list of location IDs
        """
        parent_loc_where_clause = " "
        if parent_location_id:
            stock_location = self.env['stock.location'].search([('location_id', 'child_of', parent_location_id)])
            parent_loc_where_clause = f"AND quant.location_id IN ({', '.join(map(str, stock_location.ids))})"

        # Cari lokasi available berdasarkan product ID (spesifik warna) terlebih dahulu
        query = f"""
            SELECT 
                quant.location_id, 
                MIN(quant.create_date) as oldest_quant_date
            FROM stock_quant quant
            JOIN stock_location location ON location.id = quant.location_id
            LEFT JOIN tw_selection ts ON location.type_id = ts.id
            WHERE 
                quant.company_id = {company_id}
                AND quant.product_id = {product.id}
                AND (location.residual_capacity > 0 or coalesce(location.capacity,0) = 0)
                AND (location.type_id IS NULL OR ts.value = 'rfs')
                {parent_loc_where_clause}
            GROUP BY quant.location_id
            ORDER BY oldest_quant_date ASC
        """
        self._cr.execute(query)
        location_ids = [rec[0] for rec in self._cr.fetchall() if rec[0]]
        
        # Jika tidak ditemukan, cari berdasarkan product template
        if not location_ids:
            query = f"""
                SELECT 
                    quant.location_id, 
                    MIN(quant.create_date) as oldest_quant_date
                FROM stock_quant quant
                JOIN stock_location location ON location.id = quant.location_id
                LEFT JOIN tw_selection ts ON location.type_id = ts.id
                JOIN product_product pp ON pp.id = quant.product_id
                WHERE 
                    quant.company_id = {company_id}
                    AND pp.product_tmpl_id = {product.product_tmpl_id.id}
                    AND location.residual_capacity > 0
                    AND (location.type_id IS NULL OR ts.value = 'rfs')
                    {parent_loc_where_clause}
                GROUP BY quant.location_id
                ORDER BY oldest_quant_date ASC
            """
            self._cr.execute(query)
            location_ids = [rec[0] for rec in self._cr.fetchall() if rec[0]]
        return location_ids
    
    # 14: private methods
    def _validate_location(self,location_id):
        location_obj = self.env['stock.location'].suspend_security().browse(location_id)
        if location_obj.is_restrict_capacity and location_obj.capacity > 0:
            stock_obj = self.search([('location_id','=',location_id)])
            if len(stock_obj.ids) > location_obj.capacity:
                raise ValidationError(_(f"The location {location_obj.name} has exceeded capacity {location_obj.capacity}, "
                                        "please increase capacity or reduce stock in location."))
