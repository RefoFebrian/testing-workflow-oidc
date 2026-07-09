# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools import groupby

# 5: local imports

# 6: Import of unknown third party lib


class TwDealerSaleOrderLine(models.Model):
    _inherit = "tw.dealer.sale.order.line"
    
    # 7: defaults methods

    # 8: fields
    direct_gift_dealer = fields.Float(string="Direct Gift Dealer", compute='_compute_direct_gift_total', help="Extra discount given outside discount detail from dealer")
    direct_gift_total = fields.Float(string="Direct Gift", compute='_compute_direct_gift_total', help="Extra discount given outside discount detail")
    direct_gift_quantity = fields.Float(string="Direct Gift Quantity", compute='_compute_direct_gift_total', help="Amount of discounts or subsidy in the discount detail")
    
    # 9: relation fields
    available_direct_gift_ids = fields.Many2many('tw.sales.program', string='Available Direct Gift', compute='_compute_available_direct_gift_ids', help='For domain')
    direct_gift_ids = fields.One2many('tw.dealer.sale.order.line.direct.gift', inverse_name='order_line_id', string="Order Line Direct Gift",store=True)

    # 10: constraints & sql constraints
	
    # 11: compute/depends & on change methods
    @api.depends('direct_gift_ids.unit_price', 'direct_gift_ids.quantity')
    def _compute_direct_gift_total(self):
        for line in self:
            direct_gift_total = direct_gift_dealer = direct_gift_quantity = 0
            for dg in line.direct_gift_ids:
                direct_gift_quantity += dg.quantity
                direct_gift_total += dg.unit_price * dg.quantity
                direct_gift_dealer += dg.direct_gift_dealer * dg.quantity
            
            line.recompute_helper += 1
            line.direct_gift_total = direct_gift_total
            line.direct_gift_dealer = direct_gift_dealer
            line.direct_gift_quantity = direct_gift_quantity
            
    @api.depends('order_id.company_id','order_id.finco_id','product_id')
    def _compute_available_direct_gift_ids(self):
        for line in self:
            today = date.today()
            branch = line.order_id.company_id

            domain = [
                ('company_id', 'in', [branch.id, branch.parent_id.id] if branch.parent_id else [branch.id]),
                ('start_date', '<=', today),
                ('end_date', '>=', today),
                ('state', '=', 'approved'),
                ('sales_program_type_id.value', '=', 'Program Subsidi Barang'),
                ('active', '=', True)]
            available_dg = self.env['tw.sales.program'].search(domain)

            domain_line = [('sales_program_id', 'in', available_dg.ids),('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)]
            if not self.order_id.finco_id:
                domain_line.append(('discount_finco', '=', 0))
            available_dg_line = self.env['tw.sales.program.line'].search(domain_line)
            line.available_direct_gift_ids = [(6, 0, available_dg_line.mapped('sales_program_id.id'))]

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.direct_gift_ids = False
        super()._onchange_product_id()


    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for order_line in res:
            order_line._validate_direct_gift()
        return res

    def write(self, vals):
        res = super().write(vals)
        for order_line in self:
            order_line._validate_direct_gift()
        return res

    # 13: action methods
	
    # 14: private methods

    def _get_amount_dealer_expense(self):
        total = super()._get_amount_dealer_expense()
        for line in self.direct_gift_ids:
            total += line.direct_gift_dealer
        return total
    
    def _validate_direct_gift(self):
        self.ensure_one()
        if self.direct_gift_ids:
            gifts = self.direct_gift_ids.mapped('direct_gift_id')
            if len(gifts) != len(self.direct_gift_ids):
                raise Warning("Direct Gift tidak boleh duplikat! Silahkan periksa inputan direct gift")

        