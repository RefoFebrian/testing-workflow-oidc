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
    
    part_sales_line_id = fields.Many2one('tw.part.sales.line', 'Part Sales Line', index='btree_not_null')

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields.append('part_sales_line_id')
        return distinct_fields

    def _get_related_invoices(self):
        """ Overridden from stock_account to return the customer invoices
        related to this stock move.
        """
        rslt = super(StockMove, self)._get_related_invoices()
        invoices = self.mapped('picking_id.part_sales_id.invoice_ids').filtered(lambda x: x.state == 'posted')
        rslt += invoices
        #rslt += invoices.mapped('reverse_entry_ids')
        return rslt

    def _get_source_document(self):
        res = super()._get_source_document()
        return self.sudo().part_sales_line_id.order_id or res

    def _get_part_sales_lines(self):
        """ Return all possible part sales lines for one stock move. """
        self.ensure_one()
        return (self + self.browse(self._rollup_move_origs() | self._rollup_move_dests())).part_sales_line_id

    def _assign_picking_post_process(self, new=False):
        super(StockMove, self)._assign_picking_post_process(new=new)
        if new:
            picking_id = self.mapped('picking_id')
            part_sales_ids = self.mapped('part_sales_line_id.order_id')
            for part_sales_id in part_sales_ids:
                picking_id.message_post_with_source(
                    'mail.message_origin_link',
                    render_values={'self': picking_id, 'origin': part_sales_id},
                    subtype_xmlid='mail.mt_note',
                )

    def _get_all_related_sm(self, product):
        return super()._get_all_related_sm(product) | self.filtered(lambda m: m.part_sales_line_id.product_id == product)
    
    def _get_new_picking_values(self):
        res = super()._get_new_picking_values()
        for record in self:
            if record.part_sales_line_id:
                res.update({
                    'division': record.part_sales_line_id.order_id.division,
                    'company_id': record.part_sales_line_id.order_id.company_id.id,
                    'partner_id': record.part_sales_line_id.order_id.partner_id.id
                })
        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _should_show_lot_in_invoice(self):
        return 'customer' in {self.location_id.usage, self.location_dest_id.usage}


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    part_sales_id = fields.Many2one('tw.part.sales', 'Part Sales')


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields += ['part_sales_line_id', 'partner_id', 'sequence', 'to_refund']
        return fields


class StockPicking(models.Model):
    _inherit = "stock.picking"

    part_sales_id = fields.Many2one('tw.part.sales', compute="_compute_part_sales_id", inverse="_set_part_sales_id", string="Part Sales", store=True, index='btree_not_null')

    @api.depends('group_id')
    def _compute_part_sales_id(self):
        for picking in self:
            picking.part_sales_id = picking.group_id.part_sales_id

    def _set_part_sales_id(self):
        if self.group_id:
            self.group_id.part_sales_id = self.part_sales_id
        else:
            if self.part_sales_id:
                vals = {
                    'part_sales_id': self.part_sales_id.id,
                    'name': self.part_sales_id.name,
                }
            else:
                vals = {}

            pg = self.env['procurement.group'].create(vals)
            self.group_id = pg

    def _auto_init(self):
        """
        Create related field here, too slow
        when computing it afterwards through _compute_related.

        Since group_id.part_sales_id is created in this module,
        no need for an UPDATE statement.
        """
        if not column_exists(self.env.cr, 'stock_picking', 'part_sales_id'):
            create_column(self.env.cr, 'stock_picking', 'part_sales_id', 'int4')
        return super()._auto_init()

    def _action_done(self):
        res = super()._action_done()
        part_sales_lines_vals = []
        for move in self.move_ids:
            part_sales = move.picking_id.part_sales_id
            # Creates new PS line only when pickings linked to a part sales and
            # for moves with qty. done and not already linked to a PS line.
            if not part_sales \
                or (move.location_dest_id.usage != 'customer' and not (move.location_id.usage == 'customer' and move.to_refund)) \
                or move.part_sales_line_id \
                or not move.picked:
                continue
            product = move.product_id
            quantity = move.quantity
            if move.to_refund:
                quantity *= -1

            ps_line_vals = {
                'move_ids': [(4, move.id, 0)],
                'name': product.display_name,
                'order_id': part_sales.id,
                'product_id': product.id,
                'product_uom_qty': 0,
                'qty_delivered': quantity,
                'product_uom': move.product_uom.id,
            }
            if product.invoice_policy == 'delivery':
                # Check if there is already a SO line for this product to get
                # back its unit price (in case it was manually updated).
                ps_line = part_sales.order_line.filtered(lambda sol: sol.product_id == product)
                if ps_line:
                    ps_line_vals['price_unit'] = ps_line[0].price_unit
            elif product.invoice_policy == 'order':
                # No unit price if the product is invoiced on the ordered qty.
                ps_line_vals['price_unit'] = 0
            part_sales_lines_vals.append(ps_line_vals)

        if part_sales_lines_vals:
            self.env['tw.part.sales.line'].with_context(skip_procurement=True).create(part_sales_lines_vals)
        return res

    def _log_less_quantities_than_expected(self, moves):
        """ Log an activity on part sales that are linked to moves. The
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
            related to the part sales where the note will be logged.

            :param moves_information dict:
            {'move_id': ['part_sales_line_id', (new_qty, old_qty)], ..}

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

        documents = self.sudo()._log_activity_get_documents(moves, 'part_sales_line_id', 'DOWN', _keys_in_groupby)
        self._log_activity(_render_note_exception_quantity, documents)

        return super(StockPicking, self)._log_less_quantities_than_expected(moves)

    def _can_return(self):
        self.ensure_one()
        return super()._can_return() or self.part_sales_id


class StockLot(models.Model):
    _inherit = "stock.lot"

    part_sales_ids = fields.Many2many('tw.part.sales', string="Dealer Sales Orders", compute='_compute_part_sales_ids')
    part_sales_count = fields.Integer('Part sales count', compute='_compute_part_sales_ids')

    @api.depends('name')
    def _compute_part_sales_ids(self):
        part_saless = defaultdict(lambda: self.env['tw.part.sales'])
        for move_line in self.env['stock.move.line'].search([('lot_id', 'in', self.ids), ('state', '=', 'done')]):
            move = move_line.move_id
            if move.picking_id.location_dest_id.usage in ('customer', 'transit') and move.part_sales_line_id.order_id:
                part_saless[move_line.lot_id.id] |= move.part_sales_line_id.order_id
        for lot in self:
            lot.part_sales_ids = part_saless[lot.id]
            lot.part_sales_count = len(lot.part_sales_ids)

    def action_view_so(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action['domain'] = [('id', 'in', self.mapped('part_sales_ids.id'))]
        action['context'] = dict(self._context, create=False)
        return action
    