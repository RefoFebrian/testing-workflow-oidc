# 1: imports of python lib

# 2: import of known third party lib
from datetime import datetime, date, time

# 3: imports of odoo
from odoo import api, fields, models, _

from odoo.exceptions import UserError as Warning

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    # 7: defaults methods

    # 8: fields 

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('product_qty', 'product_uom', 'company_id', 'order_id.partner_id', 'price_unit')
    def _compute_price_unit_and_date_planned_and_name(self):
        super()._compute_price_unit_and_date_planned_and_name()
        for line in self:
            if line.product_id and line.product_qty:
                pricelist = line.order_id.pricelist_id
                if not pricelist:
                    pricelist = line.order_id._get_pricelist()
                    if not pricelist:
                        if line.order_id.division =='Umum':
                            pricelist = line.order_id.partner_id.sudo().property_product_pricelist
                product = line.product_id.with_context(pricelist=pricelist.id if pricelist else pricelist, quantity=line.product_qty, date=line.order_id.date_order, uom=line.product_uom.id)
                line.price_unit = line._get_price(pricelist, product)

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _get_price(self, pricelist, product):
        """
        Get price unit from pricelist or fallback to standard_price.
        
        - Jika tidak ada pricelist dan is_only_use_pricelist=True: raise Warning
        - Jika tidak ada pricelist dan is_only_use_pricelist=False: gunakan standard_price
        - Jika ada pricelist: ambil harga dari pricelist via _price_get
          (warning untuk is_only_use_pricelist sudah di-handle di _get_applicable_rules)
        """
        self.ensure_one()
        
        # Jika Pricelist tidak ditemukan atau bernilai False / pricelist() Object Kosong
        if not pricelist:
            # Cek apakah kategori produk wajib pricelist
            if product.categ_id.is_only_use_pricelist:
                raise Warning(_("Pricelist is required for product '%s', Tolong buat pricelist terlebih dahulu." % (product.name)))
            # Jika tidak wajib pricelist, maka ambil standard_price
            return product.standard_price
        
        # Note: _price_get memanggil _get_applicable_rules yang handle warning
        # jika product category is_only_use_pricelist=True dan tidak ada item
        price_unit = pricelist.with_company(self.company_id.id)._price_get(product, self.product_qty).get(pricelist.id, False)
        if not price_unit:
            # Fallback ke standard_price jika tidak ada harga di pricelist
            return product.standard_price
        
        return price_unit    

