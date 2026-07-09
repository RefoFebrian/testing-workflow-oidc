# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, Command
from odoo.exceptions import ValidationError, UserError

# Import discount calculator
from odoo.addons.tw_account_discount.utils.discount_calculator import DiscountCalculator

class TWSaleOrderDiscount(models.Model):
    _name = "tw.sale.order.discount"
    _description = "TW Sale Order Discount"
    _order = "id desc"
    
    # Basic fields
    name = fields.Char(string='Description', related='discount_id.name', store=True, readonly=False)
    amount = fields.Float(string='Amount', required=True, default=0.0)
    
    # Related fields from discount_id
    discount_type = fields.Selection(related='discount_id.discount_type', string='Tipe Diskon', store=True, readonly=True)
    
    # Related fields from discount_id
    account_id = fields.Many2one('account.account', related='discount_id.account_id', store=True, readonly=True)
    tax_ids = fields.Many2many('account.tax', related='discount_id.tax_ids', string='Taxes', readonly=True)
    
    # Relation fields
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True, index=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True, readonly=True)
    sale_order_id = fields.Many2one('tw.sale.order', string='Sale Order', ondelete='cascade', required=True, index=True)
    discount_id = fields.Many2one('tw.account.discount', string='Discount Type',domain="[('type', '=', 'out_receipt')]",required=True,ondelete='restrict',index=True)
    
    # Constraints
    _sql_constraints = [
        ('check_amount_positive', 'CHECK(amount >= 0)', 'Discount amount must be positive.'),
    ]
    
    # Compute and onchange methods
    @api.onchange('discount_id')
    def _onchange_discount_id(self):
        if self.discount_id:
            # Reset amount when discount type changes
            self.amount = 0.0
    
    def get_discount_amount(self, base_amount):
        """
        Calculate discount amount based on discount type and value
        
        Args:
            base_amount (float): The base amount to calculate discount from
            
        Returns:
            float: The calculated discount amount
            
        Raises:
            UserError: If discount type is not set on the discount record
        """
        self.ensure_one()
        if not self.discount_id.discount_type:
            raise UserError(_("Discount type is not set on discount %s") % self.discount_id.name)
            
        try:
            return DiscountCalculator.calculate_discount(
                base_amount,
                self.discount_id.discount_type,
                self.amount
            )
        except ValidationError as e:
            raise UserError(str(e))
    

