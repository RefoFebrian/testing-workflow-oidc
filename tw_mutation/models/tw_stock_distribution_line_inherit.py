# -*- coding: utf-8 -*-

from odoo import api, models, fields, _
from odoo.exceptions import UserError

class StockDistributionLineInherit(models.Model):
    _inherit = "tw.stock.distribution.line"
    
    @api.depends(
        'stock_distribution_id',
        'product_id',
        'stock_distribution_id.mutation_order_id',
        'stock_distribution_id.mutation_order_id.state',
        'stock_distribution_id.mutation_order_id.picking_ids.state'
    )
    def _compute_supply_qty(self):
        """Extend supply_qty computation to include mutation order quantities.
        
        For mutation orders, calculates the total quantity based on done stock moves.
        This extends the base implementation in tw_stock_distribution.
        """
        # Call parent method first to handle sale order quantities
        super(StockDistributionLineInherit, self - self.filtered('stock_distribution_id.mutation_order_id'))._compute_supply_qty()
        
        # Only process lines with valid stock distribution and mutation orders
        for line in self.filtered(lambda l: l.stock_distribution_id and l.stock_distribution_id.mutation_order_id and l.product_id):
            mutation_order = line.stock_distribution_id.mutation_order_id
            if mutation_order.state != 'done':
                continue
                
            # Get all done stock moves for this product in the mutation order
            done_moves = self.env['stock.move'].search([
                ('origin', '=', mutation_order.name),
                ('product_id', '=', line.product_id.id),
                ('state', '=', 'done'),
                ('picking_code', '=', 'outgoing')  # Only outgoing moves (deliveries)
            ])
            
            if done_moves:
                # Add the sum of done quantities to the supply_qty
                line.supply_qty += sum(move.quantity for move in done_moves)
