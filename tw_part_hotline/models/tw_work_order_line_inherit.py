# 1: imports of python lib
from datetime import date, datetime, timedelta, time

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning, ValidationError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrderLine(models.Model):
    _inherit = "tw.work.order.line"

    # 7: default methods

    # 8: fields

    # 9: relation fields
    part_hotline_id = fields.Many2one(
        'tw.part.hotline',
        string="No Hotline",
        domain="[('customer_id', '=', parent.partner_id), ('company_id', '=', parent.company_id), ('state', '=', 'approved'), ('status_po', '=', 'done')]"
    )
    # available_hotline_product_ids = fields.Many2many('product.product', string='Domain Product Hotline', compute='_compute_available_hotline_product_ids')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    # TODO: Catatan : Jika pakai domain bikin lemot view
    # @api.depends('part_hotline_id')
    # def _compute_available_hotline_product_ids(self):
    #     all_saleable = self.env['product.product'].search([('sale_ok', '=', True)]).ids
    #     for line in self:
    #         if line.part_hotline_id:
    #             item_ids = [
    #                 detail.product_id.id
    #                 for detail in line.part_hotline_id.part_detail_ids
    #                 if detail.qty_available > 0 and detail.qty_available > detail.qty_reserved
    #             ]
    #             line.available_hotline_product_ids = [(6, 0, item_ids)]
    #         else:
    #             line.available_hotline_product_ids = [(6, 0, all_saleable)]

    @api.onchange('division')
    def _onchange_category_id_by_division(self):
        """Override: skip reset when division change came from hotline selection."""
        if self.part_hotline_id:
            self.part_hotline_id = False
        return super()._onchange_category_id_by_division()

    # @api.onchange('product_id', 'location_id', 'product_uom_qty')
    # def _onchange_product_id_warning(self):
    #     """Override: skip price/tax recalculation when product change came from hotline selection."""
    #     if self.part_hotline_id:
    #         return
    #     return super()._onchange_product_id_warning()

    @api.onchange('product_id', 'division')
    def _onchange_product_id_set_location(self):
        """Override: skip location reset when product change came from hotline selection."""
        if self.part_hotline_id:
            return
        return super()._onchange_product_id_set_location()

    @api.onchange('part_hotline_id')
    def _onchange_part_hotline_id(self):
        """When a hotline is selected on a WO line, populate product from hotline detail."""
        self.location_id = False
        self.product_id = False
        self.name = False
        self.product_qty = 0
        self.product_uom_qty = 0
        self.price_unit = 0
        self.discount = 0
        self.product_uom = False
        self.qty_available = 0
        self.tax_id = False
        if not self.part_hotline_id:
            return
        location_obj = self.env['stock.location'].search([
            ('company_id', '=', self.order_id.company_id.id),
            ('name', '=', 'Hotline')
        ], limit=1)
        stock_quant_obj = self.env['stock.quant']

        # Collect products already used in sibling lines for this hotline
        existing_products = self.order_id.order_line.filtered(
            lambda l: l.part_hotline_id.id == self.part_hotline_id.id and l.id != self._origin.id
        ).mapped('product_id.id')

        available_details = []
        for detail in self.part_hotline_id.part_detail_ids:
            if detail.product_id.id in existing_products:
                continue
            if detail.qty_available > 0 and detail.qty_available > detail.qty_reserved:
                available_details.append(detail)

        if not available_details:
            raise Warning('Tidak ada product yang tersedia pada Hotline %s!' % self.part_hotline_id.name)

        # Fill current line with the first available product
        first_detail = available_details[0]
        product_qty = first_detail.qty_available - first_detail.qty_reserved
        qty_avb = stock_quant_obj.compare_stock_on_transaction(
            self.part_hotline_id.company_id.id, 'Sparepart',
            first_detail.product_id.id, product_qty, location_obj.id
        )
        self.division = 'Sparepart'
        self.location_id = location_obj.id
        self.name = first_detail.product_id.display_name
        self.product_id = first_detail.product_id.id
        self.product_qty = product_qty
        self.product_uom_qty = product_qty
        self.price_unit = first_detail.price
        self.discount = 0
        self.product_uom = first_detail.product_id.uom_id.id
        self.qty_available = qty_avb
        self.tax_id = [(6, 0, first_detail.product_id.taxes_id.ids)]
        if hasattr(self, 'warranty'):
            self.warranty = first_detail.product_id.product_tmpl_id.categ_id.warranty

        # Add remaining products as new order lines
        new_lines = []
        for detail in available_details[1:]:
            product_qty = detail.qty_available - detail.qty_reserved
            qty_avb = stock_quant_obj.compare_stock_on_transaction(
                self.part_hotline_id.company_id.id, 'Sparepart',
                detail.product_id.id, product_qty, location_obj.id
            )
            vals = {
                'part_hotline_id': self.part_hotline_id.id,
                'division': 'Sparepart',
                'location_id': location_obj.id,
                'product_id': detail.product_id.id,
                'name': detail.product_id.display_name,
                'product_qty': product_qty,
                'product_uom_qty': product_qty,
                'price_unit': detail.price,
                'discount': 0,
                'product_uom': detail.product_id.uom_id.id,
                'qty_available': qty_avb,
                'tax_id': [(6, 0, detail.product_id.taxes_id.ids)],
            }
            if hasattr(self, 'warranty'):
                vals['warranty'] = detail.product_id.product_tmpl_id.categ_id.warranty
            new_lines.append((0, 0, vals))

        if new_lines:
            self.order_id.update({'order_line': new_lines})