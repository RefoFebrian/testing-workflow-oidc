from collections import defaultdict
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, RedirectWarning
from odoo.fields import Command

class SaleOrderLine(models.Model):
    _name = "tw.sale.order.line"
    _inherit = "sale.order.line"
    _description = "Sale Order Line"
    
    name = fields.Text(
        string="Description",
        compute='_compute_name',
        store=True, readonly=False, required=True, precompute=True)
    cogs = fields.Float('COGS Unit', compute='_compute_cogs', store=True, readonly=False)
    cogs_total = fields.Monetary('HPP Total', compute='_compute_cogs_total', currency_field='currency_id')
    qty_available = fields.Float('Qty Available')

    order_id = fields.Many2one(comodel_name='tw.sale.order', string="Order Reference", required=True, ondelete='cascade', index=True)
    route_id = fields.Many2one('stock.route', string='Route', compute='_compute_route_id', store=True, ondelete='restrict')
    invoice_lines = fields.Many2many(comodel_name='account.move.line', relation='tw_sale_order_line_invoice_rel', column1='order_line_id', column2='invoice_line_id', string="Invoice Lines", copy=False)
    product_document_ids = fields.Many2many(
        string="Product Documents",
        help="The product documents for this order line that will be merged in the PDF quote.",
        comodel_name='product.document',
        relation='tw_sale_order_line_product_document_rel',
        domain="[('id', 'in', available_product_document_ids)]",
        readonly=False,
    )
    move_ids = fields.One2many('stock.move', 'sale_order_line_id', string='Stock Moves')
    
    @api.depends('order_id.company_id', 'order_id.division')  # adjust depends
    def _compute_route_id(self):
        for line in self:
            picking_type = False
            # Check if stock_distribution_id exists (added in another module) and use its PO Type
            if 'stock_distribution_id' in line.order_id._fields and line.order_id.stock_distribution_id:
                picking_type = line.order_id.stock_distribution_id.purchase_order_type_id.default_outgoing_type_id
            
            if not picking_type:
                picking_type = self.env['stock.picking.type'].get_picking_type(
                    'outgoing', line.order_id.company_id.id, line.order_id.division
                )
            if picking_type:
                rule = self.env['stock.rule'].search([
                    ('picking_type_id', '=', picking_type.id),
                    ('location_dest_id', '=', picking_type.default_location_dest_id.id),
                ], order='route_sequence, sequence', limit=1)
                line.route_id = rule.route_id if rule else False
            else:
                line.route_id = False

    @api.constrains('discount')
    def _check_discount_not_negative(self):
        """Validate discount must not be negative."""
        for line in self:
            if line.discount < 0:
                raise Warning('Discount cannot be negative!')
    
    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            if not line.product_id:
                continue

            if line.product_id:
                line.name = line._get_sale_order_line_multiline_description_sale()
                continue

    @api.depends('product_id', 'company_id')
    def _compute_tax_id(self):
        lines_by_company = defaultdict(lambda: self.env['tw.sale.order.line'])
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

    @api.depends('product_id')
    def _compute_cogs(self):
        """Compute Unit HPP (COGS) from product purchase price.
        This field is editable, so manual values will be preserved.
        """
        for record in self:
            if not record.cogs:
                record.cogs = record._get_purchase_price(raise_if_not_found=False)

    @api.depends('cogs', 'product_uom_qty')
    def _compute_cogs_total(self):
        """Compute Total COGS = Unit COGS * Quantity."""
        for record in self:
            record.cogs_total = record.cogs * record.product_uom_qty

    @api.onchange('product_uom_qty')
    def _onchange_qty_validation(self):
        """Validate qty on change."""
        self._validate_order_line()
    
    @api.onchange('product_id')
    def _onchange_product_id_warning(self):
        for rec in self:
            if not rec.product_id:
                return

            product = rec.product_id
            if product.sale_line_warn != 'no-message':
                if product.sale_line_warn == 'block':
                    rec.product_id = False

                return {
                    'warning': {
                        'title': _("Warning for %s", product.name),
                        'message': product.sale_line_warn_msg,
                    }
                }
            
            if not rec.order_id.partner_id:
                raise Warning("Before choosing a product, select a customer in the sales form.")
            
            if not rec.product_id:
                return
        
            warning_msgs = ''
            
            if warning_msgs:
                raise Warning(f"Configuration Error! : \n{warning_msgs}")
            
            # Check Product Price
            rec.get_product_price()
            # Stock availability
            qty_avb = rec.get_quantity_available(rec.order_id.company_id.id, rec.product_id.id, rec.order_id.division, rec.order_id.location_id.id)

            taxes = rec.product_id.supplier_taxes_id or rec.product_id.product_tmpl_id.supplier_taxes_id
            rec.qty_available = qty_avb
            rec.tax_id = [(6, 0, taxes.ids)]
    
    def write(self, values):
        lines = self.env['tw.sale.order.line']
        if 'product_uom_qty' in values:
            lines = self.filtered(lambda r: r.state == 'sale' and not r.is_expense)

        if 'product_packaging_id' in values:
            self.move_ids.filtered(
                lambda m: m.state not in ['cancel', 'done']
            ).product_packaging_id = values['product_packaging_id']

        previous_product_uom_qty = {line.id: line.product_uom_qty for line in lines}
        res = super().write(values)
        if lines:
            lines._action_launch_stock_rule(previous_product_uom_qty)
            # Sync initial_qty to the new demand after procurement engine updates moves
            for line in lines:
                pending_moves = line.move_ids.filtered(
                    lambda m: m.state not in ('done', 'cancel') and m.product_uom_qty
                )
                for move in pending_moves:
                    move.initial_qty = move.product_uom_qty
        return res
    
    def get_product_price(self):
        current_pricelist = self.order_id.get_pricelist()
        if not current_pricelist:
            raise Warning("Attention! The Sale Pricelist Configuration for this Branch is not Available. Please Configure it First.")
        
        current_price = current_pricelist.with_company(self.order_id.company_id)._price_get(self.product_id, self.product_uom_qty, company_id=self.order_id.company_id.id)[current_pricelist.id]
        
        if not current_price:
            raise Warning(f"Attention! The Price for { self.product_id.name } is not found in the Active Pricelist!")
        self.write({'price_unit': current_price})

    def get_quantity_available(self, company_id, product_id, division, location_id):
        for record in self:
            qty_available = record.env['stock.quant'].get_stock_available(product_id, company_id, location_id=location_id)

            record.env['stock.quant'].compare_stock_on_transaction(
                company_id=company_id,
                division=division,
                product_id=product_id,
                qty=record.product_uom_qty,
                location_id=location_id
            )
            
            if qty_available <= 0:
                raise Warning(f"Stock untuk produk {record.product_id.name} tidak tersedia")
            return qty_available

    def _prepare_procurement_values(self, group_id=False):
        values = super()._prepare_procurement_values(group_id)
        self.ensure_one()
        if values.get('sale_line_id'):
            values.pop('sale_line_id')

        values.update({'sale_order_line_id': self.id})
        return values
    
    def _prepare_procurement_group_vals(self):
        vals = super()._prepare_procurement_group_vals()
        if vals.get('sale_id'):
            vals.pop('sale_id')
        return {
            'name': self.order_id.name,
            'move_type': self.order_id.picking_policy,
            'sale_order_id': self.order_id.id,
            'partner_id': self.order_id.partner_shipping_id.id,
        }

    def _get_purchase_price(self, raise_if_not_found=True):
        """Get Unit Purchase Price (COGS per unit).
        
        Args:
            raise_if_not_found: If True, raise Warning when price is not found.
                               If False, return 0 silently (for compute methods).
        """
        price = 0
        if self.product_id:
            categ_obj = self.env['product.category'].with_context(company_id=self.order_id.company_id.id).search([('id', '=', self.product_id.categ_id.id)])
            if categ_obj.property_cost_method == 'fifo':
                pricelist_beli = self.order_id.company_id.branch_setting_id.pricelist_purchase_unit_id
                if not pricelist_beli and raise_if_not_found:
                    raise Warning(f'Pricelist Purchase Unit is not set for {self.order_id.company_id.name}.\n'
                    "- Go to the Master Branch Setting.\n"
                    "- Set the 'Pricelist Purchase Unit' to proceed.\n"
                    "This configuration is required for proper operation.")
                else:
                    price = pricelist_beli.with_company(self.order_id.company_id.id)._price_get(self.product_id, 1)[pricelist_beli.id]
                    
                if price: 
                    tax = self.tax_id            
                    tax_result = tax.compute_all(
                        price,
                        currency=self.currency_id,
                        quantity=1,
                        product=self.product_id,
                    )
                    price_untaxed = tax_result['total_excluded']
                    price = price_untaxed  # Unit price only
            else:
                price = self.with_company(self.order_id.company_id).product_id.standard_price  # Unit price only
            
            if not price and raise_if_not_found:
                raise Warning("No Purchase Price Found for set COGS!\nPlease Check the Pricelist Configuration.")

        return price
    
    def _prepare_invoice_line(self, **optional_values):
        invoice_line = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        invoice_line.pop('sale_line_ids')
        invoice_line.update({
            'company_id': self.order_id.company_id.id,
            'division': self.order_id.division,
            'sale_order_line_ids': [Command.link(self.id)],
        })

        # Ensure cogs (Unit COGS) is computed if not already set
        if self.product_id and not self.cogs:
            unit_price = self.with_company(self.order_id.company_id).sudo()._get_purchase_price()
            if not unit_price:
                raise Warning("No Purchase Price Found for set COGS!\\nPlease Check the Pricelist Configuration.")
            self.update({'cogs': unit_price})
        
        return invoice_line
    
    def _validate_order_line(self):
        """
        Validate order line qty:
        - Qty must be greater than 0
        - Qty must not exceed qty_available
        """
        for line in self:
            if line.product_uom_qty <= 0:
                raise Warning('Quantity cannot be less than or equal to zero')
            
            if line.qty_available and line.product_uom_qty > line.qty_available:
                raise Warning('Quantity must not exceed qty available')
