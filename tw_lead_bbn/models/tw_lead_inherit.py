# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib

class LeadsBBN(models.Model):
    _inherit = "tw.lead"

    # 7: defaults methods
    
    # 8: fields

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods

    # 14: private methods

    def _get_basic_price(self):
        self.ensure_one()
        unit_price = super()._get_basic_price()
        currency = self.company_id.currency_id
        product_tmpl = self.product_id.product_tmpl_id
        
        # default plate value is H which means Black for regular customer
        plate_value = self.env.ref('tw_pricelist_bbn.tw_selection_plate_type_black')
        pricelist_bbn = self.env['product.pricelist']._get_bbn_sales_pricelist(self.company_id, plate_value)
        bbn_price = pricelist_bbn.with_context(self.company_id)._get_product_price(product_tmpl, 1, currency)
        
        price = unit_price + bbn_price
        return price

