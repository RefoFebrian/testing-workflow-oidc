# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class MutationRequestLine(models.Model):
    _name = "tw.mutation.request.line"
    _description = "Mutation Request Line"
    
    # 7: defaults methods

    # 8: fields
    description = fields.Text(string='Description')
    requested_qty = fields.Float(string='Requested Qty', digits='Product Unit of Measure')
    approved_qty = fields.Float(string='Approved Qty', digits='Product Unit of Measure', compute='_compute_qty_from_sd', store=True)
    supply_qty = fields.Float(string='Supply Qty', digits='Product Unit of Measure', compute='_compute_qty_from_sd', store=True)
    price = fields.Float(string='Unit Price', digits='Product Price')
    sub_total = fields.Float(string='Subtotal', digits='Product Price', compute='_compute_price', store=True)

    # 9: relation fields
    request_id = fields.Many2one(comodel_name='tw.mutation.request', string='Request')
    product_id = fields.Many2one(comodel_name='product.product', string='Product')
    product_category_ids = fields.Many2many(
        comodel_name='product.category',
        relation='tw_mutation_request_product_category_rel', column1='request_line_id', column2='product_category_id',
        compute='_compute_product_category_ids',
        string="Product Category")

    # 10: constraints & sql constraints
    @api.constrains('product_id')
    def _check_unique_request_line(self):
        for record in self:
            domain = [
                ('request_id', '=', record.request_id.id),
                ('product_id', '=', record.product_id.id)
            ]
            if self.search_count(domain) > 1:
                raise Warning("Product already exists.")
                
    # 11: compute/depends & on change methods
    @api.depends('price', 'requested_qty')
    def _compute_price(self):
        for record in self:
            record.sub_total = record.requested_qty * record.price
        
    @api.depends('product_id')
    def _compute_product_category_ids(self):
        self.product_category_ids = False
        for record in self:
            record.product_category_ids = [(6, 0, self.env['product.category'].get_child_ids(record.request_id.division))]

    @api.depends('request_id.stock_distribution_id', 'request_id.stock_distribution_id.stock_distribution_ids', 
                 'request_id.stock_distribution_id.stock_distribution_ids.approved_qty',
                 'request_id.stock_distribution_id.stock_distribution_ids.supply_qty',
                 'product_id')
    def _compute_qty_from_sd(self):
        """Mirror approved_qty and supply_qty from Stock Distribution Line."""
        for record in self:
            record.approved_qty = 0
            record.supply_qty = 0
            # Use suspend_security() to bypass company rules when accessing cross-company records
            stock_distribution_id = record.request_id.suspend_security().stock_distribution_id
            if stock_distribution_id and record.product_id:
                sd_line = self.env['tw.stock.distribution.line'].suspend_security().search([
                    ('stock_distribution_id', '=', stock_distribution_id.id),
                    ('product_id', '=', record.product_id.id)
                ], limit=1)
                if sd_line:
                    record.approved_qty = sd_line.approved_qty
                    record.supply_qty = sd_line.supply_qty
        
    @api.onchange('product_id')
    def onchange_product_id(self):
        self.price = False
        if not self.request_id.company_id or not self.request_id.branch_sender_id or not self.request_id.purchase_order_type_id:
            return {'warning':{'title':'Attention !','message':'Before adding details,\nPlease fill in the header first.'}}
        if self.product_id:
            self.requested_qty = 1
            self.approved_qty = 0
            branch_obj = self.env['res.company'].suspend_security().search([('partner_id','=',self.request_id.branch_sender_id.id)],limit=1)
            if not branch_obj:
                raise Warning(f"Branch for partner {self.request_id.branch_sender_id.name} is not found.")
            
            pricelist = self.env['tw.branch.setting'].suspend_security()._get_pricelist_purchase(branch_obj, self.request_id.division)
            self.description = self.product_id.product_tmpl_id.description
            if self.request_id.division == 'Unit':
                price = pricelist.with_company(branch_obj).suspend_security()._price_get(self.product_id, 1)[pricelist.id]
                self.price = price
            else:
                # TODO : seharusnya menggunakan get price juga, tetapi di handle saat pengecekan use_pricelist supaya bisa lewat
                # self.price = pricelist.with_company(branch_obj)._price_get(self.product_id, 1)[pricelist.id]
                self.price = self.product_id.standard_price
            self.description = self.product_id.name
    
    @api.onchange('requested_qty')
    def onchange_quantity(self):
        if self.requested_qty < 0:
            self.requested_qty = False
            return {'warning': {'title': 'Perhatian!', 'message': 'Request Quantity harus lebih dari nol!'}}
            
    # 12: override methods
    
    # 13: action methods
            
    # 14: private methods