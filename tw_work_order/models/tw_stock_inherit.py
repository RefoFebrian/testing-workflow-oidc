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
    
    work_order_line_id = fields.Many2one('tw.work.order.line', 'Work Order Line', index='btree_not_null')

    @api.model
    def _prepare_merge_moves_distinct_fields(self):
        distinct_fields = super(StockMove, self)._prepare_merge_moves_distinct_fields()
        distinct_fields.append('work_order_line_id')
        return distinct_fields

    def _get_sale_order_lines(self):
        """ Return all possible work order lines for one stock move. """
        self.ensure_one()
        return (self + self.browse(self._rollup_move_origs() | self._rollup_move_dests())).work_order_line_id

    def _assign_picking_post_process(self, new=False):
        super(StockMove, self)._assign_picking_post_process(new=new)
        if new:
            picking_id = self.mapped('picking_id')
            work_order_ids = self.mapped('work_order_line_id.order_id')
            for work_order_id in work_order_ids:
                picking_id.message_post_with_source(
                    'mail.message_origin_link',
                    render_values={'self': picking_id, 'origin': work_order_id},
                    subtype_xmlid='mail.mt_note',
                )

    def _get_all_related_sm(self, product):
        return super()._get_all_related_sm(product) | self.filtered(lambda m: m.work_order_line_id.product_id == product)
    
    def _get_new_picking_values(self):
        res = super()._get_new_picking_values()
        for record in self:
            if record.work_order_line_id:
                res.update({
                    'division': record.work_order_line_id.order_id.division,
                    'company_id': record.work_order_line_id.order_id.company_id.id,
                    'partner_id': record.work_order_line_id.order_id.partner_id.id
                })
        return res
    
    # def write(self,vals):
    #     res = super(StockMove, self).write(vals)
    #     for move in self:
    #         if move.work_order_line_id and move.work_order_line_id.order_id: 
    #             work_order_id = move.work_order_line_id.order_id                 
    #             if work_order_id._test_moves_done():
    #                 work_order_id.write({
    #                     'type_wo': 2,
    #                     'is_shipped': True,
    #                 })
    #     return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _should_show_lot_in_invoice(self):
        return 'customer' in {self.location_id.usage, self.location_dest_id.usage}


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    work_order_id = fields.Many2one('tw.work.order', 'Work Order')


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_custom_move_fields(self):
        fields = super(StockRule, self)._get_custom_move_fields()
        fields += ['work_order_line_id']
        return fields


class StockPicking(models.Model):
    _inherit = "stock.picking"

    work_order_id = fields.Many2one('tw.work.order', compute="_compute_work_order_id", inverse="_set_work_order_id", string="Work Order", store=True, index='btree_not_null')

    @api.depends('group_id')
    def _compute_work_order_id(self):
        for picking in self:
            picking.work_order_id = picking.group_id.work_order_id

    def _set_work_order_id(self):
        if self.group_id:
            self.group_id.work_order_id = self.work_order_id
        else:
            if self.work_order_id:
                vals = {
                    'work_order_id': self.work_order_id.id,
                    'name': self.work_order_id.name,
                }
            else:
                vals = {}

            pg = self.env['procurement.group'].create(vals)
            self.group_id = pg

    def _auto_init(self):
        """
        Create related field here, too slow
        when computing it afterwards through _compute_related.

        Since group_id.work_order_id is created in this module,
        no need for an UPDATE statement.
        """
        if not column_exists(self.env.cr, 'stock_picking', 'work_order_id'):
            create_column(self.env.cr, 'stock_picking', 'work_order_id', 'int4')
        return super()._auto_init()


class StockLot(models.Model):
    _inherit = "stock.lot"

    work_order_ids = fields.Many2many('tw.work.order', string="Dealer Sales Orders", compute='_compute_work_order_ids')
    work_order_count = fields.Integer('Work order count', compute='_compute_work_order_ids')

    @api.depends('name')
    def _compute_work_order_ids(self):
        work_orders = defaultdict(lambda: self.env['tw.work.order'])
        for move_line in self.env['stock.move.line'].search([('lot_id', 'in', self.ids), ('state', '=', 'done')]):
            move = move_line.move_id
            if move.picking_id.location_dest_id.usage in ('customer', 'transit') and move.work_order_line_id.order_id:
                work_orders[move_line.lot_id.id] |= move.work_order_line_id.order_id
        for lot in self:
            lot.work_order_ids = work_orders[lot.id]
            lot.work_order_count = len(lot.work_order_ids)

    def action_view_so(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action['domain'] = [('id', 'in', self.mapped('work_order_ids.id'))]
        action['context'] = dict(self._context, create=False)
        return action