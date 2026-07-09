# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    _description = "Purchase Order Line"

    # 7: defaults methods
    @api.depends('order_id.company_id', 'order_id.division')
    def _compute_price_pricelist(self):
        # ? Jika module pricelist belum terinstall maka compute price ini tidak akan digunakan dan secara default ambil dari standar_price product
        for order in self:
            order.price_pricelist = order.price

    # 8: fields
    is_discount = fields.Boolean(help="Flag as discount line. It will not show in the purchase order line, and will generated as invoice line")
    original_price_unit = fields.Float(help="Original unit price of the product")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount')
    def _compute_amount(self):
        for line in self:
            base_line = line._prepare_base_line_for_taxes_computation()
            self.env['account.tax']._add_tax_details_in_base_line(base_line, line.company_id)
            price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
            price_total = base_line['tax_details']['raw_total_included_currency']
            price_tax = line.price_total - line.price_subtotal
            if line.is_discount:
                price_subtotal = price_subtotal * -1
                price_total = price_total * -1
                price_tax = price_tax * -1
            line.price_subtotal = price_subtotal
            line.price_total = price_total
            line.price_tax = price_tax

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _create_stock_moves(self,picking):
        values = []
        for line in self.filtered(lambda l: not l.display_type):
            for val in line._prepare_stock_moves(picking):
                values.append(val)
            line.move_dest_ids.created_purchase_line_ids = [Command.clear()]

        return self.env['stock.move'].create(values)
        

    def _create_discount_move_line(self, move, discount_name, discount_amount):
        self.ensure_one()
        aml_currency = move and move.currency_id or self.currency_id
        date = move and move.date or fields.Date.today()
        purchase = self.order_id
        
        res = {
            'display_type': self.display_type or 'discount',
            'name': f"{discount_name} {purchase.name}",
            'quantity': 1,
            'discount': 0,
            'credit': discount_amount,
            'amount_currency': discount_amount,
            'price_unit': discount_amount,
            'tax_ids': [(6, 0, self.taxes_id.ids)],
            'purchase_line_id': self.id,
            'is_downpayment': self.is_downpayment,
        }
        if self.analytic_distribution and not self.display_type:
            res['analytic_distribution'] = self.analytic_distribution
        return res
    
    def _get_purchase_line_id(self, order_id, product_id):
        if not order_id or not product_id:
            return False
        obj_purchase_order_line = self.suspend_security().search([
            ('order_id','=',order_id),
            ('product_id','=',product_id)
            ],limit=1)
        if obj_purchase_order_line :  
            return obj_purchase_order_line
        
        return False

    def _verify_costing_method(self):
        self.ensure_one()

        # Non-Trade (Untuk asset) tidak perlu pengecekan ini
        categ_name = self.product_id.categ_id.complete_name
        if 'Non-trade' in categ_name:
            return

        # Check product valuation method
        product_valuation_method = self.product_id.categ_id.with_company(self.company_id).property_valuation
        if product_valuation_method != 'real_time':
            raise Warning('You cannot confirm a purchase order with a product valuation method other than %s.'%product_valuation_method)

        # Check product costing method
        unit_costing_method = 'fifo'
        sparepart_costing_method = 'average'
        direct_gift_costing_method = 'fifo'
        product_costing_method = self.product_id.categ_id.with_company(self.company_id).property_cost_method
        if self.order_id.division == 'Unit' and product_costing_method != unit_costing_method:
            raise Warning('You cannot confirm a purchase order unit with a product costing method other than %s.'%unit_costing_method)
        elif self.order_id.division == 'Sparepart' and product_costing_method != sparepart_costing_method:
            if not('EV' in categ_name and product_costing_method == unit_costing_method):
                raise Warning('You cannot confirm a purchase order sparepart with a product costing method other than %s.'%(sparepart_costing_method))
        elif self.order_id.division == 'Umum' and 'Direct Gift' in categ_name and product_costing_method != direct_gift_costing_method:
            raise Warning('You cannot confirm a purchase order direct gift with a product costing method other than %s.'%(direct_gift_costing_method))