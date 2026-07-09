# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning


class TwStockAdjustmentLine(models.Model):
    """
    Stock Adjustment Line model for individual product adjustments.
    Each line represents one product/lot combination to be adjusted.
    """
    _name = "tw.stock.adjustment.line"
    _description = "Stock Adjustment Line"
    _order = "product_id"

    # Relation fields
    adjustment_id = fields.Many2one(
        comodel_name='tw.stock.adjustment',
        string='Adjustment',
        required=True,
        ondelete='cascade',
        index=True
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product',
        required=True,
        domain="[('type', '=', 'product')]"
    )
    lot_id = fields.Many2one(
        comodel_name='stock.lot',
        string='Lot/Serial Number',
        domain="[('product_id', '=', product_id)]"
    )
    location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Location',
        required=True
    )
    
    # Related fields
    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='UoM',
        related='product_id.uom_id',
        readonly=True
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='adjustment_id.company_id',
        store=True
    )
    adjustment_state = fields.Selection(
        related='adjustment_id.state',
        string='Adjustment State',
        store=True
    )
    
    # Quantity fields
    qty_system = fields.Float(
        string='System Qty',
        digits='Product Unit of Measure',
        readonly=True,
        help='Quantity recorded in the system (stock.quant)'
    )
    qty_counted = fields.Float(
        string='Counted Qty',
        digits='Product Unit of Measure',
        help='Quantity counted during physical inventory'
    )
    difference = fields.Float(
        string='Difference',
        digits='Product Unit of Measure',
        compute='_compute_difference',
        store=True,
        help='Difference between counted and system quantity'
    )
    
    # Value fields
    system_cost = fields.Float(
        string='System Cost',
        digits='Product Price',
        readonly=True,
        help='Product cost from system (standard price or average cost) at adjustment time'
    )
    adjustment_cost = fields.Float(
        string='Adjustment Cost',
        digits='Product Price',
        help='Unit cost for this adjustment (required for adding new stock)'
    )
    value_difference = fields.Float(
        string='Value Difference',
        digits='Product Price',
        compute='_compute_value_difference',
        store=True,
        help='Monetary value of the quantity difference'
    )
    
    # Additional fields
    reason = fields.Text(
        string='Reason',
        help='Explanation for the quantity difference'
    )
    state = fields.Selection([
        ('open', 'Open'),
        ('counted', 'Counted'),
        ('validated', 'Validated'),
    ], string='Status', default='open', readonly=True)

    # Compute methods
    @api.depends('qty_system', 'qty_counted')
    def _compute_difference(self):
        for record in self:
            record.difference = record.qty_counted - record.qty_system

    @api.depends('difference', 'adjustment_cost')
    def _compute_value_difference(self):
        for record in self:
            # Use adjustment_cost for value calculation, fallback to system_cost
            price = record.adjustment_cost or record.system_cost
            record.value_difference = record.difference * price

    def _update_from_quant(self):
        """Helper method to update qty_system, qty_counted, system_cost from stock.quant."""
        if not self.product_id:
            return
        
        location = self.location_id or self.adjustment_id.location_id
        company = self.adjustment_id.company_id
        
        if not location or not company:
            return
        
        # Get child locations
        location_ids = self.env['stock.location'].suspend_security().search([
            ('id', 'child_of', location.id)
        ]).ids
        
        # Build quant domain
        quant_domain = [
            ('company_id', '=', company.id),
            ('product_id', '=', self.product_id.id),
            ('location_id', 'in', location_ids),
            ('quantity', '>', 0),
        ]
        
        # Add lot filter
        if self.lot_id:
            quant_domain.append(('lot_id', '=', self.lot_id.id))
        else:
            quant_domain.append(('lot_id', '=', False))
        
        quant = self.env['stock.quant'].suspend_security().search(quant_domain, limit=1)
        
        self.qty_system = quant.quantity if quant else 0.0
        self.qty_counted = quant.quantity if quant else 0.0
        if quant and quant.quantity:
            self.system_cost = quant.value / quant.quantity
        else:
            self.system_cost = self.product_id.standard_price
            
        # Prefill adjustment cost with system cost
        self.adjustment_cost = self.system_cost

    # Onchange methods
    @api.onchange('product_id')
    def _onchange_product_id(self):
        # Reset fields when product changes
        self.lot_id = False
        self.qty_system = 0.0
        self.qty_counted = 0.0
        self.system_cost = 0.0
        self.adjustment_cost = 0.0
        
        if self.product_id:
            # Get location from parent adjustment if not set
            location = self.location_id or self.adjustment_id.location_id
            if location:
                self.location_id = location
            
            # For products without tracking (Sparepart), get stock directly
            if self.product_id.tracking == 'none':
                self._update_from_quant()
            else:
                # For tracked products, use standard price as placeholder
                self.system_cost = self.product_id.standard_price
                self.adjustment_cost = self.system_cost

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        """Update qty_system when lot is selected."""
        self._update_from_quant()

    @api.onchange('qty_counted')
    def _onchange_qty_counted(self):
        if self.qty_counted != self.qty_system:
            self.state = 'counted'
        else:
            self.state = 'open'

    # Business logic methods
    def _apply_adjustment(self):
        """
        Apply the adjustment to stock.quant using 100% base Odoo approach.
        1. If quant doesn't exist, create it with quantity=0 first
        2. Then use action_apply_inventory (base Odoo) for all cases
        """
        self.ensure_one()
        
        if self.difference == 0:
            return
        
        # Find existing quant
        quant = self.env['stock.quant'].sudo().search([
            ('product_id', '=', self.product_id.id),
            ('location_id', '=', self.location_id.id),
            ('lot_id', '=', self.lot_id.id if self.lot_id else False)
        ], limit=1)
        
        if not quant:
            # Create quant with quantity=0 first using _update_available_quantity
            # This method uses sudo() internally and bypasses ORM restriction
            self.env['stock.quant'].with_context(inventory_mode=True)._update_available_quantity(
                product_id=self.product_id,
                location_id=self.location_id,
                quantity=0,  # Create with qty=0
                lot_id=self.lot_id or None,
            )
            # Search again to get the created quant
            quant = self.env['stock.quant'].sudo().search([
                ('product_id', '=', self.product_id.id),
                ('location_id', '=', self.location_id.id),
                ('lot_id', '=', self.lot_id.id if self.lot_id else False)
            ], limit=1)
        
        if quant and quant.quantity > 0:
            # Existing stock with value - use base Odoo action_apply_inventory
            quant.with_context(inventory_mode=True).sudo().write({
                'inventory_quantity': self.qty_counted
            })
            quant.with_context(
                inventory_name=self.adjustment_id.name
            ).sudo().action_apply_inventory()
            
            # Update stock.move origin so smart buttons can find it
            recent_moves = self.env['stock.move'].sudo().search([
                ('product_id', '=', self.product_id.id),
                ('is_inventory', '=', True),
                ('state', '=', 'done'),
                ('origin', '=', False),
            ], order='id desc', limit=1)
            if recent_moves:
                recent_moves.write({'origin': self.adjustment_id.name})
        else:
            # New stock (or 0 qty quant) - use custom approach with adjustment_cost
            self._create_adjustment_move_with_valuation()
        
        # Update line state
        self.suspend_security().write({'state': 'validated'})

    def _create_adjustment_move_with_valuation(self):
        """
        Create stock.move for new stock adjustment with proper price_unit.
        This ensures correct valuation layer and journal entries.
        """
        self.ensure_one()
        
        # Validate adjustment_cost is set
        if not self.adjustment_cost:
            raise Warning(_("New Price must be set for product %s before applying adjustment.") % self.product_id.display_name)
        
        # Get inventory adjustment location
        inventory_loss_location = self.env['stock.location'].sudo().search([
            ('usage', '=', 'inventory'),
            '|',
            ('company_id', '=', self.company_id.id),
            ('company_id', '=', False),
        ], limit=1)
        
        if not inventory_loss_location:
            raise Warning(_("Inventory Loss location not found."))
        
        # For positive adjustment (adding new stock): from inventory loss to stock location
        move_vals = {
            'name': _('INV:') + (self.adjustment_id.name or ''),
            'product_id': self.product_id.id,
            'product_uom_qty': self.qty_counted,
            'product_uom': self.product_id.uom_id.id,
            'location_id': inventory_loss_location.id,
            'location_dest_id': self.location_id.id,
            'is_inventory': False,  # False so it uses our price_unit for valuation (treated as receipt)
            'origin': self.adjustment_id.name,
            'company_id': self.company_id.id,
            'price_unit': self.adjustment_cost,
        }
        
        move = self.env['stock.move'].sudo().create(move_vals)
        move.sudo()._action_confirm()
        
        # Ensure move lines exist and are updated
        if not move.move_line_ids:
            # Create move line manually if not exist (common for new stock)
            vals = {
                'move_id': move.id,
                'product_id': self.product_id.id,
                'product_uom_id': self.product_id.uom_id.id,
                'location_id': move.location_id.id,
                'location_dest_id': move.location_dest_id.id,
                'quantity': self.qty_counted,
                'lot_id': self.lot_id.id if self.lot_id else False,
            }
            self.env['stock.move.line'].sudo().create(vals)
        else:
            # Update existing lines
            move.move_line_ids.sudo().write({
                'quantity': self.qty_counted,
                'lot_id': self.lot_id.id if self.lot_id else False,
            })
            
        # For Odoo 17/18+: Mark as picked to allow validation
        if 'picked' in move._fields:
            move.picked = True
            
        move.sudo()._action_done()
        



