# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class InheritTWStockPickingBatchLineExtras(models.Model):
    _inherit = "tw.stock.picking.batch.line"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    product_extras_domain_ids = fields.Many2many(
        comodel_name='product.product',
        relation='tw_batch_line_product_extras_rel', column1='batch_line_id', column2='product_extras_id',
        compute='_compute_product_extras_domain_ids',
        string="List of Product Extras")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('product_id', 'batch_id.source_picking_ids')
    def _compute_product_extras_domain_ids(self):
        """Compute product extras domain from source picking moves in bulk."""
        batches = self.mapped('batch_id')
        batch_extras_map = {}
        for batch in batches:
            picking_ids = batch.source_picking_ids
            if not picking_ids:
                unit_products = batch.batch_line_ids.product_id.filtered(
                    lambda p: p.product_tmpl_id.division == 'Unit'
                )
                if unit_products:
                    move_objs = self.env['stock.move'].suspend_security().search([
                        ('product_id', 'in', unit_products.ids),
                        ('picking_id.state', 'in', ['assigned', 'confirmed', 'waiting'])
                    ])
                    picking_ids = move_objs.mapped('picking_id')
                
            if picking_ids:
                extras_moves = self.env['stock.move'].suspend_security().search([
                    ('picking_id', 'in', picking_ids.ids),
                    ('product_id.product_tmpl_id.division', '=', 'Extras'),
                    ('state', 'in', ['assigned', 'confirmed', 'waiting'])
                ])
                # mapped('product_id').ids automatically returns distinct product IDs
                batch_extras_map[batch.id] = extras_moves.mapped('product_id').ids
            else:
                batch_extras_map[batch.id] = []

        for record in self:
            record.product_extras_domain_ids = batch_extras_map.get(record.batch_id.id, [])

    # 12: override methods

    # 13: action methods

    # 14: private methods
