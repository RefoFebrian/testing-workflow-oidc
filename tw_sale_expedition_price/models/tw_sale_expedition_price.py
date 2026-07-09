from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

from datetime import datetime

class InheritSaleOrder(models.Model):
    _inherit = "tw.sale.order.line"
    # INFO : Connecting Sales Order Line with Expedition Price

    def _get_pricelist_expedition(self):
        pricelist_category = self.env.ref('tw_pricelist.tw_pricelist_data_category_price_product').id
        expedition_obj = self.order_id.company_id.branch_setting_id.expedition_id
        if not expedition_obj:
            raise Warning(f'Default Expedition was not found in the Branch: {self.order_id.company_id.name}\n'
            "- Go to the Master Branch Setting.\n"
            "- Set the 'Default Expedition' to proceed.\n"
            "This configuration is required for proper operation.")

        pricelist_obj = expedition_obj.property_product_pricelist
        if not pricelist_obj:
            raise Warning(
                f"Pricelist Expedition is not set for {expedition_obj.name}.\n"
                "- Go to the Master Expedition.\n"
                "- Set the 'Pricelist' to proceed.\n"
                "This configuration is required for proper operation."
            )
        
        if pricelist_obj.type != 'expedition':
            raise Warning(
                f"Pricelist Expedition is not set for {expedition_obj.name}.\n"
                "- Go to the Master Expedition.\n"
                "- Set the 'Pricelist' to proceed.\n"
                "This configuration is required for proper operation."
            )

        price = 0
        if self.product_id:
            price = pricelist_obj.with_company(self.order_id.company_id.id)._price_get_by_category_price(self.product_id, 1, pricelist_category)[pricelist_obj.id]
            if not price:
                raise Warning(f'Price expedition is not set for product {self.product_id.name}.')
    
        return price
    
    def _get_purchase_price(self, raise_if_not_found=True):
        price = super()._get_purchase_price(raise_if_not_found=raise_if_not_found)
        if self.product_id.categ_id.property_cost_method == 'fifo':
            price += self.with_company(self.order_id.company_id.id)._get_pricelist_expedition()
        return price
        