# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict
from datetime import datetime

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
from odoo.tools import float_compare, float_is_zero
from odoo.fields import Command

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwWorkOrderLine(models.Model):
    _name = "tw.work.order.line"
    _inherit = "sale.order.line"
    _description = "TW Work Order Line"

    # 7: defaults methods

    # 8: fields
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options_list(['Sparepart','Service']), string='Division', required=True)
    qty_available = fields.Float(string='Qty Available')

    # 9: relation fields
    order_id = fields.Many2one(comodel_name='tw.work.order',string="Order Reference",required=True, ondelete='cascade', index=True)
    location_id = fields.Many2one('stock.location', string='Location')
    available_location_ids = fields.Many2many('stock.location', compute='_compute_available_location_ids')

    # Sale Order Line Fields
    invoice_lines = fields.Many2many(comodel_name='account.move.line',relation='tw_work_order_line_invoice_rel', column1='order_line_id', column2='invoice_line_id',string="Invoice Lines",copy=False)
    product_document_ids = fields.Many2many(string="Product Documents",
        help="The product documents for this order line that will be merged in the PDF quote.",
        comodel_name='product.document',
        relation='tw_work_order_line_product_document_rel',
        domain="[('id', 'in', available_product_document_ids)]",
        readonly=False,
    )

    # 10: constraints & sql constraints
    @api.constrains('product_id', 'order_id')
    def _check_duplicate_product(self):
        for line in self:              
            if not line.order_id or not line.product_id:
                continue

            sibling_lines = line.order_id.order_line.filtered(lambda l: l.id != line.id)

            # Cek apakah ada product_id yang sama
            for sl in sibling_lines:
                if sl.product_id.id == line.product_id.id and sl.order_id.id == line.order_id.id:
                    raise Warning(
                        f"Produk '{line.product_id.display_name}' sudah ditambahkan sebelumnya dalam order ini. Tambahkan QTY atau Produk lain."
                    )


    # 11: compute/depends & on change methods

    @api.onchange('division')
    def _onchange_category_id_by_division(self):
        self.product_id = False
        self.location_id = False
        self.price_unit = 0
        self.name = False
        self.qty_available = 0

    @api.depends('product_id', 'order_id.company_id', 'division')
    def _compute_available_location_ids(self):
        for line in self:
            if line.division == 'Sparepart' and line.product_id and line.order_id.company_id:
                quants = self.env['stock.quant'].sudo().search([
                    ('product_id', '=', line.product_id.id),
                    ('company_id', '=', line.order_id.company_id.id),
                    ('location_id.usage', '=', 'internal'),
                    ('quantity', '>', 0)
                ])
                line.available_location_ids = [(6, 0, quants.mapped('location_id').ids)]
            else:
                company_id = line.order_id.company_id.id if line.order_id.company_id else self.env.company.id
                locations = self.env['stock.location'].search([
                    ('company_id', '=', company_id),
                    ('usage', '=', 'internal')
                ])
                line.available_location_ids = [(6, 0, locations.ids)]

    @api.onchange('discount')
    def create_discount(self):
        if self.discount > 100:
            raise Warning("Perhatian! Maksimum Diskon adalah 100%")
        
        if self.discount < 0:
            raise Warning("Perhatian! Minimum Diskon tidak boleh minus.")

    # Sale Order Line
    @api.depends('product_id', 'company_id')
    def _compute_tax_id(self):
        lines_by_company = defaultdict(lambda: self.env['tw.work.order.line'])
        cached_taxes = {}
        for line in self:
            if line.product_type == 'combo':
                line.tax_id = False
                continue
            lines_by_company[line.company_id] += line
        for company, lines in lines_by_company.items():
            for line in lines.with_company(company):
                taxes = None
                if line.product_id:
                    taxes = line.product_id.taxes_id._filter_taxes_by_company(company)
                if not line.product_id or not taxes:
                    # Nothing to map
                    line.tax_id = False
                    continue
                fiscal_position = line.order_id.fiscal_position_id
                cache_key = (fiscal_position.id, company.id, tuple(taxes.ids))
                cache_key += line._get_custom_compute_tax_cache_key()
                if cache_key in cached_taxes:
                    result = cached_taxes[cache_key]
                else:
                    result = fiscal_position.map_tax(taxes)
                    cached_taxes[cache_key] = result
                # If company_id is set, always filter taxes by the company
                line.tax_id = result

    # Sale Order Line
    @api.onchange('product_id','location_id','product_uom_qty')
    def _onchange_product_id_warning(self):
        product_warning = super()._onchange_product_id_warning()
        if product_warning:
            return product_warning

        if not self.order_id.partner_id:
            raise Warning("Before choosing a product, select a customer in the work order form.")
        
        if not self.product_id:
            return

        price_unit = self._get_price()
        if price_unit < 0:
            raise Warning(_("Price for this product is not found in pricelist or price is 0. Please check the pricelist."))

        self.price_unit = price_unit
        
        product = self.product_id.with_context( lang=self.order_id.partner_id.lang, partner_id=self.order_id.partner_id.id)
        warning_msgs = ''
        
        # Get product name and description
        name = product.display_name
        if product.description_sale:
            name += '\n' + product.description_sale

        if warning_msgs:
            raise Warning(f"Configuration Error! : \n{warning_msgs}")
        # Stock availability
        qty_avb = 0
        if self.division and self.product_id and self.location_id and self.order_id.company_id:
            qty_avb = self.get_quantity_available(self.order_id.company_id.id, self.product_id.id, self.division, self.location_id.id)
        
        if not qty_avb and self.division != 'Service':
            raise Warning(_("Stock untuk produk %s tidak ditemukan!" % self.product_id.name))

        taxes = self.product_id.supplier_taxes_id or self.product_id.product_tmpl_id.supplier_taxes_id
        # self.name = name
        self.qty_available = qty_avb
        self.tax_id = [(6, 0, taxes.ids)]

    @api.onchange('product_id', 'division')
    def _onchange_product_id_set_location(self):
        self._set_location()

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        create = super(TwWorkOrderLine, self).create(vals_list)
        for record in create:
            record._check_discount()
        return create

    def write(self,vals):
        for line in self:
            line._check_is_picking(vals)
            if 'product_uom_qty' in vals and vals['product_uom_qty'] < line.product_uom_qty:
                if line.qty_delivered > 0:
                    raise Warning(_(
                        'Tidak dapat mengurangi kuantitas untuk produk "%(product)s", Karena sudah picking.',
                        product=line.product_id.display_name,
                    ))
            if 'product_id' in vals and vals['product_id'] != line.product_id.id:
                if line.qty_delivered > 0:
                    raise Warning(_(
                        'Produk "%(product)s" tidak dapat diubah, Karena sudah picking.',
                        product=line.product_id.display_name,
                    ))
            if 'location_id' in vals and vals['location_id'] != line.location_id.id:
                if line.qty_delivered > 0:
                    raise Warning(_(
                        'Lokasi untuk produk "%(product)s" tidak dapat diubah, Karena sudah picking.',
                        product=line.product_id.display_name,
                    ))

        if vals.get('product_uom_qty') and self.order_id.state not in ['draft','waiting_for_approval']:
            # Update qty picking
            self.order_id.action_supply()
        res = super(TwWorkOrderLine, self).write(vals)
        if 'discount' in vals:
            for record in self:
                record._check_discount()
        return res

    def unlink(self):
        for line in self:
            if line.qty_delivered > 0:
                raise Warning(_('Tidak bisa menghapus data karena sudah ada picking!'))
        return super(TwWorkOrderLine, self).unlink()

    # 13: action methods
    def action_add_from_catalog(self):
        order = self.env['tw.work.order'].browse(self.env.context.get('order_id'))
        return order.action_add_from_catalog()

    # 14: private methods
    def _get_pricelist(self):
        current_pricelist = self.order_id.company_id.branch_setting_id.pricelist_service_id
        if self.division == 'Sparepart':  
            current_pricelist = self.order_id.company_id.branch_setting_id.pricelist_sale_sparepart_id
        
        if not current_pricelist:
            raise Warning(_(f'{self.division}Pricelist not found for branch {self.order_id.company_id.branch_setting_id.name}!'))
        return current_pricelist

    def _get_price(self):
        self.ensure_one()
        price_unit = 0
        pricelist = self._get_pricelist()
        if self.division == 'Service':
            price_unit = pricelist.with_company(self.order_id.company_id.id)._price_get_by_category_service(self.product_id, self.product_uom_qty, category_service=self.order_id.product_id.product_tmpl_id.service_category_id.id)[pricelist.id]
        elif self.division == 'Sparepart':
            price_unit = pricelist.with_company(self.order_id.company_id.id)._price_get(self.product_id, self.product_uom_qty)[pricelist.id]
        return price_unit

    def get_quantity_available(self, company_id, product_id, division, location_id):        
        qty_available = 0
        for record in self:
            if division == 'Sparepart':
                qty_available = self.env['stock.quant'].compare_stock_on_transaction(
                    company_id=company_id,
                    division=division,
                    product_id=product_id,
                    qty=record.product_uom_qty,
                    location_id=location_id
                )
            
        return qty_available

    def _get_harga_jasa(self, product_obj, product_uom_qty, category_service,pricelist):
        if not category_service:
            raise Warning("Category Service tidak ditemukan untuk Produk %s" % product_obj.name)
        harga_jasa = pricelist.with_company(self.order_id.company_id.id)._price_get_by_category_service(product_obj, product_uom_qty, category_service.id)[pricelist.id]
        return harga_jasa

    def _set_location(self):
        for line in self:
            if line.division == 'Sparepart' and line.product_id and line.order_id.company_id:
                quants = self.env['stock.quant'].sudo().search([
                    ('product_id', '=', line.product_id.id),
                    ('company_id', '=', line.order_id.company_id.id),
                    ('location_id.usage', '=', 'internal'),
                    ('quantity', '>', 0)
                ], order='quantity desc', limit=1)

                if quants:
                    line.location_id = quants[0].location_id.sudo().id
                else:
                    line.location_id = False

    # Sale Order Line
    def _prepare_invoice_line(self, **optional_values):
        work_order_line = super(TwWorkOrderLine, self)._prepare_invoice_line(**optional_values)
        work_order_line.pop('sale_line_ids')
        work_order_line.update({
            'company_id': self.order_id.company_id.id,
            'division': self.order_id.division,
            'work_order_line_ids': [Command.link(self.id)],
        })
        return work_order_line

    # Override in TW Work Order Approval
    def _check_discount(self):
        pass

    def _check_is_picking(self, vals):
        if vals.get('product_uom_qty'):
            if vals.get('product_uom_qty') < self.qty_delivered:
                raise Warning(_('Tidak bisa mengubah data karena sudah ada picking!'))