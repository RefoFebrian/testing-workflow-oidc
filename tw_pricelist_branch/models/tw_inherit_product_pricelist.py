# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions

from odoo.exceptions import UserError as Warning

from datetime import datetime, date

import logging
_logger = logging.getLogger(__name__)

class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def generate_product_supplierinfo(self,partner=False):
        
        # Search Partner from TW Branch
        # TODO Jika untuk divisi lain bagaimana?
        query_search_tupple = ()
        if self.type == 'sales':
            query_search_tupple = "|",('pricelist_sale_sparepart_id','=',self.id),('pricelist_sale_unit_id','=',self.id)
        elif self.type == 'purchase':
            query_search_tupple = "|",('pricelist_purchase_sparepart_id','=',self.id),('pricelist_purchase_unit_id','=',self.id) 
        partner = self.env['tw.branch.setting'].suspend_security().search(
            [
                query_search_tupple
            ]
        ).partner_id.id
        generate_product_supplierinfo = super(ProductPricelist, self).generate_product_supplierinfo(partner=partner)
        return generate_product_supplierinfo