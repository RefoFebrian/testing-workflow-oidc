# 1: imports of python lib
from datetime import date, datetime, timedelta,time

from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib
class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    # 7: fields

    # 8: relation fields
    part_hotline_product_ids = fields.Many2many('product.product', compute='_compute_hotline_product_ids', string='Allowed Hotline Products')

    # 9: constraints & sql constraints
    @api.depends('order_id.part_hotline_id', 'order_id.order_line.product_id',
                 'order_id.part_hotline_id.purchase_order_ids.state',
                 'order_id.part_hotline_id.purchase_order_ids.order_line.product_id')
    def _compute_hotline_product_ids(self):
        """
        Calculates products that are NOT yet ordered in ANY PO linked to this hotline.
        """
        for rec in self:
            hotline = rec.order_id.part_hotline_id
            if hotline:
                # 1. All products defined in the hotline
                all_hotline_products = hotline.part_detail_ids.mapped('product_id')

                # 2. Get products from ALL non-cancelled POs for this hotline
                existing_pos = hotline.purchase_order_ids.filtered(lambda po: po.state != 'cancel')

                # Products in OTHER POs
                other_pos = existing_pos.filtered(lambda po: po.id != rec.order_id.id)
                products_in_other_pos = other_pos.mapped('order_line.product_id')

                # 3. Products in THIS PO (excluding this line's current selection)
                other_lines_this_po = rec.order_id.order_line - rec
                products_in_this_po = other_lines_this_po.mapped('product_id')

                # 4. Final = Total Hotline Items - (Items in other POs) - (Items in current PO line siblings)
                rec.part_hotline_product_ids = all_hotline_products - products_in_other_pos - products_in_this_po
            else:
                rec.part_hotline_product_ids = self.env['product.product']

    def _get_pricelist(self, company=None):
        if not company:
            company = self.order_id.company_id
        branch_setting = company.branch_setting_id
        if not branch_setting:
            raise Warning(
                'Branch Setting belum dikonfigurasi untuk cabang %s! '
                'Silahkan buka menu Company → Open Branch Setting terlebih dahulu.'
                % company.name
            )
        current_pricelist = branch_setting.pricelist_sale_sparepart_id
        if not current_pricelist:
            raise Warning('Pricelist not found for branch %s!' % branch_setting.name)
        return current_pricelist
