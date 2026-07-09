# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class StockDistributionLine(models.Model):
    _name = "tw.stock.distribution.line"
    _description = "Stock Distribution Line"

    description = fields.Text('Description', compute="_compute_description")
    qty = fields.Integer('Qty')
    requested_qty = fields.Integer('Requested Qty')
    approved_qty = fields.Integer('Approved Qty')
    supply_qty = fields.Integer('Supply Qty', compute='_compute_supply_qty', store=True)

    price = fields.Float('Unit Price', digits='Product Price')
    sub_total = fields.Float('Subtotal', digits='Product Price', store=True, readonly=True, compute='_compute_price')

    product_domain = fields.Binary(string='Domain Product', compute='_compute_domain_product')

    stock_distribution_id = fields.Many2one('tw.stock.distribution', 'Stock Distribution')
    product_id = fields.Many2one(comodel_name='product.product', string='Product')

    @api.depends('product_id')
    def _compute_domain_product(self):
        for record in self:
            categ_ids = self.env['product.category'].get_child_ids(record.stock_distribution_id.division)
            domain = [('categ_id','in',categ_ids)]
            record.product_domain = domain
    
    @api.depends('description')
    def _compute_description(self):
        # Menghitung sub-total berdasarkan approved_qty dan price
        for record in self:
            record.description = record.product_id.display_name

    @api.depends(
        'stock_distribution_id',
        'product_id',
        'stock_distribution_id.sale_order_id',
        'stock_distribution_id.sale_order_id.state',
        'stock_distribution_id.sale_order_id.order_line.qty_delivered'
    )
    def _compute_supply_qty(self):
        """Compute the quantity already supplied based on related sale orders.
        
        Uses qty_delivered from the sale order line for calculation.
        Mutation order calculation is handled in the tw_mutation module.
        """
        for line in self:
            if not line.stock_distribution_id or not line.product_id:
                line.supply_qty = 0
                continue
                
            total_supplied = 0.0
            
            # For sale orders, use qty_delivered from the sale order line
            if line.stock_distribution_id.sale_order_id and line.stock_distribution_id.sale_order_id.state in ('sale', 'done'):
                sale_order = line.stock_distribution_id.sale_order_id
                sale_order_line = self.env['tw.sale.order.line'].search([
                    ('order_id', '=', sale_order.id),
                    ('product_id', '=', line.product_id.id)
                ], limit=1)
                
                if sale_order_line:
                    total_supplied += sale_order_line.qty_delivered
            
            line.supply_qty = total_supplied

    @api.depends('price', 'approved_qty')
    def _compute_price(self):
        # Menghitung sub-total berdasarkan approved_qty dan price
        for record in self:
            record.sub_total = record.approved_qty * record.price

    @api.onchange('approved_qty')
    def quantity_change(self):
        # Validasi perubahan approved_qty agar sesuai dengan requested_qty
        if self.approved_qty < 0:
            raise Warning(_('Quantity Cannot be less than Zero'))
        elif self.approved_qty > self.requested_qty:
            raise Warning(_('Quantity must not Exceed Demand'))
        
    @api.onchange('product_id')
    def product_id_change(self):
        for rec in self:
            if rec.product_id:
                rec.description = rec.product_id.product_tmpl_id.display_name
                rec.get_product_price()
    
    def get_product_price(self):
        current_pricelist = self.stock_distribution_id._get_pricelist()
        if not current_pricelist:
            raise Warning(f"Attention! The Sale Pricelist Configuration for {self.stock_distribution_id.company_id.name} is not Available. Please Configure it First.")

        current_price = current_pricelist.with_company(self.stock_distribution_id.company_id.id)._price_get(self.product_id, self.approved_qty)[current_pricelist.id]
        
        if not current_price:
            raise Warning(f"Attention! The Price for { self.product_id.name } is not found in the Active Pricelist!")
        self.write({ 'price': current_price })