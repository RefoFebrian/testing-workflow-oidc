# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools.sql import column_exists, create_column

# 5: local imports

# 6: Import of unknown third party lib


class StockMove(models.Model):
    _inherit = "stock.move"
    
    dealer_sale_order_line_id = fields.Many2one('tw.dealer.sale.order.line', 'Dealer Sale Order Line', index='btree_not_null')

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields.append('dealer_sale_order_line_id')
        return distinct_fields

    def _get_related_invoices(self):
        """ Overridden from stock_account to return the customer invoices
        related to this stock move.
        """
        rslt = super(StockMove, self)._get_related_invoices()
        invoices = self.mapped('picking_id.dealer_sale_order_id.invoice_ids').filtered(lambda x: x.state == 'posted')
        rslt += invoices
        #rslt += invoices.mapped('reverse_entry_ids')
        return rslt

    def _get_source_document(self):
        res = super()._get_source_document()
        return self.sudo().dealer_sale_order_line_id.order_id or res

    def _get_sale_order_lines(self):
        """ Return all possible sale order lines for one stock move. """
        self.ensure_one()
        return (self + self.browse(self._rollup_move_origs() | self._rollup_move_dests())).dealer_sale_order_line_id

    def _assign_picking_post_process(self, new=False):
        super(StockMove, self)._assign_picking_post_process(new=new)
        if new:
            picking_id = self.mapped('picking_id')
            sale_order_ids = self.mapped('dealer_sale_order_line_id.order_id')
            for sale_order_id in sale_order_ids:
                picking_id.message_post_with_source(
                    'mail.message_origin_link',
                    render_values={'self': picking_id, 'origin': sale_order_id},
                    subtype_xmlid='mail.mt_note',
                )

    def _get_all_related_sm(self, product):
        return super()._get_all_related_sm(product) | self.filtered(lambda m: m.dealer_sale_order_line_id.product_id == product)
    
    def _get_new_picking_values(self):
        res = super()._get_new_picking_values()
        for record in self:
            if record.dealer_sale_order_line_id:
                res.update({
                    'division': record.dealer_sale_order_line_id.order_id.division,
                    'company_id': record.dealer_sale_order_line_id.order_id.company_id.id,
                    'partner_id': record.dealer_sale_order_line_id.order_id.partner_id.id
                })
        return res

    def _action_assign(self, force_qty=False):
        # Allow to force the lot_id usage during the reservation
        # We need to do it before the super call to be sure that the reservation
        # is done on the right lot.
        for move in self:
            if move.dealer_sale_order_line_id and move.dealer_sale_order_line_id.lot_id:
                lot = move.dealer_sale_order_line_id.lot_id
                if move.state in ['confirmed', 'partially_available', 'waiting']:
                    move._update_reserved_quantity(
                        move.product_uom_qty,
                        move.location_id,
                        lot_id=lot,
                        strict=True
                    )
                    
                    if lot.product_id.id == move.product_id.id:
                        move.write({'restrict_lot_ids': [(6, 0, [lot.id])]})
        return super(StockMove, self)._action_assign(force_qty=force_qty)
