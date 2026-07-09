    # -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
from odoo.tools import OrderedSet
from odoo.tools.safe_eval import safe_eval
from odoo.tools.float_utils import float_compare, float_round, float_is_zero

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)

class InheritStockMove(models.Model):
    _inherit = "stock.move"
    
    _description = "Stock Move"
    
    # 7: defaults methods

    # 8: fields
    qty_available = fields.Float('Qty Available', digits='Product Unit of Measure')
    use_create_lots = fields.Boolean(
        'Create New Lots/Serial Numbers', 
        related='picking_type_id.use_create_lots', store=True, readonly=False,
        help="If this is checked only, it will suppose you want to create new Lots/Serial Numbers, so you can provide them in a text field. ")
    use_existing_lots = fields.Boolean(
        'Use Existing Lots/Serial Numbers',
        related='picking_type_id.use_existing_lots', store=True, readonly=False,
        help="If this is checked, you will be able to choose the Lots/Serial Numbers. You can also decide to not put lots in this operation type.  This means it will create stock with no lot or not put a restriction on the lot taken. ")
    is_create_serial_number = fields.Boolean(string='Create Serial Number?',default=True)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), string='Division', compute='_compute_division', store=True)
    initial_qty = fields.Float('Initial Qty')

    # 9: relation fields
    company_id = fields.Many2one("res.company", string="Branch")
    restrict_lot_ids = fields.Many2many(
        comodel_name='stock.lot',
        relation='tw_stock_move_restrict_lot_rel',
        column1='move_id',
        column2='lot_id',
        string="Restrict Lot"
    )
    available_location_ids = fields.Many2many(
        comodel_name='stock.location',
        relation='tw_stock_move_available_location_rel', column1='move_id', column2='location_id',
        compute='_compute_available_location_ids',
        string="Source Location Availables")
    has_chassis_tracking = fields.Selection(
        selection=[('serial', 'Serial Number'), ('serial_chassis', 'Serial & Chassis Number')], 
        string='Tracking', store=True, compute='_compute_has_chassis_tracking',
        help='Tracking Lot by Serial Number or (Serial Number and Chassis Number)'
    )
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('product_id', 'location_id')
    def _onchange_qty_available(self):
        self.qty_available = 0.0
        if self.product_id and self.picking_id.company_id and self.picking_id.location_id:
            qty_available = self.env['stock.quant'].get_stock_available(self.product_id.id, self.picking_id.company_id.id, False, self.picking_id.location_id.id)
            self.qty_available = qty_available

    @api.onchange('location_id')
    def _onchange_location_id(self):
        if self.location_id:
            for move_line in self.move_line_ids:
                move_line.location_id = self.location_id.id
    
    @api.onchange('move_line_ids')
    def _onchange_validate_duplicate_lot(self):
        """Validate duplicate lot on move_line_ids.

        Covers two input modes:
        - lot_id  : many2one, used when use_existing_lots is enabled
        - lot_name: freetext, used when use_create_lots is enabled (no existing lot yet)

        Both are normalised to their string name so cross-mode duplicates are
        caught as well (e.g. a lot_name that matches an already-selected lot_id.name).
        """
        if not self.move_line_ids:
            return

        seen_names = {}
        seen_chassis = []
        for line in self.move_line_ids:
            # Resolve the effective serial name from whichever input mode is active
            serial_name = None
            if line.lot_id:
                serial_name = line.lot_id.name
            elif line.lot_name:
                serial_name = line.lot_name

            if not serial_name:
                continue

            if serial_name in seen_names:
                return {
                    'warning': {
                        'title': _("Warning"),
                        'message': _(
                            "Unit dengan serial number '%(serial)s' sudah di input.\n"
                            "Mohon pilih serial number lain.",
                            serial=serial_name,
                        ),
                    }
                }
            seen_names[serial_name] = True

            # Check also the chassis
            if line.chassis_number:
                if line.chassis_number in seen_chassis:
                    return {
                        'warning': {
                            'title': _("Warning"),
                            'message': _(
                                "Unit dengan chassis number '%(chassis)s' sudah di input.\n"
                                "Mohon pilih chassis number lain.",
                                chassis=line.chassis_number,
                            ),
                        }
                    }
                seen_chassis.append(line.chassis_number)

    @api.depends(
        'has_tracking',
        'picking_type_id.use_create_lots',
        'picking_type_id.use_existing_lots',
        'state',
        'origin_returned_move_id',
        'product_id.type',
        'picking_code',
        'byproduct_id',
    )
    def _compute_show_info(self):
        for move in self:
            if move.byproduct_id or move.id in self.production_id.move_finished_ids.ids:
                move.show_quant = False
                move.show_lots_text = False
                move.show_lots_m2o = True
                move.use_create_lots = False
            elif move.raw_material_production_id and move.product_id.categ_id.tracking == 'serial_chassis':
                move.show_quant = False
                move.show_lots_text = False
                move.show_lots_m2o = True
                move.use_create_lots = False
            else:
                move.show_quant = False
                move.show_lots_text = move.has_tracking != 'none'\
                    and move.picking_type_id.use_create_lots\
                    and not move.picking_type_id.use_existing_lots\
                    and move.state != 'done' \
                    and not move.origin_returned_move_id.id
                move.show_lots_m2o = not move.show_quant\
                    and not move.show_lots_text\
                    and move.has_tracking != 'none'\
                    and (move.picking_type_id.use_existing_lots or move.state == 'done' or move.origin_returned_move_id.id)
            
    
    @api.depends('location_id')
    def _compute_available_location_ids(self):
        for record in self:
            location_ids = self.env['stock.quant']._get_location_available_by_product(record.product_id, record.picking_id.company_id.id or record.company_id.id)
            if location_ids:
                record.available_location_ids = location_ids
            else:
                record.available_location_ids = []

    @api.depends('product_id')
    def _compute_division(self):
        for record in self:
            record.division = record.product_id.product_tmpl_id.division

    @api.depends('product_id', 'product_id.categ_id.tracking')
    def _compute_has_chassis_tracking(self):
        for record in self:
            if record.product_id.categ_id.tracking:
                record.has_chassis_tracking = record.product_id.categ_id.tracking
            else:
                record.has_chassis_tracking = False

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('product_uom_qty'):
                vals['initial_qty'] = vals['product_uom_qty']
        return super(InheritStockMove, self).create(vals_list)
    
    def write(self,vals):
        if vals.get('product_uom_qty'):
            for record in self:
                if not record.initial_qty or record.initial_qty < vals.get('product_uom_qty',0):
                    vals['initial_qty'] = vals.get('product_uom_qty',0)
        return super(InheritStockMove, self).write(vals)
    
    def unlink(self):
        return super().unlink()

    def get_formview_action(self, access_uid=None):
        """ Override this method in order to redirect many2one towards the right model depending on access_uid """
        user = self.env.user
        if access_uid:
            user = self.env['res.users'].browse(access_uid).sudo()
        if not user.has_group('tw_stock.group_tw_stock_move_form_read'):
            raise UserError(_("You do not have access to this document."))
            
        res = super().get_formview_action(access_uid=access_uid)
        return res

    def _get_price_unit(self):
        """Use invoice line net price (incl. header discount) when available."""
        self.ensure_one()
        # Preserve purchase_mrp kit pricing logic when applicable.
        if (
            'bom_line_id' in self._fields
            and self.bom_line_id
            and self.purchase_line_id
            and self.product_id != self.purchase_line_id.product_id
            and not self._should_ignore_pol_price()
        ):
            return super()._get_price_unit()
        if self._should_ignore_pol_price():
            return super()._get_price_unit()
        price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
        line = self.purchase_line_id
        order = line.order_id
        received_qty = self._get_qty_received_without_self()
        used_invoice_price = False
        if float_compare(line.qty_invoiced, received_qty, precision_rounding=line.product_uom.rounding) > 0:
            move_layer = line.move_ids.sudo().stock_valuation_layer_ids
            invoiced_layer = line.sudo().invoice_lines.stock_valuation_layer_ids
            # value on valuation layer is in company's currency, while value on invoice line is in order's currency
            receipt_value = 0
            for layer in move_layer:
                if not layer._should_impact_price_unit_receipt_value():
                    continue
                receipt_value += layer.currency_id._convert(
                    layer.value, order.currency_id, order.company_id, layer.create_date, round=False)
            if invoiced_layer:
                receipt_value += sum(invoiced_layer.mapped(lambda l: l.currency_id._convert(
                    l.value, order.currency_id, order.company_id, l.create_date, round=False)))
            total_invoiced_value = 0
            invoiced_qty = 0
            for invoice_line in line.sudo().invoice_lines:
                if invoice_line.move_id.state != 'posted':
                    continue
                # Adjust unit price to account for line discount before taxes.
                adjusted_unit_price = invoice_line.price_unit * (1 - (invoice_line.discount / 100)) if invoice_line.discount else invoice_line.price_unit
                if invoice_line.tax_ids:
                    invoice_line_value = invoice_line.tax_ids.compute_all(
                        adjusted_unit_price,
                        currency=invoice_line.currency_id,
                        quantity=invoice_line.quantity,
                        rounding_method="round_globally",
                    )['total_void']
                else:
                    invoice_line_value = adjusted_unit_price * invoice_line.quantity
                total_invoiced_value += invoice_line.currency_id._convert(
                        invoice_line_value, order.currency_id, order.company_id, invoice_line.move_id.invoice_date, round=False)
                invoiced_qty += invoice_line.product_uom_id._compute_quantity(invoice_line.quantity, line.product_id.uom_id, rounding_method="HALF-UP")
            # TODO : currency check (This todo is migrated from odoo official)
            remaining_value = total_invoiced_value - receipt_value
            # TODO : qty_received in product uom (This todo is migrated from odoo official)
            remaining_qty = invoiced_qty - line.product_uom._compute_quantity(received_qty, line.product_id.uom_id, rounding_method="HALF-UP")
            has_remaining = (
                not order.currency_id.is_zero(remaining_value)
                and not float_is_zero(remaining_qty, precision_rounding=line.product_id.uom_id.rounding)
            )
            if order.currency_id != order.company_id.currency_id and has_remaining:
                # will be rounded during currency conversion
                price_unit = remaining_value / remaining_qty
                used_invoice_price = True
            elif has_remaining:
                price_unit = float_round(remaining_value / remaining_qty, precision_digits=price_unit_prec)
                used_invoice_price = True
            else:
                price_unit = line._get_gross_price_unit()
        else:
            price_unit = line._get_gross_price_unit()
        if order.currency_id != order.company_id.currency_id:
            convert_date = self._get_currency_convert_date()
            price_unit = order.currency_id._convert(
                price_unit, order.company_id.currency_id, order.company_id, convert_date, round=False)
        _logger.debug(
            "SVL price_unit move=%s product=%s used_invoice_price=%s price_unit=%s",
            self.id,
            self.product_id.display_name,
            used_invoice_price,
            price_unit,
        )
        if self.product_id.lot_valuated:
            return dict.fromkeys(self.lot_ids, price_unit)
        return {self.env['stock.lot']: price_unit}

    def _action_done(self, cancel_backorder=False):
        """
        Override to check if source location allows negative stock
        before executing the move that would result in negative quants.
        """
        for move in self:
            # Only check for outgoing moves from internal/transit locations
            if move.location_id.usage not in ['internal', 'transit']:
                continue
            if move.to_refund:
                continue
            
            # Get current available stock at source location
            available_qty = self.env['stock.quant'].sudo().get_stock_available(
                move.product_id.id,
                move.company_id.id,
                location_id=move.location_id.id,
                include_reserved=True
            )
            
            # Check if move would result in negative stock
            # TO DO: Error pada saat validate picking incoming (check by SKU)
            # if move.quantity > available_qty:
            #     # Check if location allows negative stock
            #     if not move.location_id._get_allow_negative_stock():
            #         raise Warning(
            #             _("Stock tidak mencukupi untuk produk '%(product)s'.\n"
            #               "Tersedia: %(available)s, Diminta: %(qty)s, Hasil: %(result)s\n"
            #               "Lokasi '%(location)s' tidak mengizinkan stock negatif.",
            #               product=move.product_id.display_name,
            #               available=available_qty,
            #               qty=move.quantity,
            #               result=available_qty - move.quantity,
            #               location=move.location_id.complete_name
            #             )
            #         )
        
        return super(InheritStockMove, self)._action_done(cancel_backorder=cancel_backorder)

    # 13: action methods

    # 14: private methods
    def _is_last_move_from_route(self):
        """
        Setup |  Type	    | Common Use Case           | When move_dest_ids is filled
        ----------------------------------------------------------------------------------------------
        Push  | (Incoming)	| Receipt → Quality → Stock	| After Validation of the previous step.
        Pull  | (Outgoing)	| Pick → Pack → Delivery	| Immediately upon creation (SO Confirmation).

        Check if this move is the last in the chain/route.
        Handles both:
        1. Chained moves already created (Pull Rules or validated Push Rules)
        2. Chained moves that WILL be created upon validation (Pending Push Rules)
        """
        self.ensure_one()
        # 1. If it already has destination moves, it's definitely not the last.
        if self.move_dest_ids.filtered(lambda m: m.state != 'cancel'):
            return False

        # 2. Look ahead for Push Rules that will trigger upon validation.
        # This logic mimics stock.move._push_apply()
        warehouse_id = self.warehouse_id or self.picking_id.picking_type_id.warehouse_id

        # Check if there is a push rule matching product and destination location
        rule = self.env['procurement.group'].sudo()._get_push_rule(self.product_id, self.location_dest_id, {
            'route_ids': self.route_ids, 
            'product_packaging_id': self.product_packaging_id, 
            'warehouse_id': warehouse_id,
        })
        
        if rule:
            # Domain check (optional but recommended for accuracy)
            if rule.push_domain:
                if not self.filtered_domain(safe_eval(rule.push_domain)):
                    # If it doesn't match the specific push domain, it might not trigger
                    # Note: Odoo loops here to find the next rule, but for a "last move" check,
                    # we only return False if ANY rule is found that would trigger.
                    return True 

            # Check special case for returns (Odoo skips push rules for returns to avoid loops)
            if not self.origin_returned_move_id or self.origin_returned_move_id.location_dest_id.id != rule.location_dest_id.id:
                return False

        return True


    def _is_first_move_from_route(self):
        """
        Check if this move is the first in the chain/route.
        A move is first if it has no origin moves (move_orig_ids).
        
        This is more reliable than checking rules, as move chains are always
        linked via move_orig_ids/move_dest_ids regardless of route configuration.
        """
        self.ensure_one()
        # Check if there are any origin moves
        # If no move_orig_ids, this is the first move in the chain
        return not self.move_orig_ids

    def _get_first_transfer(self):
        """
        Get the first transfer (picking) in the move chain.
        Traverses backwards through move_orig_ids until finding moves with no origin.
        Returns its own picking if this move is already the first transfer.
        
        :return: stock.picking recordset (first picking in chain)
        """
        self.ensure_one()
        
        current_moves = self
        visited_move_ids = set()
        
        # Traverse backwards through move_orig_ids until we find the start
        while current_moves.move_orig_ids:
            # Prevent infinite loops - check if ANY of current moves already visited
            current_move_ids = set(current_moves.ids)
            if current_move_ids & visited_move_ids:  # Set intersection - if any overlap
                break
            visited_move_ids.update(current_move_ids)

            # Stop at return chain boundary: if current move has
            # origin_returned_move_id, its move_orig_ids point to the
            # original delivery chain, not the return chain.
            if current_moves.origin_returned_move_id:
                break
            
            # Move to the origin moves (may be multiple records)
            current_moves = current_moves.move_orig_ids
        
        # Return the picking of the first moves
        first_picking = current_moves.picking_id
        
        # Fallback to self's picking if no first picking found
        if not first_picking:
            return self.picking_id
        
        return first_picking
    
    def get_first_rule_location(self):
        self.ensure_one()
        first_picking = self._get_first_transfer()
        return first_picking.location_id
    
    def _push_apply(self):
        new_moves = super()._push_apply()
        if self.lot_ids:
            new_moves.write({
                'restrict_lot_ids': [(6, 0, self.lot_ids.ids)],
            })
        return new_moves
    
    def _search_picking_for_assignation_domain(self):
        """ Odoo Try to assign the moves to an existing picking that has not been
        reserved yet and has the same procurement group, locations and picking
        type (moves should already have them identical). 
        
        We want to skip this method for picking from transaction like PO and the other transaction
        that should have their own picking.
        """
        domain = super()._search_picking_for_assignation_domain()
        domain += [('origin', '=', False)]
        return domain
        
    def _get_in_move_lines(self):
        """ Returns the `stock.move.line` records of `self` considered as incoming. It is done thanks
        to the `_should_be_valued` method of their source and destionation location as well as their
        owner.

        TW : We change the logic to create the journal entry at the last route of the picking instead of the first
        This is for pending the journal entry creation until the invoice is receipt.
        this pending schema will combined with 'Stored' state of a picking.

        :returns: a subset of `self` containing the incoming records
        :rtype: recordset
        """
        self.ensure_one()
        res = OrderedSet()
        valuation_on_last_route = bool(self.company_id.incoming_valuation_on_last_route)
        original_source_location = self.get_first_rule_location()
        # Safe fallback: if we can't determine the first source, fall back to the original (config OFF) behavior.
        if valuation_on_last_route and not original_source_location:
            valuation_on_last_route = False
        origin_valued = original_source_location._should_be_valued() if original_source_location else False

        for move_line in self.move_line_ids:
            if not move_line.picked:
                continue
            if move_line._should_exclude_for_valuation():
                continue
            if move_line.location_dest_id._should_be_valued():
                source_valued = move_line.location_id._should_be_valued()
                is_last = move_line.move_id._is_last_move_from_route()
                if source_valued:
                    # Jika source location perlu di nilai, tetapi config valuation on last route hidup
                    # Kita cek apakah original route (picking pertama nya) adalah origin not valued dan move ini
                    # berasal dari last route (picking terakhir)
                    if valuation_on_last_route and is_last:
                        if not origin_valued:
                            res.add(move_line.id)
                        # untuk kondisi MO mebentuk valuation
                        if self.picking_id.mutation_order_id:
                            res.add(move_line.id)
                elif not source_valued:
                    # Jika source location tidak perlu di nilai, tetapi config valuation on last route hidup
                    # Kita cek apakah move ini berasal dari last route (picking terakhir)
                    # Jika tidak, maka skip
                    if valuation_on_last_route:
                        if not origin_valued and is_last:
                            res.add(move_line.id)
                        first_picking = self._get_first_transfer()
                        if first_picking.return_id and is_last:
                            res.add(move_line.id)
                    else:
                        res.add(move_line.id)

        return self.env['stock.move.line'].browse(res)
    
    def _update_reserved_quantity(self, need, location_id, lot_id=None, package_id=None, owner_id=None, strict=True):
        """Override to pass move_id via context so that _update_available_quantity
        can centrally populate reservation_ids on the quant."""
        self.ensure_one()
        return super(InheritStockMove, self.with_context(
            reservation_move_id=self.id
        ))._update_reserved_quantity(need, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)

    def _get_location_from_stock_avb(self,picking_obj,product_id):
        is_main_dealer = picking_obj._is_main_dealer()
        if picking_obj.division == 'Sparepart' and is_main_dealer:
            search_obj = [('division','=',picking_obj.division),('is_temporary_location','=',False)]
            type_search_val = [('type', '=', 'StockLocation')]
            if picking_obj.picking_type_id.name in ('Hotline','hotline'):
                type_search_val.append(('value','=','hotline'))
                type_obj = self.env['tw.selection'].search(type_search_val)
                search_obj.append(('type_id','=',type_obj.id))
            else:
                type_search_val.append(('value','not in', ['hotline','nrfs']))
                type_obj = self.env['tw.selection'].search(type_search_val)
                search_obj.append(('type_id','in',type_obj.ids))
                
            location_obj = self.env['stock.location'].suspend_security().search(search_obj)
            if location_obj:
                location_ids = [loc.id for loc in location_obj]
                quant_obj = self.env['stock.quant'].suspend_security().search([
                    ('company_id','=',picking_obj.company_id.id),
                    ('product_id','=',product_id),
                    ('location_id','in',location_ids),
                    ('quantity','>',0)
                ],limit=1,order='create_date asc')
                return quant_obj
        
        return False

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """
            Override untuk mengontrol lot assignment saat reservasi move jika bypass reservasi True.
        """
        vals = super()._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        if self._should_skip_serial_auto_assign():
            vals.pop('lot_id', None)
            vals.pop('lot_name', None)
        return vals
    
    def _add_serial_move_line_to_vals_list(self, reserved_quant, quantity):
        """
        Override to skip auto-assigning serial numbers for mutation order pickings.
        
        For mutation orders, we want the user to manually select the lot/serial
        instead of auto-creating one move line per unit.
        
        By not passing reserved_quant, the move line is created without a pre-assigned
        lot_id, allowing the user to freely select any available serial number.
        """
        if self._should_skip_serial_auto_assign():
            # Return a single move line with the full quantity WITHOUT the reserved_quant
            # This creates a move line without lot_id, so user can select any serial
            return [self._prepare_move_line_vals(quantity=quantity)]
        return super()._add_serial_move_line_to_vals_list(reserved_quant, quantity)

    def _should_skip_serial_auto_assign(self):
        """
        Check if serial auto-assignment should be skipped for this move.
        
        Returns True for moves belonging to mutation order / sale order pickings.
        Extended in MO and SO module.
        Can be extended to add more conditions.
        """
        return False
        
    def _get_new_picking_values(self):
        res = super(InheritStockMove, self)._get_new_picking_values()
        for record in self:
            picking_ids = [move.picking_id.id for move in record.move_orig_ids]
            picking_obj = self.env['stock.picking'].suspend_security().search([
                ('id', 'in', picking_ids),
                ('division', '!=', False),
                ('company_id', '!=', False),
            ], limit=1)
            if picking_obj:
                res.update({
                    'division': picking_obj.division,
                    'company_id': picking_obj.company_id.id,
                    'partner_id': picking_obj.partner_id.id,
                    'origin': picking_obj.origin,
                })

        return res
        
    def _get_location_available(self):
        if self.bom_line_id:
            location_obj = self.env['stock.location'].search([('usage', '=', self.picking_id.location_id.usage),'|',('company_id', '=', self.company_id.id),('company_id', '=', False)])
        elif self.picking_id.location_id:
            location_obj = self.env['stock.location'].search([('location_id', 'child_of', self.picking_id.location_id.id)])
        else:
            location_obj = self.picking_type_id.default_location_src_id
        return location_obj
    
    def _check_valid_qty(self):
        if self.product_uom_qty:
            if self.quantity > self.product_uom_qty:
                raise Warning(_('\nQuantity (%d) cannot be greater than the demand/requested quantity (%d)!'%(self.quantity,self.product_uom_qty)))

    def _split(self, qty, restrict_partner_id=False):
        res = super(InheritStockMove, self)._split(qty, restrict_partner_id=restrict_partner_id)
        # ? next_serial_count dijadikan 0, sehingga tidak perlu membuat stock move line baru 
        if res:
            for record in res:
                if record.get('next_serial_count'):
                    record['next_serial_count'] = 0
        return res
        
