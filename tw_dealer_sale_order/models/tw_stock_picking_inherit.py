# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.osv import expression

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools.sql import column_exists, create_column
from dateutil.relativedelta import relativedelta

# 5: local imports

# 6: Import of unknown third party lib

class StockPicking(models.Model):
    _inherit = "stock.picking"

    dealer_sale_order_id = fields.Many2one('tw.dealer.sale.order', compute="_compute_dealer_sale_order_id", inverse="_set_dealer_sale_order_id", string="Dealer Sales Order", store=True, index='btree_not_null')

    @api.depends('group_id')
    def _compute_dealer_sale_order_id(self):
        for picking in self:
            picking.dealer_sale_order_id = picking.group_id.dealer_sale_order_id

    def _action_done(self):
        res = super()._action_done()
        sale_order_lines_vals = []
        for move in self.move_ids:
            sale_order = move.picking_id.dealer_sale_order_id
            # Creates new SO line only when pickings linked to a sale order and
            # for moves with qty. done and not already linked to a SO line.
            if not sale_order \
                or (move.location_dest_id.usage != 'customer' and not (move.location_id.usage == 'customer' and move.to_refund)) \
                or move.dealer_sale_order_line_id \
                or not move.picked:
                continue
            product = move.product_id
            quantity = move.quantity
            if move.to_refund:
                quantity *= -1

            so_line_vals = {
                'move_ids': [(4, move.id, 0)],
                'name': product.display_name,
                'order_id': sale_order.id,
                'product_id': product.id,
                'product_uom_qty': 0,
                'qty_delivered': quantity,
                'product_uom': move.product_uom.id,
            }
            if product.invoice_policy == 'delivery':
                # Check if there is already a SO line for this product to get
                # back its unit price (in case it was manually updated).
                so_line = sale_order.order_line.filtered(lambda sol: sol.product_id == product)
                if so_line:
                    so_line_vals['price_unit'] = so_line[0].price_unit
            elif product.invoice_policy == 'order':
                # No unit price if the product is invoiced on the ordered qty.
                so_line_vals['price_unit'] = 0
            sale_order_lines_vals.append(so_line_vals)

        if sale_order_lines_vals:
            self.env['tw.dealer.sale.order.line'].with_context(skip_procurement=True).create(sale_order_lines_vals)

        # Trigger DSO 'Done' check after picking is validated
        for picking in self:
            if picking.dealer_sale_order_id:
                picking.dealer_sale_order_id.sudo()._check_dso_done()
                picking.dealer_sale_order_id.sudo()._check_dso_revert_sale()

        return res

    def _set_dealer_sale_order_id(self):
        if self.group_id:
            self.group_id.dealer_sale_order_id = self.dealer_sale_order_id
        else:
            if self.dealer_sale_order_id:
                vals = {
                    'dealer_sale_order_id': self.dealer_sale_order_id.id,
                    'name': self.dealer_sale_order_id.name,
                }
            else:
                vals = {}

            pg = self.env['procurement.group'].create(vals)
            self.group_id = pg

    def _prepare_update_lot(self,picking,move,move_line):
        res = super()._prepare_update_lot(picking, move, move_line)
        if 'dealer_sale_order_id' in self._fields and picking.dealer_sale_order_id and move._is_last_move_from_route():
            res.update({
                'dealer_sale_order_id': picking.dealer_sale_order_id.id,
                'location_id': move_line.location_dest_id.id,
                'partner_id': picking.partner_id.id
            })
            if move_line.lot_id.state not in ('paid', 'paid_offtr'):
                res.update({'state': 'sold'})

        return res

    def _auto_init(self):
        """
        Create related field here, too slow
        when computing it afterwards through _compute_related.

        Since group_id.dealer_sale_order_id is created in this module,
        no need for an UPDATE statement.
        """
        if not column_exists(self.env.cr, 'stock_picking', 'dealer_sale_order_id'):
            create_column(self.env.cr, 'stock_picking', 'dealer_sale_order_id', 'int4')
        return super()._auto_init()

    def _log_less_quantities_than_expected(self, moves):
        """ Log an activity on sale order that are linked to moves. The
        note summarize the real processed quantity and promote a
        manual action.

        :param dict moves: a dict with a move as key and tuple with
        new and old quantity as value. eg: {move_1 : (4, 5)}
        """

        def _keys_in_groupby(sale_line):
            """ group by order_id and the sale_person on the order """
            return (sale_line.order_id, sale_line.order_id.user_id)

        def _render_note_exception_quantity(moves_information):
            """ Generate a note with the picking on which the action
            occurred and a summary on impacted quantity that are
            related to the sale order where the note will be logged.

            :param moves_information dict:
            {'move_id': ['sale_order_line_id', (new_qty, old_qty)], ..}

            :return: an html string with all the information encoded.
            :rtype: str
            """
            origin_moves = self.env['stock.move'].browse([move.id for move_orig in moves_information.values() for move in move_orig[0]])
            origin_picking = origin_moves.mapped('picking_id')
            values = {
                'origin_moves': origin_moves,
                'origin_picking': origin_picking,
                'moves_information': moves_information.values(),
            }
            return self.env['ir.qweb']._render('sale_stock.exception_on_picking', values)

        documents = self.sudo()._log_activity_get_documents(moves, 'dealer_sale_order_line_id', 'DOWN', _keys_in_groupby)
        self._log_activity(_render_note_exception_quantity, documents)

        return super(StockPicking, self)._log_less_quantities_than_expected(moves)

    def _can_return(self):
        self.ensure_one()
        return super()._can_return() or self.dealer_sale_order_id

