from collections import defaultdict
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
from odoo.fields import Command
from odoo.tools import float_compare, float_is_zero


class PartSalesLine(models.Model):
    _name = "tw.part.sales.line"
    _inherit = "sale.order.line"
    _description = "Part Sales Line"

    force_cogs = fields.Float('Force COGS')
    hpp_average = fields.Float('HPP', compute='_compute_hpp', store=True)
    qty_available = fields.Float('Qty Available')
    
    order_id = fields.Many2one(comodel_name='tw.part.sales',string="Order Reference",required=True, ondelete='cascade', index=True)
    invoice_lines = fields.Many2many(comodel_name='account.move.line',relation='tw_part_sales_line_invoice_rel', column1='order_line_id', column2='invoice_line_id',string="Invoice Lines",copy=False)
    product_document_ids = fields.Many2many(string="Product Documents",
        help="The product documents for this order line that will be merged in the PDF quote.",
        comodel_name='product.document',
        relation='tw_part_sales_line_product_document_rel',
        domain="[('id', 'in', available_product_document_ids)]",
        readonly=False,
    )
    location_id = fields.Many2one('stock.location', string='Location')
    
    @api.constrains('product_id')
    def _check_duplicate_product(self):
        for line in self:
            if line.product_id and line.order_id:
                duplicates = line.order_id.order_line.filtered(
                    lambda l:l.product_id == line.product_id
                )
                if len(duplicates) > 1:
                    raise Warning(f"Product '{line.product_id.display_name}' sudah ada di Part Sales Order ini!")

    @api.depends('product_id', 'company_id')
    def _compute_tax_id(self):
        lines_by_company = defaultdict(lambda: self.env['tw.part.sales.line'])
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

    @api.depends('force_cogs')
    def _compute_hpp(self):
        for record in self:
            if record.force_cogs:
                record.hpp_average = record.force_cogs
            # TODO: activate this code if product.price.branch has been migrated
            # else:
            #     record.hpp_average = self.env['product.price.branch']._get_price( record.order_id.warehouse_id.id, record.product_id.id)

    # no trigger product_id.invoice_policy to avoid retroactively changing SO
    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'state')
    def _compute_qty_to_invoice(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in self:            
            if line.state == 'sale' and not line.display_type:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice', 'qty_invoiced')
    def _compute_invoice_status(self):
        """
        Compute the invoice status of a PS line. Possible statuses:
        - no: if the PS is not in status 'sale', we consider that there is nothing to
          invoice. This is also the default value if the conditions of no other status is met.
        - to invoice: we refer to the quantity to invoice of the line. Refer to method
          `_compute_qty_to_invoice()` for more information on how this quantity is calculated.
        - upselling: this is possible only for a product invoiced on ordered quantities for which
          we delivered more than expected. The could arise if, for example, a project took more
          time than expected but we decided not to invoice the extra cost to the client. This
          occurs only in state 'sale', the upselling opportunity is removed from the list.
        - invoiced: the quantity invoiced is larger or equal to the quantity ordered.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if line.state != 'sale':
                line.invoice_status = 'no'
            elif line.is_downpayment and line.untaxed_amount_to_invoice == 0:
                line.invoice_status = 'invoiced'
            elif not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                line.invoice_status = 'to invoice'
            elif line.state == 'sale' and line.product_id.invoice_policy == 'order' and\
                    line.product_uom_qty >= 0.0 and\
                    float_compare(line.qty_delivered, line.product_uom_qty, precision_digits=precision) == 1:
                line.invoice_status = 'upselling'
            # di bawah ini ketika qty product 1 dan qty invoice 1 maka status invoiced (Full Invoice)
            elif float_compare(line.qty_invoiced, line.product_uom_qty, precision_digits=precision) >= 0:
                line.invoice_status = 'invoiced'
            else:
                line.invoice_status = 'no'

    @api.depends('state', 'product_id', 'untaxed_amount_invoiced', 'qty_delivered', 'product_uom_qty', 'price_unit')
    def _compute_untaxed_amount_to_invoice(self):
        """ Total of remaining amount to invoice on the part sales line (taxes excl.) as
                total_sol - amount already invoiced
            where Total_sol depends on the invoice policy of the product.

            Note: Draft invoice are ignored on purpose, the 'to invoice' amount should
            come only from the SO lines.
        """
        for line in self:
            amount_to_invoice = 0.0
            if line.state == 'sale':
                # Note: do not use price_subtotal field as it returns zero when the ordered quantity is
                # zero. It causes problem for expense line (e.i.: ordered qty = 0, deli qty = 4,
                # price_unit = 20 ; subtotal is zero), but when you can invoice the line, you see an
                # amount and not zero. Since we compute untaxed amount, we can use directly the price
                # reduce (to include discount) without using `compute_all()` method on taxes.
                price_subtotal = 0.0
                uom_qty_to_consider = line.qty_delivered if line.product_id.invoice_policy == 'delivery' else line.product_uom_qty
                price_reduce = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                price_subtotal = price_reduce * uom_qty_to_consider
                if len(line.tax_id.filtered(lambda tax: tax.price_include)) > 0:
                    # As included taxes are not excluded from the computed subtotal, `compute_all()` method
                    # has to be called to retrieve the subtotal without them.
                    # `price_reduce_taxexcl` cannot be used as it is computed from `price_subtotal` field. (see upper Note)
                    price_subtotal = line.tax_id.compute_all(
                        price_reduce,
                        currency=line.currency_id,
                        quantity=uom_qty_to_consider,
                        product=line.product_id,
                        partner=line.order_id.partner_shipping_id)['total_excluded']
                inv_lines = line._get_invoice_lines()
                if any(inv_lines.mapped(lambda l: l.discount != line.discount)):
                    # In case of re-invoicing with different discount we try to calculate manually the
                    # remaining amount to invoice
                    amount = 0
                    for l in inv_lines:
                        if len(l.tax_ids.filtered(lambda tax: tax.price_include)) > 0:
                            amount += l.tax_ids.compute_all(l.currency_id._convert(l.price_unit, line.currency_id, line.company_id, l.date or fields.Date.today(), round=False) * l.quantity)['total_excluded']
                        else:
                            amount += l.currency_id._convert(l.price_unit, line.currency_id, line.company_id, l.date or fields.Date.today(), round=False) * l.quantity

                    amount_to_invoice = max(price_subtotal - amount, 0)
                else:
                    amount_to_invoice = price_subtotal - line.untaxed_amount_invoiced

            line.untaxed_amount_to_invoice = amount_to_invoice

    @api.depends('product_id', 'state', 'qty_invoiced', 'qty_delivered')
    def _compute_product_updatable(self):
        self.product_updatable = True
        for line in self:
            if (
                line.is_downpayment
                or line.state == 'cancel'
                or line.state == 'sale' and (
                    line.order_id.locked
                    or line.qty_invoiced > 0
                    or line.qty_delivered > 0
                )
            ):
                line.product_updatable = False

    @api.depends('state')
    def _compute_product_uom_readonly(self):
        for line in self:
            # line.ids checks whether it's a new record not yet saved
            line.product_uom_readonly = line.ids and line.state in ['sale', 'cancel']

    @api.onchange('product_id')
    def _onchange_product_id_set_location(self):
        self._set_location()

    @api.onchange('discount')
    def _onchange_discount(self):
        for record in self:
            if record.discount < 0:
                raise Warning("Discount tidak boleh lebih kecil dari 0.")
 
    @api.onchange('product_id','location_id','product_uom_qty')
    def _onchange_product_id_warning(self):
        product_warning = super()._onchange_product_id_warning()
        if product_warning:
            return product_warning

        if not self.order_id.partner_id:
            raise Warning("Before choosing a product, select a customer in the part sales form.")
        
        if not self.product_id:
            return
        
        product = self.product_id.with_context( lang=self.order_id.partner_id.lang, partner_id=self.order_id.partner_id.id )
        warning_msgs = ''
        
        # Get product name and description
        name = product.display_name
        if product.description_sale:
            name += '\n' + product.description_sale

        if warning_msgs:
            raise Warning(f"Configuration Error! : \n{warning_msgs}")
        
        # Stock availability
        if self.product_id and self.location_id and self.order_id.company_id:
            qty_avb = self.get_quantity_available(self.order_id.company_id.id, self.product_id.id, self.order_id.division, self.location_id.id)
        else:
            qty_avb = 0

        taxes = self.product_id.supplier_taxes_id or self.product_id.product_tmpl_id.supplier_taxes_id
        # self.name = name
        self.qty_available = qty_avb
        self.tax_id = [(6, 0, taxes.ids)]

    
    def _prepare_invoice_line(self, **optional_values):
        part_sales_line = super(PartSalesLine, self)._prepare_invoice_line(**optional_values)
        part_sales_line.pop('sale_line_ids')
        part_sales_line.update({
            'company_id': self.order_id.company_id.id,
            'division': self.order_id.division,
            'part_sales_line_ids': [Command.link(self.id)],
        })

        return part_sales_line
    
    # override method
    @api.model_create_multi
    def create(self, vals):
        for record in vals:
            if record.get('qty_available') > 0 and record.get('product_uom_qty') <= 0:
                raise Warning("Quantity in Order Lines cannot be less than or equal to 0.")
        return super().create(vals)

    def write(self, vals):
        for record in self:
            if 'qty_available' in vals and 'product_uom_qty' in vals:
                qty_available = vals.get('qty_available', record.qty_available)
                qty_uom = vals.get('product_uom_qty', record.product_uom_qty)
                if qty_available > 0 and qty_uom <= 0:
                    raise Warning("Quantity in Order Lines cannot be less than or equal to 0.")
        return super().write(vals)
        

    def get_quantity_available(self, company_id, product_id, division, location_id):        
        qty_available = 0
        for record in self:
            qty_available = self.env['stock.quant'].compare_stock_on_transaction(
                company_id=company_id,
                division=division,
                product_id=product_id,
                qty=record.product_uom_qty,
                location_id=location_id
            )
            
        return qty_available

    def renew_available(self):
        for so_line in self:
            quantity_available = so_line.get_quantity_available(self.order_id.company_id.id, so_line.product_id.id, self.order_id.division, self.location_id.id)
            so_line.qty_available = quantity_available
    
    def _set_location(self):
        for line in self:
            if line.product_id and line.order_id.company_id:
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