
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round
from odoo.tools.misc import groupby as tools_groupby

from collections import defaultdict

import logging
_log = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    date = fields.Date('Date', default=fields.Date.today())
    order_type = fields.Selection([
        ('regular', 'Regular'),
        ('bundling', 'Bundling'),
    ], string='Order Type', default='regular')
    state = fields.Selection(selection_add=[
        ('done',),
        ('unbuild','Unbuild'),
    ])
    show_produce_all = fields.Boolean(compute='_compute_show_produce', help='Technical field to check if produce all button can be shown')
    
    # Audit Trail
    confirm_uid = fields.Many2one('res.users', 'Confirmed by')
    confirm_date = fields.Datetime('Confirmed on')
    done_uid = fields.Many2one('res.users', 'Done by')
    done_date = fields.Datetime('Done on')
    unbuild_uid = fields.Many2one('res.users', 'Unbuild by')
    unbuild_date = fields.Datetime('Unbuild on')
    
    # Relational fields
    move_raw_ids = fields.One2many('stock.move', 'raw_material_production_id', string='Move Raw Material')
    move_raw_lot_ids = fields.One2many('stock.move.line', related='move_raw_ids.move_line_ids', string='Serial Number Material')
    move_lot_ids = fields.One2many('stock.move.line', 'production_id', string='Detail Serial Number')

    @api.depends('bom_id')
    def _compute_product_qty(self):
        for production in self:
            if production.state != 'draft' or production.order_type == 'bundling':
                continue
            if production.bom_id and production._origin.bom_id != production.bom_id:
                production.product_qty = production.bom_id.product_qty
            elif not production.bom_id:
                production.product_qty = 1.0

    @api.depends(
        'move_raw_ids.state', 'move_raw_ids.quantity', 'move_finished_ids.state',
        'workorder_ids.state', 'product_qty', 'qty_producing', 'move_raw_ids.picked', 'unbuild_count')
    def _compute_state(self):
        super()._compute_state()
        for production in self:
            if production.state == 'done' and production.unbuild_count == production.product_qty:
                production.state = 'unbuild'
    
    @api.depends('state', 'product_qty', 'qty_producing','order_type')
    def _compute_show_produce(self):
        for production in self:
            if production.order_type == 'bundling':
                state_ok = production.state == 'to_close'
            else:
                state_ok = production.state in ('confirmed', 'progress', 'to_close')
            qty_none_or_all = production.qty_producing in (0, production.product_qty)
            production.show_produce_all = state_ok and qty_none_or_all
            production.show_produce = state_ok and not qty_none_or_all

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name', False) or vals['name'] == _('New'):
                if vals['order_type'] == 'bundling':
                    company = self.env['res.company'].sudo().search([('id', '=', vals['company_id'])])
                    vals['name'] = self.env['ir.sequence'].with_company(company).get_sequence_code('UB', company.code)
        res = super().create(vals_list)
        return res

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_("You cannot delete a production order that is not in draft state"))
        return super().unlink()

    def action_confirm(self):
        self.validate_bundling_production()
        if self.order_type == 'bundling':
            self._check_bundling_stock_availability()
        res = super().action_confirm()
        self.write({
            'confirm_uid': self.env.user.id,
            'confirm_date': fields.Datetime.now(),
            'state': 'confirmed'
        })
        return res
    
    def action_generate_serial(self):
        self.ensure_one()
        if self.order_type == 'bundling':
            self._check_bundling_stock_availability()
        if self.order_type != 'bundling':
            return super().action_generate_serial()
        return True

    def action_open_upload_serial_wizard(self):
        self.ensure_one()
        return {
            'name': _('Upload Serial Number'),
            'type': 'ir.actions.act_window',
            'res_model': 'tw.upload.serial.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_production_id': self.id},
        }
        
    def action_start_production(self):
        self.ensure_one()
        if self.state != 'confirmed' or self.order_type != 'bundling':
            raise UserError(_("You can only start production for confirmed bundling orders."))
            
        bundling_loc = self.picking_type_id.warehouse_id.bundling_location_id
        if not bundling_loc:
            raise UserError(_("Please configure a Bundling Location on the warehouse %s.") % self.picking_type_id.warehouse_id.name)
            
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', self.picking_type_id.warehouse_id.id)
        ], limit=1)
        
        if not picking_type:
            raise UserError(_("No internal transfer operation type found for warehouse %s.") % self.picking_type_id.warehouse_id.name)
            
        # Extract reservation details before unreserving
        move_details = []
        move_raw = self.move_raw_ids.sudo()
        for move in move_raw:
            if move.state not in ('done', 'cancel') and move.product_uom_qty > 0:
                lines = []
                for ml in move.move_line_ids:
                    lines.append({
                        'product_id': ml.product_id.id,
                        'product_uom_id': ml.product_uom_id.id,
                        'quantity': ml.quantity,
                        'lot_id': ml.lot_id.id if ml.lot_id else False,
                        'location_id': ml.location_id.id,
                    })
                move_details.append({
                    'move': move,
                    'product_id': move.product_id.id,
                    'product_uom_qty': move.product_uom_qty,
                    'product_uom': move.product_uom.id,
                    'location_id': move.location_id.id,
                    'lines': lines
                })

        # Unreserve MO to free the stock
        move_raw._do_unreserve()
        
        # Create Picking
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': self.location_src_id.id,
            'location_dest_id': bundling_loc.id,
            'origin': self.name,
            'name': self.name + 'M',
            'company_id': self.company_id.id,
        })
        
        for detail in move_details:
            new_move = self.env['stock.move'].create({
                'name': self.name,
                'reference': self.name,
                'product_id': detail['product_id'],
                'product_uom_qty': detail['product_uom_qty'],
                'product_uom': detail['product_uom'],
                'location_id': detail['location_id'],
                'location_dest_id': bundling_loc.id,
                'company_id': self.company_id.id,
                'picking_id': picking.id,
            })
        picking.action_confirm()
        # Clean auto-reservations from picking safely
        picking.do_unreserve()

        for detail in move_details:
            move = picking.move_ids.filtered(lambda m: m.product_id.id == detail['product_id'])
            for line in detail['lines']:
                if line['quantity'] > 0:
                    self.env['stock.move.line'].create({
                        'move_id': move.id,
                        'product_id': line['product_id'],
                        'product_uom_id': line['product_uom_id'],
                        'quantity': line['quantity'],
                        'lot_id': line['lot_id'],
                        'location_id': line['location_id'],
                        'location_dest_id': bundling_loc.id,
                        'company_id': self.company_id.id,
                        'picking_id': picking.id,
                        'production_id': self.id,
                    })
                    
        picking.move_ids.picked = True
        picking.with_context(skip_sms=True).button_validate()

        # Update MO raw moves to consume from the bundling location.
        # _return_stock_from_bundling detects this when button_mark_done is called.
        for move in move_raw.filtered(lambda m: m.state not in ('done', 'cancel')):
            move.write({'location_id': bundling_loc.id})
        self.sudo().write({'location_src_id': bundling_loc.id})

        # Reserve the exact serial numbers from the bundling location
        self.action_assign()

        # Set production_id so lots appear in move_lot_ids (used by _post_inventory)
        for move in move_raw.filtered(lambda m: m.state not in ('done', 'cancel')):
            move.move_line_ids.filtered(lambda ml: not ml.production_id).write({
            'production_id': self.id,
        })

        # Set qty_producing so that Odoo's _compute_state transitions from
        # 'in_progress' -> 'to_close', making the "Produce All" button visible.
        self.qty_producing = self.product_qty
        return super().action_start()

    def _do_return_to_stock(self, bundling_loc, stock_loc):
        """Helper to move stock back from bundling to warehouse stock."""
        moves_in_bundling = self.move_raw_ids.filtered(
            lambda m: m.location_id == bundling_loc and m.state not in ('done', 'cancel')
        )
        if not moves_in_bundling:
            return

        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id', '=', self.picking_type_id.warehouse_id.id)
        ], limit=1)
        if not picking_type:
            return

        return_details = []
        for move in moves_in_bundling:
            lines = [
                {
                    'product_id': ml.product_id.id,
                    'product_uom_id': ml.product_uom_id.id,
                    'quantity': ml.quantity,
                    'lot_id': ml.lot_id.id if ml.lot_id else False,
                }
                for ml in move.move_line_ids if ml.quantity > 0
            ]
            if lines:
                return_details.append({
                    'product_id': move.product_id.id,
                    'product_uom_qty': sum(l['quantity'] for l in lines),
                    'product_uom': move.product_uom.id,
                    'lines': lines,
                })

        if not return_details:
            return

        # Unreserve the MO so we can physically return the stock
        self.move_raw_ids._do_unreserve()

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': bundling_loc.id,
            'location_dest_id': stock_loc.id,
            'name': self.name + 'R',
            'origin': _("Return to stock %s") % self.name,
            'company_id': self.company_id.id,
        })
        for detail in return_details:
            new_move = self.env['stock.move'].create({
                'name': picking.origin,
                'product_id': detail['product_id'],
                'product_uom_qty': detail['product_uom_qty'],
                'product_uom': detail['product_uom'],
                'location_id': bundling_loc.id,
                'location_dest_id': stock_loc.id,
                'company_id': self.company_id.id,
                'picking_id': picking.id,
            })
            for line in detail['lines']:
                self.env['stock.move.line'].create({
                    'move_id': new_move.id,
                    'product_id': line['product_id'],
                    'product_uom_id': line['product_uom_id'],
                    'quantity': line['quantity'],
                    'lot_id': line['lot_id'],
                    'location_id': bundling_loc.id,
                    'location_dest_id': stock_loc.id,
                    'company_id': self.company_id.id,
                    'picking_id': picking.id,
                })
        picking.action_confirm()
        picking.move_ids.picked = True
        picking.with_context(skip_sms=True).button_validate()

        # Reset MO source location
        self.sudo().write({'location_src_id': stock_loc.id})
        for move in self.move_raw_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
            move.write({'location_id': stock_loc.id})

        # Re-reserve from stock_loc
        self.action_assign()
        self.move_raw_ids.move_line_ids.filtered(lambda ml: not ml.production_id).write({
            'production_id': self.id,
        })

    def _return_stock_from_bundling(self):
        """Move stock back from bundling location to original warehouse stock."""
        self.ensure_one()
        bundling_loc = self.picking_type_id.warehouse_id.bundling_location_id
        stock_loc = self.picking_type_id.warehouse_id.lot_stock_id
        if bundling_loc and stock_loc:
            self._do_return_to_stock(bundling_loc, stock_loc)

    def _check_sn_uniqueness(self):
        """Bypass for bundling.
        
        For bundling, the finished product's serial number is swapped from
        the component lot in _post_inventory. Odoo's native uniqueness check
        would trigger a conflict here because the lot still technically
        belongs to the component product at this stage.
        """
        if self.order_type == 'bundling':
            return
        return super()._check_sn_uniqueness()

    def button_mark_done(self):
        self.sudo().with_company(self.company_id).validate_bundling_production()
        self.sudo().with_company(self.company_id).validate_bundling_stock()

        if self.order_type == 'bundling':
            # Move stock back from the Bundling location to the original stock location.
            # This eliminates the "serial already assigned" conflict that Odoo raises when
            # a serial is present in a real (non-virtual) location during production.

            if self.qty_producing == 0:
                self.qty_producing = self.product_qty
                self._set_qty_producing()

            for move in self.move_raw_ids:
                if move.state not in ('done', 'cancel') and move.product_uom_qty > 0:
                    move.picked = True

        done_transaction = self.with_company(self.company_id)
        mark_done = super(MrpProduction, done_transaction).button_mark_done()
        self.sudo()._clean_quant_after_production()
        self.write({
            'done_uid': self.env.user.id,
            'done_date': fields.Datetime.now(),
        })
        return mark_done

    
    def button_unbuild(self):
        if self.order_type == 'bundling':
            return self._unbuild_bundling_order()
        unbuild = super().button_unbuild()
        self.write({
            'unbuild_uid': self.env.user.id,
            'unbuild_date': fields.Datetime.now(),
        })
        return unbuild

    def action_cancel(self):
        for production in self:
            if production.order_type == 'bundling':
                bundling_loc = production.picking_type_id.warehouse_id.bundling_location_id
                stock_loc = production.picking_type_id.warehouse_id.lot_stock_id
                if bundling_loc and stock_loc:
                    production._do_return_to_stock(bundling_loc, stock_loc)
        return super().action_cancel()

    def pre_button_mark_done(self):
        pre_mark = super().pre_button_mark_done()
        if self.order_type == 'bundling' and pre_mark != True and pre_mark.get('xml_id') == 'mrp.action_mrp_batch_produce':
            return True
        return pre_mark

    def _set_quantities(self):
        """Override to skip auto-generating a lot_producing_id for bundling orders.
        
        Odoo's native _set_quantities() calls action_generate_serial() when no
        lot_producing_id is set, which auto-creates a serial number for the finished
        product. For bundling orders, the finished product's serial number is derived
        from the component lots in _post_inventory, so we must skip this step.
        """
        if self.order_type != 'bundling':
            return super()._set_quantities()

        # For bundling: only propagate qty_producing to component moves.
        # Skip lot_producing_id auto-generation — _post_inventory handles that.
        # NOTE: _set_qty_producing already handles the serial qty clamp for non-bundling,
        # and skips it for bundling (see override below), so we can call it directly.
        self._set_qty_producing(pick_manual_consumption_moves=True)


    def _set_qty_producing(self, pick_manual_consumption_moves=True):
        if self.product_id.tracking == 'serial':
            qty_producing_uom = self.product_uom_id._compute_quantity(self.qty_producing, self.product_id.uom_id, rounding_method='HALF-UP')
            # allow changing a non-zero value to a 0 to not block mass produce feature
            if self.order_type != 'bundling':
                if qty_producing_uom != 1 and not (qty_producing_uom == 0 and self._origin.qty_producing != self.qty_producing):
                    self.qty_producing = self.product_id.uom_id._compute_quantity(1, self.product_uom_id, rounding_method='HALF-UP')

        # waiting for a preproduction move before assignement
        is_waiting = self.warehouse_id.manufacture_steps != 'mrp_one_step' and self.picking_ids.filtered(lambda p: p.picking_type_id == self.warehouse_id.pbm_type_id and p.state not in ('done', 'cancel'))

        # For bundling orders, skip finished product moves entirely.
        # The lot-swap for finished products is handled in _post_inventory.
        # Including finished moves here triggers Odoo's serial conflict check because
        # the component serials are now back in the stock location.
        if self.order_type == 'bundling':
            move_iter = self.move_raw_ids.filtered(lambda m: not is_waiting or m.product_id.tracking == 'none')
        else:
            move_iter = (
                self.move_raw_ids.filtered(lambda m: not is_waiting or m.product_id.tracking == 'none')
                | self.move_finished_ids.filtered(lambda m: m.product_id != self.product_id or m.product_id.tracking == 'serial')
            )

        for move in move_iter:
            # picked + manual means the user set the quantity manually
            if move.manual_consumption and move.picked:
                continue

            # sudo needed for portal users
            if move.sudo()._should_bypass_set_qty_producing():
                continue

            new_qty = float_round((self.qty_producing - self.qty_produced) * move.unit_factor, precision_rounding=move.product_uom.rounding)
            move._set_quantity_done(new_qty)
            if (not move.manual_consumption or pick_manual_consumption_moves) \
                    and move.quantity \
                    and (move.product_id != self.product_id or not move.production_id or move.product_id.tracking != 'serial'):
                move.picked = True

    def _post_inventory(self, cancel_backorder=False):
        if self.order_type != 'bundling':
            return super()._post_inventory(cancel_backorder=cancel_backorder)

        moves_to_do, moves_not_to_do, moves_to_cancel = set(), set(), set()
        for move in self.move_raw_ids:
            if move.state == 'done':
                moves_not_to_do.add(move.id)
            elif not move.picked:
                moves_to_cancel.add(move.id)
            elif move.state != 'cancel':
                moves_to_do.add(move.id)

        self.with_context(skip_mo_check=True).env['stock.move'].browse(moves_to_do)._action_done(cancel_backorder=cancel_backorder)
        self.with_context(skip_mo_check=True).env['stock.move'].browse(moves_to_cancel)._action_cancel()
        moves_to_do = self.move_raw_ids.filtered(lambda x: x.state == 'done') - self.env['stock.move'].browse(moves_not_to_do)
        # Create a dict to avoid calling filtered inside for loops.
        moves_to_do_by_order = defaultdict(lambda: self.env['stock.move'], [
            (key, self.env['stock.move'].concat(*values))
            for key, values in tools_groupby(moves_to_do, key=lambda m: m.raw_material_production_id.id)
        ])
        for order in self:
            # Menghitung durasi WO
            for workorder in order.workorder_ids:
                if workorder.state not in ('done', 'cancel'):
                    workorder.duration_expected = workorder._get_duration_expected()
                if workorder.duration == 0.0:
                    workorder.duration = workorder.duration_expected
                    workorder.duration_unit = round(workorder.duration / max(workorder.qty_produced, 1), 2)
            order._cal_price(moves_to_do_by_order[order.id])

            # Menggunakan lot dari komponen sebagai lot hasil produksi
            finish_moves = order.move_finished_ids.filtered(lambda m: m.product_id == order.product_id and m.state not in ('done', 'cancel'))
            # We must only look at move lines linked to our raw moves to avoid double counting 
            # lines from the Bundling internal pickings (which also share the production_id).
            move_lot_ids = order.move_raw_ids.move_line_ids.filtered(lambda m: m.state == 'done' and m.lot_id)
            # Use only the FIRST finish move as a template to avoid the N×N copy explosion.
            # finish_moves may already be split into N moves by Odoo's _set_qty_producing,
            # so we must reduce to a single base before iterating over lots.
            if finish_moves and move_lot_ids:
                # To prevent "already assigned" unique constraint errors, we must ensure
                # no lots already exist for the finished product with these names.
                # This can happen if Odoo auto-generated them or from previous failed attempts.
                lot_names = move_lot_ids.lot_id.mapped('name')
                duplicate_lots = self.env['stock.lot'].search([
                    ('name', 'in', lot_names),
                    ('product_id', '=', finish_moves[0].product_id.id),
                    ('company_id', '=', finish_moves[0].company_id.id),
                ])
                if duplicate_lots:
                    # Clear out duplicates to allow the component lot to take over the identity
                    duplicate_lots.sudo().unlink()

                move_lot_ids.lot_id.write({
                    'product_id': finish_moves[0].product_id.id,
                    'company_id': finish_moves[0].company_id.id,
                    'production_id': self.id,
                })
                finish_moves.move_line_ids.unlink()
                base_move = finish_moves[0]
                for move_lot in move_lot_ids:
                    separated_move = base_move.copy({
                        'quantity': move_lot.quantity,
                        'price_unit': self._get_new_valuation(move_lot),
                    })
                    separated_move.lot_ids = move_lot.lot_id
                # Delete ALL original finish_moves (not just the first) to avoid leftovers
                finish_moves.unlink()
                
        moves_to_finish = self.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        moves_to_finish.picked = True
        moves_to_finish._action_done(cancel_backorder=cancel_backorder)
        return True
    
    def _clean_quant_after_production(self):
        """
        Clean up quants after production by finding quants grouped by lot.
        If a lot has quants with quantities of -1 and 1 respectively, update them to 0.
        Jika tidak di clean, maka compute location tidak berjalan dan location di lot akan hilang
        """
        # Search for all quants with quantity -1 or 1
        quants = self.env['stock.quant'].sudo().search([
            ('quantity', 'in', [-1, 1]),
            ('lot_id', '!=', False),
            ('location_id', '=', self.production_location_id.id),
            ('lot_id', 'in', self.move_lot_ids.lot_id.ids)
        ])
        
        # Group quants by lot_id
        quants_by_lot = defaultdict(lambda: self.env['stock.quant'])
        for quant in quants:
            quants_by_lot[quant.lot_id.id] |= quant
        
        # Process each lot
        for lot_id, lot_quants in quants_by_lot.items():
            # Check if this lot has both -1 and 1 quantities
            quantities = lot_quants.mapped('quantity')
            if -1 in quantities and 1 in quantities:
                # Update all quants for this lot to quantity 0
                lot_quants.sudo().write({'quantity': 0})

    def _get_new_valuation(self, move_line):
        components = self.move_raw_ids.filtered(lambda ln: ln.product_id.tracking != "serial")
        component_price = sum(
            line.product_id.standard_price * line.quantity
            for component in components
            for line in component.move_line_ids
        ) / self.product_qty
        labor_price = sum(wo._cal_cost() for wo in self.workorder_ids) / self.product_qty
        unit_price = abs(move_line.suspend_security().lot_id.stock_valuation_layer_ids[-1].value)
        new_valuation = component_price + labor_price + unit_price
        return new_valuation        

    def _prepare_finished_extra_vals(self):
        self.ensure_one()
        if self.order_type != 'bundling':
            return super()._prepare_finished_extra_vals()
        return {}
    
    def _post_labour(self):
        for mo in self:
            if mo.with_company(mo.company_id).product_id.valuation != 'real_time':
                continue

            product_accounts = mo.product_id.product_tmpl_id.get_product_accounts()
            
            # Group workorders by partner
            wo_by_partner = defaultdict(lambda: self.env['mrp.workorder'])
            for wo in mo.workorder_ids:
                partner = wo.workcenter_id.partner_id
                if not partner:
                    raise UserError(_("Partner belum di set pada Work Center %s") % wo.workcenter_id.name)
                wo_by_partner[partner] |= wo

            for partner, wos in wo_by_partner.items():
                labour_amounts = defaultdict(float)
                workorders_by_account = defaultdict(lambda: self.env['mrp.workorder'])
                
                for wo in wos:
                    expense_account = wo.workcenter_id.expense_account_id
                    if not expense_account:
                        raise UserError(_("Expense Account belum di set pada Work Center %s") % wo.workcenter_id.name)
                    bundling_account = wo.workcenter_id.bundling_account_id
                    if not bundling_account:
                        raise UserError(_("Bundling Account belum di set pada Work Center %s") % wo.workcenter_id.name)

                    cost = wo.company_id.currency_id.round(wo._cal_cost())
                    if wo.company_id.currency_id.is_zero(cost):
                        continue
                        
                    labour_amounts[expense_account] += cost
                    labour_amounts[bundling_account] -= cost
                    workorders_by_account[expense_account] |= wo

                if not labour_amounts:
                    continue

                desc = _('%s - Labour - %s', mo.name, partner.name)
                division = mo.product_id.division
                vals = {
                    'journal_id': product_accounts['stock_journal'].id,
                    'date': fields.Date.context_today(self),
                    'company_id': self.company_id.id,
                    'division': division,
                    'ref': desc,
                    'move_type': 'entry',
                    'line_ids': [(0, 0, {
                        'company_id': self.company_id.id,
                        'partner_id': partner.id,
                        'name': desc,
                        'ref': desc,
                        'division': division,
                        'balance': -amt,
                        'account_id': acc.id,
                    }) for acc, amt in labour_amounts.items()]
                }
                account_move = self.env['account.move'].sudo().create(vals)
                account_move._post()
                
                for line in account_move.line_ids:
                    if line.account_id in workorders_by_account:
                        workorders_by_account[line.account_id].time_ids.write({'account_move_line_id': line.id})

    def _unbuild_bundling_order(self):
        self.ensure_one()
        unbuilds = self.env['mrp.unbuild']
        for move in self.move_lot_ids:
            if move.lot_id:
                unbuild_vals = self._prepare_unbuild_vals(move.lot_id)
                unbuilds += self.env['mrp.unbuild'].sudo().create(unbuild_vals)
        for unbuild in unbuilds:
            unbuild.action_unbuild()
        self._clean_quant_after_production()
    
    def _prepare_unbuild_vals(self,lot):
        vals = {
            'product_id': self.product_id.id,
            'lot_id': lot.id,
            'mo_id': self.id,
            'company_id': self.company_id.id,
            'location_id': self.location_dest_id.id,
            'location_dest_id': self.location_src_id.id,
        }
        return vals

    def validate_bundling_production(self):
        for production in self:
            if production.order_type == 'bundling':
                if production.product_id.tracking != 'serial':
                    raise UserError(_("Product %s must be tracked by serial number for bundling production") % production.product_id.name)
                
                move_raw_with_lot_ids = production.move_raw_ids.filtered(lambda ln: ln.product_id.tracking == "serial")
                if len(move_raw_with_lot_ids) != 1:
                    raise UserError(_("Only one raw material with lot/serial number is allowed for bundling production"))
                
                lot_ids = production.move_lot_ids.filtered(lambda m: m.lot_id).mapped('lot_id')
                if len(lot_ids) != len(set(lot_ids.ids)):
                    # Find duplicate lot names
                    lot_names = lot_ids.mapped('name')
                    duplicates = [name for name in lot_names if lot_names.count(name) > 1]
                    raise UserError(_("Duplicate serial numbers found: %s") % ', '.join(set(duplicates)))
    
    def validate_bundling_stock(self):
        for production in self:
            # Check for duplicate lots in move_lot_ids
            
            for move in production.move_raw_ids:
                qty_available = self.env['stock.quant'].get_stock_available(move.product_id.id, move.company_id.id, location_id=move.location_id.id, include_reserved=True)
                if move.product_qty > qty_available:
                    raise ValidationError(_("Validation Failed : Not enough stock for product %s in location %s. Available: %s. Needed: %s") % (move.product_id.name, move.location_id.complete_name, qty_available, move.product_qty))
                
                if production.state in ('draft', 'approved'):
                    continue
                # Check supply only when necesary
                if move.product_uom_qty != move.quantity:
                    raise UserError(_("Demand and supply quantity of product %s are not equal. \n Demand : %s \n Supply : %s") % (move.product_id.name, move.product_uom_qty, move.quantity))
                

    def _check_bundling_stock_availability(self):
        for production in self:
            for move in production.move_raw_ids:
                # To support multi-step manufacturing, we check the main warehouse stock location
                # rather than the immediate pre-production location, because the stock hasn't moved yet.
                warehouse_stock_location = production.picking_type_id.warehouse_id.lot_stock_id
                check_location = warehouse_stock_location if warehouse_stock_location else move.location_id
                
                qty_available = self.env['stock.quant'].get_stock_available(
                    move.product_id.id, 
                    move.company_id.id, 
                    location_id=check_location.id
                )
                if move.product_qty > qty_available:
                    raise ValidationError(_("Not enough stock for product %s in location %s. Available: %s. Needed: %s") % (
                        move.product_id.name, 
                        check_location.name, 
                        qty_available, 
                        move.product_qty
                    ))

                