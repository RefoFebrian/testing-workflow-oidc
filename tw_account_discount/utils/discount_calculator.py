# -*- coding: utf-8 -*-

from odoo import _
from odoo.exceptions import ValidationError

class DiscountCalculator:
    """Utility class for calculating discounts"""
    
    @staticmethod
    def _convert_discount_value(discount_type, discount_value):
        """
        Convert discount value to proper format based on type
        
        Args:
            discount_type (str): Type of discount ('fixed' or 'percentage')
            discount_value (float): Value of the discount
            
        Returns:
            float: The converted discount value
        """
        # TODO: Kode ini membuat jika diskon di isi 0.5% menjadi 50%, padahal memang 0.5% 
        # if discount_type == 'percentage' and discount_value <= 1:
        #     return discount_value * 100
        return discount_value

    @classmethod
    def calculate_discount(cls, amount, discount_type, discount_value):
        """
        Calculate discount based on type and value
        
        Args:
            amount (float): Base amount to calculate discount from
            discount_type (str): Type of discount ('fixed' or 'percentage')
            discount_value (float): Value of the discount
            
        Returns:
            float: The calculated discount amount
            
        Raises:
            ValidationError: If discount_type is invalid
        """
        # Convert discount value if needed
        converted_value = cls._convert_discount_value(discount_type, discount_value)
        if discount_type == 'fixed':
            return min(converted_value, amount)  # Ensure discount doesn't exceed amount
        elif discount_type == 'percentage':
            if not 0 <= converted_value <= 100:
                raise ValidationError(_('Discount percentage must be between 0 and 100'))
            return (amount * converted_value) / 100.0
        else:
            raise ValidationError(_('Invalid discount type: %s') % discount_type)
