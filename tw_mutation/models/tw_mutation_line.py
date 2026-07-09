from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning


class MutationOrderLine(models.Model):
    _name = "tw.mutation.order.line"
    _description = 'Mutation Order Line'
    
    description = fields.Text('Description')

    state = fields.Selection(related='mutation_order_id.state', string='State of Mutation Order')

    initial_cogs = fields.Float('Initial COGS', digits='Product Price', help='Also known as Performance HPP')
    sub_total = fields.Float('Sub Total', digits='Product Price', compute='_compute_sub_total', store=True)
    price = fields.Float('Price', digits='Product Price')
    qty = fields.Float('Qty', digits='Product Unit of Measure')
    qty_available = fields.Float('Qty Available', digits='Product Unit of Measure')
    qty_supply = fields.Float('Qty Supply', digits='Product Unit of Measure')
    
    mutation_order_id = fields.Many2one('tw.mutation.order', string='Mutation Order')
    product_id = fields.Many2one('product.product', string='Product')
    stock_distribution_id = fields.Many2one(related="mutation_order_id.stock_distribution_id")
    
    # Computed fields for picking qty tracking
    qty_outgoing = fields.Float(
        'Qty Outgoing', 
        digits='Product Unit of Measure',
        compute='_compute_picking_qty',
        store=True,
        help='Quantity yang sudah terkirim dari branch sender'
    )
    qty_incoming = fields.Float(
        'Qty Incoming', 
        digits='Product Unit of Measure',
        compute='_compute_picking_qty',
        store=True,
        help='Quantity yang sudah diterima oleh branch receiver'
    )
    @api.depends('mutation_order_id.picking_ids.state', 'mutation_order_id.picking_ids.move_ids.state')
    def _compute_picking_qty(self):
        """Compute qty_outgoing and qty_incoming from related pickings."""
        for line in self:
            qty_outgoing = 0.0
            qty_incoming = 0.0
            
            if line.mutation_order_id:
                pickings = self.env['stock.picking'].sudo().search([
                    ('mutation_order_id', '=', line.mutation_order_id.id),
                    ('state', '=', 'done')
                ])
                
                for picking in pickings:
                    for move in picking.move_ids.filtered(
                        lambda m: m.product_id == line.product_id and m.state == 'done'
                    ):
                        if picking.picking_type_id.code == 'outgoing':
                            qty_outgoing += move.quantity
                        elif picking.picking_type_id.code == 'incoming':
                            qty_incoming += move.quantity
            
            line.qty_outgoing = qty_outgoing
            line.qty_incoming = qty_incoming

    @api.depends('price')
    def _compute_sub_total(self):
        for record in self:
            record.sub_total = record.price * record.qty
    
    @api.onchange('qty')
    def _onchange_qty(self):
        self._validate_order()
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            record.qty_available = 0
            if record.product_id:
                record.qty_available = record.get_quantity_available()
                record.sudo().get_product_price()

    def _validate_order(self):
        for record in self:
            if record.qty > record.qty_available:
                raise Warning('Quantity must not exceed qty available')
            if record.qty <= 0:
                raise Warning('Quantity cannot be less than or equal to zero')
            
            # Check qty not exceeding approved qty from SD (Stock Distribution)
            if record.stock_distribution_id:
                sd_line = self.env['tw.stock.distribution.line'].sudo().search([
                    ('stock_distribution_id', '=', record.stock_distribution_id.id),
                    ('product_id', '=', record.product_id.id)
                ], limit=1)
                if sd_line and record.qty > sd_line.approved_qty:
                    raise Warning(f'Quantity must not exceed approved qty from Stock Distribution (qty approved: {sd_line.approved_qty})')


    def get_quantity_available(self):
        qty_available = self.env['stock.quant'].get_stock_available(self.product_id.id,self.mutation_order_id.company_id.id,location_id=self.mutation_order_id.location_id.id)

        self.env['stock.quant'].compare_stock_on_transaction(
            company_id=self.mutation_order_id.company_id.id,
            division=self.mutation_order_id.division,
            product_id=self.product_id.id,
            qty=self.qty,
            location_id=self.mutation_order_id.location_id.id
        )

        if qty_available <= 0:
            raise Warning(f"Stock untuk produk {self.product_id.name} tidak tersedia")
        return qty_available
    
    def get_product_price(self):
        current_pricelist = self.mutation_order_id._get_pricelist()
        if not current_pricelist:
            raise Warning("Attention! The Sale Pricelist Configuration for this Branch is not Available. Please Configure it First.")

        current_price = current_pricelist.with_company(self.mutation_order_id.company_id.id)._price_get(self.product_id, 1)[current_pricelist.id]
        
        if not current_price:
            raise Warning(f"Attention! The Price for { self.product_id.name } is not found in the Active Pricelist!")
        self.write({ 'price': current_price })