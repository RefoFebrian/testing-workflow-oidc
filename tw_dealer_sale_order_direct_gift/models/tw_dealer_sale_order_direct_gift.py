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

class TwSaleOrderDirectGift(models.Model):
    _name = "tw.dealer.sale.order.line.direct.gift"
    _description = "Direct Gift Dealer Sale Order"

    # 7: defaults methods

    # 8: fields
    quantity = fields.Integer(string='Quantity', required=True)
    unit_price = fields.Float(string='Amount', required=True)
    direct_gift_md = fields.Float(string='Direct Gift MD')
    direct_gift_ahm = fields.Float(string='Direct Gift AHM')
    direct_gift_finco = fields.Float(string='Direct Gift Finco')
    direct_gift_dealer = fields.Float(string='Direct Gift Dealer')
    direct_gift_others = fields.Float(string='Direct Gift Others')
    force_cogs = fields.Float(string='Force COGS')
    
    # 9: relation fields
    order_line_id = fields.Many2one(comodel_name='tw.dealer.sale.order.line', ondelete='cascade')
    direct_gift_id = fields.Many2one(comodel_name='tw.sales.program', string='Direct Gift Code',required=True)
    product_id = fields.Many2one(comodel_name='product.product', string='Product Gift',required=True)
    product_tmpl_id = fields.Many2one(comodel_name='product.template', string='Product Unit',required=True)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    @api.onchange('direct_gift_id')
    def _onchange_direct_gift_id(self):
        self.quantity = 0
        self.unit_price = 0
        self.direct_gift_md = 0
        self.direct_gift_ahm = 0
        self.direct_gift_finco = 0
        self.direct_gift_dealer = 0
        self.direct_gift_others = 0
        if self.direct_gift_id:
            existing_dg = self.order_line_id.direct_gift_ids.filtered(lambda x: x.direct_gift_id == self.direct_gift_id and str(x.id) != str(self.id))
            if existing_dg:
                raise Warning(_("Direct Gift %s sudah ada! Tidak bisa menginput direct gift yang sama") % self.direct_gift_id.name)
                
            tmpl = self.order_line_id.product_id.product_tmpl_id
            direct_gift_line = self.direct_gift_id.line_ids.filtered(lambda x: x.product_tmpl_id == tmpl)
            if not direct_gift_line:
                raise Warning(_(f"Direct Gift untuk Produk {tmpl.name} tidak ditemukan!"))
                
            self.product_id = self.direct_gift_id.product_id.id
            self.product_tmpl_id = direct_gift_line.product_tmpl_id.id
            self.quantity = direct_gift_line.qty
            self.unit_price = direct_gift_line.discount_total
            self.force_cogs = direct_gift_line.discount_total
            self.direct_gift_md = direct_gift_line.discount_md
            self.direct_gift_ahm = direct_gift_line.discount_ahm
            self.direct_gift_finco = direct_gift_line.discount_finco
            self.direct_gift_dealer = direct_gift_line.discount_dealer
            self.direct_gift_others = direct_gift_line.discount_others
        
    @api.onchange('unit_price')
    def _onchange_unit_price(self):
        if self.unit_price < 0:
            raise Warning(_("Amount tidak boleh negatif!"))

        tmpl = self.order_line_id.product_id.product_tmpl_id
        direct_gift_line = self.direct_gift_id.line_ids.filtered(lambda x: x.product_tmpl_id == tmpl)
        if self.unit_price > direct_gift_line.discount_total:
            raise Warning(_("Amount tidak boleh lebih besar dari Total Direct Gift!"))

    # 12: override methods

    # 13: action methods

    # 14: private methods
