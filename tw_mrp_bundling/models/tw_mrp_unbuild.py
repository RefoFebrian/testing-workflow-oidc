
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round
from odoo.tools.misc import clean_context
import logging
_logger = logging.getLogger(__name__)

class MrpUnbuild(models.Model):
    _inherit = "mrp.unbuild"

    @api.depends('mo_id')
    def _compute_lot_id(self):
        for order in self:
            if order.mo_id and order.mo_id.order_type != 'bundling':
                order.lot_id = order.mo_id.lot_producing_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name', False) or vals['name'] == _('New'):
                company = self.env['res.company'].sudo().search([('id', '=', vals['company_id'])])
                vals['name'] = self.env['ir.sequence'].with_company(company).get_sequence_code('XUB', company.code)
        res = super().create(vals_list)
        return res

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_("You cannot delete a production order that is not in draft state"))
        return super().unlink()
    
    def action_unbuild(self):
        self.ensure_one()
        self._check_company()
        # remove the default_* keys that was only needed in the unbuild wizard
        self.env.context = dict(clean_context(self.env.context))
        if self.product_id.tracking != 'none' and not self.lot_id.id:
            raise UserError(_('You should provide a lot number for the final product.'))

        if self.mo_id and self.mo_id.state not in ('done', 'unbuild'):
            raise UserError(_('You cannot unbuild a undone manufacturing order.'))

        consume_moves = self._generate_consume_moves()
        consume_moves._action_confirm()
        produce_moves = self._generate_produce_moves()
        produce_moves._action_confirm()
        produce_moves.quantity = 0

        finished_moves = consume_moves.filtered(lambda m: m.product_id == self.product_id)
        consume_moves -= finished_moves

        if any(produce_move.has_tracking != 'none' and not self.mo_id for produce_move in produce_moves):
            raise UserError(_('Some of your components are tracked, you have to specify a manufacturing order in order to retrieve the correct components.'))

        if any(consume_move.has_tracking != 'none' and not self.mo_id for consume_move in consume_moves):
            raise UserError(_('Some of your byproducts are tracked, you have to specify a manufacturing order in order to retrieve the correct byproducts.'))

        for finished_move in finished_moves:
            if float_compare(finished_move.product_uom_qty, finished_move.quantity, precision_rounding=finished_move.product_uom.rounding) > 0:
                finished_move_line_vals = self._prepare_finished_move_line_vals(finished_move)
                self.env['stock.move.line'].create(finished_move_line_vals)
        finished_moves.picked = True
        finished_moves._action_done()
        
        # TODO: Will fail if user do more than one unbuild with lot on the same MO. Need to check what other unbuild has aready took
        qty_already_used = defaultdict(float)
        for move in produce_moves | consume_moves:
            if float_compare(move.product_uom_qty, move.quantity, precision_rounding=move.product_uom.rounding) < 1:
                continue
            original_move = move in produce_moves and self.mo_id.move_raw_ids or self.mo_id.move_finished_ids
            original_move = original_move.filtered(lambda m: m.product_id == move.product_id)
            if not original_move:
                move.quantity = float_round(move.product_uom_qty, precision_rounding=move.product_uom.rounding)
                continue
            needed_quantity = move.product_uom_qty
            moves_lines = original_move.mapped('move_line_ids')
            
            # For bundling orders, only process move lines that match this unbuild's lot_id
            # This prevents processing all lots when multiple unbuilds are created for the same MO
            if self.mo_id.order_type == 'bundling' and self.lot_id and move in produce_moves:
                moves_lines = moves_lines.filtered(lambda ml: ml.lot_id == self.lot_id)
            
            for move_line in moves_lines:
                # Iterate over all move_lines until we unbuilded the correct quantity.
                taken_quantity = min(needed_quantity, move_line.quantity - qty_already_used[move_line])
                taken_quantity = float_round(taken_quantity, precision_rounding=move.product_uom.rounding)
                if taken_quantity:
                    if move_line.lot_id and self.mo_id.order_type == 'bundling':
                        # Change lot product back to original component product
                        move_line.lot_id.write({'product_id': move.product_id.id,'company_id': move.company_id.id, 'production_id':False})
                    
                    move_line_vals = self._prepare_move_line_vals(move, move_line, taken_quantity)
                    if move_line.owner_id:
                        move_line_vals['owner_id'] = move_line.owner_id.id
                    unbuild_move_line = self.env["stock.move.line"].create(move_line_vals)
                    needed_quantity -= taken_quantity
                    qty_already_used[move_line] += taken_quantity
                    unbuild_move_line._apply_putaway_strategy()
        (consume_moves | produce_moves).picked = True
        consume_moves._action_done()
        produce_moves._action_done()
        produced_move_line_ids = produce_moves.mapped('move_line_ids').filtered(lambda ml: ml.quantity > 0)
        consume_moves.mapped('move_line_ids').write({'produce_line_ids': [(6, 0, produced_move_line_ids.ids)]})
        if self.mo_id:
            unbuild_msg = _("%(qty)s %(measure)s unbuilt in %(order)s",
                qty=self.product_qty,
                measure=self.product_uom_id.name,
                order=self._get_html_link(),
            )
            try:
                self.mo_id.message_post(
                    body=unbuild_msg,
                    subtype_xmlid='mail.mt_note',
                )
            except Exception as e:
                _logger.error("Failed to post message on manufacturing order: %s", e)
        return self.write({'state': 'done'})
    
    def _generate_consume_moves(self):
        moves = self.env['stock.move']
        for unbuild in self:
            if unbuild.mo_id and unbuild.mo_id.order_type == 'bundling':
                # Custom logic for bundling to consolidate moves
                finished_moves = unbuild.mo_id.move_finished_ids.filtered(lambda move: move.state == 'done' and move.product_id == unbuild.product_id)
                if finished_moves:
                    # Use the first move as a template
                    template_move = finished_moves[0]
                    if template_move.product_uom_qty > 0:
                        qty = template_move.product_uom_qty if not unbuild.lot_id else 1
                        # Calculate factor to produce exactly unbuild.product_qty from this SINGLE template move
                        factor = unbuild.product_qty / qty
                        moves += unbuild._generate_move_from_existing_move(template_move, factor, unbuild.location_id, template_move.location_id)
                
                # Handle other finished moves (byproducts) normally
                other_moves = unbuild.mo_id.move_finished_ids.filtered(
                    lambda move: move.state == 'done' and move.product_id != unbuild.product_id
                )
                if unbuild.mo_id.qty_produced > 0:
                    if not unbuild.lot_id:
                        qty = unbuild.mo_id.product_uom_id._compute_quantity(unbuild.mo_id.qty_produced, unbuild.product_uom_id)
                    else:
                        qty = 1
                    factor = unbuild.product_qty / qty
                    for finished_move in other_moves:
                        moves += unbuild._generate_move_from_existing_move(finished_move, factor, unbuild.location_id, finished_move.location_id)

            elif unbuild.mo_id:
                finished_moves = unbuild.mo_id.move_finished_ids.filtered(lambda move: move.state == 'done')
                factor = unbuild.product_qty / unbuild.mo_id.product_uom_id._compute_quantity(unbuild.mo_id.qty_produced, unbuild.product_uom_id)
                for finished_move in finished_moves:
                    moves += unbuild._generate_move_from_existing_move(finished_move, factor, unbuild.location_id, finished_move.location_id)
            else:
                factor = unbuild.product_uom_id._compute_quantity(unbuild.product_qty, unbuild.bom_id.product_uom_id) / unbuild.bom_id.product_qty
                moves += unbuild._generate_move_from_bom_line(self.product_id, self.product_uom_id, unbuild.product_qty)
                for byproduct in unbuild.bom_id.byproduct_ids:
                    if byproduct._skip_byproduct_line(unbuild.product_id):
                        continue
                    quantity = byproduct.product_qty * factor
                    moves += unbuild._generate_move_from_bom_line(byproduct.product_id, byproduct.product_uom_id, quantity, byproduct_id=byproduct.id)
        return moves

    def _prepare_finished_move_line_vals(self, finished_move):
        return {
            'move_id': finished_move.id,
            'lot_id': self.lot_id.id,
            'quantity': finished_move.product_uom_qty - finished_move.quantity,
            'product_id': finished_move.product_id.id,
            'product_uom_id': finished_move.product_uom.id,
            'location_id': finished_move.location_id.id,
            'location_dest_id': finished_move.location_dest_id.id,
        }

    def _prepare_move_line_vals(self, move, origin_move_line, taken_quantity):
        return {
            'move_id': move.id,
            'lot_id': origin_move_line.lot_id.id,
            'quantity': 1 if self.lot_id else taken_quantity,
            'product_id': move.product_id.id,
            'product_uom_id': origin_move_line.product_uom_id.id,
            'location_id': move.location_id.id,
            'location_dest_id': move.location_dest_id.id,
        }
