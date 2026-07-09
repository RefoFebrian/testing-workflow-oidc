# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command
from odoo.tools import SQL

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class TWDealerSPKLine(models.Model):
    _name = "tw.dealer.spk.line"
    _description = "SPK Line"
    _order = "id"
    
    # 7: defaults methods
    
    # 8: fields
    product_qty = fields.Integer(string="Qty", default=1)
    is_bbn = fields.Boolean(string='BBN?')
    down_payment = fields.Float(string="Uang Muka/DP", help="The initial payment made upfront for the purchase.")
    tenor = fields.Integer(string="Tenor", help="The duration of the loan or financing in months.")
    installment = fields.Float(string="Cicilan", help="The periodic payment amount for the loan or financing.")
    discount = fields.Float(string="Diskon", help="The reduction in price or amount applied to the transaction.")
    
    # 9: relation fields
    spk_id = fields.Many2one(comodel_name='tw.dealer.spk')
    plate_id = fields.Many2one(comodel_name='tw.selection', string='Plate', domain=[('type', '=', 'PlateType')])
    partner_stnk_id = fields.Many2one(comodel_name='res.partner', string='STNK',
                                      domain=[('category_id.name', '=', 'Customer')])
    product_id = fields.Many2one(comodel_name='product.product', string="Produk",
                                 domain="[('sale_ok', '=', True), ('categ_id', 'in', parent.product_category_ids)]")

    # 10: constraints & sql constraints
    @api.constrains('spk_id', 'is_bbn')
    def _check_bbn(self):
        for record in self:
            if record.spk_id.finco_id and not record.is_bbn:
                raise ValidationError(_("BBN must be checked if a Finco is selected."))
    
    @api.constrains('spk_id', 'down_payment')
    def _check_down_payment(self):
        for record in self:
            if record.spk_id.finco_id and not record.down_payment:
                raise ValidationError(_("Down Payment must be filled if a Finco is selected."))

    @api.constrains('discount')
    def _check_discount(self):
        for record in self:
            if record.discount < 0:
                raise ValidationError(_("Tidak bisa input discount negatif."))
            
    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _prepare_dealer_sale_order_line_vals(self):
        self.ensure_one()
        
        location_id = lot_id = partner_stnk_id = False
        down_payment = 0.0

        spk_obj = self.spk_id
        partner_obj = spk_obj.partner_id
        if self.down_payment:
            down_payment = self.down_payment
            
        if self.partner_stnk_id:
            partner_stnk_id = self.partner_stnk_id.id
        else:
            partner_stnk_id = spk_obj.lead_id.partner_id.id
            
        pricelist = spk_obj._get_pricelist_sales()
        price = pricelist.with_company(spk_obj.company_id)._get_product_price(self.product_id, self.product_qty)
        
        lot = self.env['stock.quant'].get_available_lot_stock(self.product_id.id, spk_obj.company_id.id)

        if lot:
            lot_id = lot[0] if len(lot) > 1 else lot
            location_id = lot_id.location_id.id
            # update state to reserved in case there are identical products in one SPK
            lot_id.write({'state': 'reserved'})
        
        vals_line = {
            'product_id': self.product_id.id,
            'product_qty': self.product_qty,
            'plate_id': self.plate_id.id,  # default plate type is black
            'partner_stnk_id': partner_stnk_id,
            'location_id': location_id,
            'lot_id': lot_id.id if lot_id else False,
            'price_unit': price,
            'discount_input': self.discount,
            'downpayment': down_payment or 0.0,
            'tenor': self.tenor or 0,
            'installment': self.installment or 0.0,
            'tax_id': [Command.set(self.product_id.taxes_id.ids)],
            'discount_regular': self.discount,
        }

        return vals_line
    
    
