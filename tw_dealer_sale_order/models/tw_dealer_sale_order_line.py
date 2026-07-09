# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.fields import Command

# 5: local imports

# 6: Import of unknown third party lib


class TwSaleOrderLine(models.Model):
    _name = "tw.dealer.sale.order.line"
    _inherit = "sale.order.line"
    _description = "Dealer Sale Order Line"

    # 7: defaults methods

    # 8: fields
    price_unit_purchase = fields.Float(string="Harga Beli Unit", compute='_compute_price_unit_purchase', store=True)
    downpayment = fields.Float('Uang Muka')
    plat = fields.Selection([('H', 'H'), ('M', 'M')], 'Plat')
    item_type = fields.Selection([('main', 'Main Item'), ('additional', 'Additional Item'), ('line_section', 'Line Section')], 'Item Type', default='main')

    gross_profit_unit = fields.Float(compute='_compute_gross_profit_unit', string='Gross Profit Unit', store=True, help="Gross profit for unit, calculated as total price unit minus total price purchase and accrued expedition.")
    
    finco_incentive = fields.Float()
    finco_incentive_tax = fields.Boolean(string="Incentive Finco Tax")
    finco_po_date = fields.Date(string="Tanggal PO")
    finco_po_number = fields.Char(string="No. PO")
    tenor = fields.Integer(string="Tenor")
    installment = fields.Integer(string="Cicilan")
    
    amount_dealer_expense = fields.Float(string="Beban Dealer", compute='_compute_amount_expense', help="Amount of dealer expense")
    discount_input = fields.Float(string="Discount Input", help="Discount yang di input di Leads dan SPK sebagai panduan ADH untuk memecah diskon")
    discount_regular = fields.Float(string="Discount Regular", help="Extra discount given outside discount detail, formerly discount_po")
    discount_total = fields.Float(compute='_compute_total_discount', help="Amount of discounts or subsidy in the discount detail")
    discount_direct = fields.Float(compute='_compute_total_discount_direct', help="Amount of direct discount")
    price_subtotal = fields.Monetary(string="Subtotal", compute='_compute_amount', store=True, precompute=True)
    price_total = fields.Monetary(string="Total", compute='_compute_amount', store=True, precompute=True)
    price_unit_tax = fields.Float(compute='_compute_price_unit_tax', help="Amount of direct discount")
    
    master_commision_amount = fields.Float('Hutang Komisi Amount (from master data)')
    commision_amount = fields.Float('Amount')
    commision_type = fields.Char('Tipe Komisi')
    chassis_number = fields.Char('No Chassis', compute='_compute_chassis_number', store=True)
    production_year = fields.Char('Tahun Rakit', compute='_compute_production_year', store=True)
    
    stock_aging = fields.Char(compute='_compute_stock_aging', string='Umur')
    recompute_helper = fields.Integer('Recompute Helper', default=1, help='Untuk modul lain men-trigger compute amount, karena depends tidak bisa di tambah, hanya bisa di replace')
    
    # 9: relation fields
    order_id = fields.Many2one('tw.dealer.sale.order',string="Order Reference",required=True, ondelete='cascade', copy=False)
    account_id = fields.Many2one('account.account', string="Account", help='For forcing invoice line on specific account')
    location_id = fields.Many2one('stock.location', string="Location")
    lot_id = fields.Many2one('stock.lot', string="No Mesin")
    move_ids = fields.One2many('stock.move', 'dealer_sale_order_line_id', string='Stock Moves')
    available_lot_ids = fields.Many2many('stock.lot',relation='tw_dealer_sale_order_line_lot_rel',column1='order_line_id', column2='lot_id',compute='_compute_available_lot_ids', readonly=False,store=False)
    tax_id = fields.Many2many('account.tax',string="Taxes",relation='tw_dealer_sale_order_line_tax_rel',column1='order_line_id', column2='tax_id',compute='_compute_tax_id',store=True, readonly=False, precompute=True,context={'active_test': False},check_company=True)
    invoice_lines = fields.Many2many('account.move.line',relation='tw_dealer_sale_order_line_invoice_rel', column1='order_line_id', column2='invoice_line_id',string="Invoice Lines",copy=False)
    
    # this field should be overwrite, because when installing this module, there is an error raise for relation constraints
    product_document_ids = fields.Many2many('product.document',string="Product Documents",help="The product documents for this order line that will be merged in the PDF quote.",relation='tw_dealer_sale_order_line_product_document_rel',domain="[('id', 'in', available_product_document_ids)]",readonly=False)
	
    # 10: constraints & sql constraints
	
    # 11: compute/depends & on change methods
    @api.depends('lot_id')
    def _compute_chassis_number(self):
        for line in self:
            line.chassis_number = line.lot_id.chassis_number
    
    @api.depends('lot_id')
    def _compute_production_year(self):
        for line in self:
            line.production_year = line.lot_id.production_year
    
    @api.depends('discount_regular')
    def _compute_total_discount(self):
        for line in self:
            line.discount_total = line._get_total_discount()
    
    @api.depends('discount_regular')
    def _compute_total_discount_direct(self):
        for line in self:
            line.discount_direct = line._get_total_discount_direct()
    
    @api.depends('discount_regular')
    def _compute_amount_expense(self):
        for line in self:
            line.amount_dealer_expense = line._get_amount_dealer_expense()
    
    @api.depends('tax_id','price_unit','discount_direct')
    def _compute_price_unit_tax(self):
        currency = self.order_id.currency_id or self.order_id.company_id.currency_id
        for line in self:
            tax = line.tax_id
            price_unit = line.price_unit - line.discount_direct
            price_unit = tax.compute_all(price_unit, currency=currency, quantity=line.product_uom_qty)
            total_discount_untaxed = price_unit['total_included'] - price_unit['total_excluded']
            line.price_unit_tax = total_discount_untaxed

    @api.depends('product_uom_qty', 'discount_regular', 'price_unit', 'tax_id', 'recompute_helper')
    def _compute_amount(self):
        for line in self:
            line._recompute_line_totals()

    @api.depends('tax_id', 'price_unit', 'product_uom_qty', 'price_unit_purchase', 'amount_dealer_expense', 'recompute_helper')
    def _compute_gross_profit_unit(self):
        for line in self:
            if line.item_type == 'main' and line.lot_id:
                total_price_unit = line._get_gp_sale_price()
                total_price_purchase = line._get_gp_purchase_price()
                total_price_additional = line._get_gp_additional_price()
                line.gross_profit_unit = total_price_unit - total_price_purchase - total_price_additional
            else:
                line.gross_profit_unit = 0

    @api.depends('product_id', 'company_id')
    def _compute_tax_id(self):
        lines_by_company = defaultdict(lambda: self.env['tw.dealer.sale.order.line'])
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

    @api.depends('product_id', 'location_id')
    def _compute_available_lot_ids(self):
        for line in self:
            available_lot_ids = []
            if line.order_id.state == 'draft' and line.item_type == 'main':
                if line.product_id and line.location_id:
                    partner = line.order_id.partner_id
                    product = line.product_id.with_context(lang=partner.lang, partner_id=partner.id)
                    available_lot_ids = self.env['stock.quant'].get_available_lot_stock(line.product_id.id, line.company_id.id, line.location_id.id).ids
                    reserved_lot = self.env['stock.lot'].search([
                        ('sales_order_reserved_id', 'in', line.order_id.ids),
                        ('location_id', '=', line.location_id.id)
                    ])
                    if reserved_lot:
                        available_lot_ids.append(reserved_lot.id)
            line.available_lot_ids = [(6, 0, available_lot_ids)]

    @api.depends('lot_id')
    def _compute_price_unit_purchase(self):
        for line in self:
            if line.lot_id and line.lot_id.state in ('stock','reserved'):
                line.price_unit_purchase = line.lot_id.with_company(self.company_id).value_svl or line.lot_id.cogs

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id:
            self.location_id = self.lot_id.location_id
    
    @api.onchange('location_id')
    def _onchange_location_id(self):
        if self.location_id != self.lot_id.location_id:
            self.lot_id = False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.lot_id = False
        self.location_id = False
        self.price_unit = False
        self.product_uom_qty = False
        self.tax_id = False
        if self.product_id:
            partner = self.order_id.partner_id
            
            taxes = self._get_taxes()
            pricelist = self._get_pricelist()
            product = self.product_id.with_context(lang=partner.lang,
                                                   partner_id=partner.id)

            self.name = product._get_product_desciption()
            self.price_unit = self._get_price(pricelist, product)
            self.product_uom_qty = 1
            self.tax_id = [(6, 0, taxes.ids)]

    def _compute_stock_aging(self):
        for line in self:
            pass

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        create = super().create(vals_list)
        create._reserve_lot()
        return create
    
    def write(self, vals):
        lines = self.env['tw.dealer.sale.order.line']
        if 'product_uom_qty' in vals:
            lines = self.filtered(lambda r: r.state == 'sale' and not r.is_expense)

        if 'product_packaging_id' in vals:
            self.move_ids.filtered(
                lambda m: m.state not in ['cancel', 'done']
            ).product_packaging_id = values['product_packaging_id']

        previous_product_uom_qty = {line.id: line.product_uom_qty for line in lines}
        written = super().write(vals)
        if lines:
            lines._action_launch_stock_rule(previous_product_uom_qty)
            
        self._reserve_lot()
        return written

    def unlink(self):
        for line in self:
            line.lot_id.write({ 
                'state': 'stock', 
                'sales_order_reserved_id': False, 
                'customer_reserved_id': False 
            })

        return super().unlink()

    # 13: action methods
    def update_lot(self, additional_vals=None):
        for line in self:
            vals = line._prepare_update_lot()
            if additional_vals:
                vals.update(additional_vals)

            line.lot_id.suspend_security().write(vals)
    
    def update_lot_state_paid(self):
        for line in self:
            line.lot_id.suspend_security().write({ 'state': line._prepare_update_lot_state() })

    def _reserve_lot(self):
        for line in self:
            if line.lot_id:
                # Jika ganti lot, atau lot di hapus dari dso line, lepas reserve di lot
                reserved_lot = self.env['stock.lot'].search([
                    ('id', '!=', line.lot_id.id),
                    ('sales_order_reserved_id', '!=', False),
                    ('sales_order_reserved_id', '=', line.order_id.id)
                ])
                if reserved_lot:
                    reserved_lot.write({
                        'state': 'stock',
                        'sales_order_reserved_id': False,
                        'customer_reserved_id': False,
                    })

            # Reserved lot dengan lot baru yang di input.
            # Hanya reserve jika lot masih dalam state 'stock',
            # agar tidak meng-override state lot yang sudah 'sold', 'paid', dsb.
            if line.lot_id and line.lot_id.state == 'stock':
                line.lot_id.write({
                    'sales_order_reserved_id': line.order_id.id,
                    'customer_reserved_id': line.order_id.partner_id.id,
                    'state': 'reserved',
                })
            
	
    # 14: private methods
    def _recompute_line_totals(self):
        for line in self:
            base_line = line._prepare_base_line_for_taxes_computation()
            self.env['account.tax']._add_tax_details_in_base_line(base_line, line.company_id)
            line.price_subtotal = base_line['tax_details']['raw_total_excluded_currency']
            line.price_total = base_line['tax_details']['raw_total_included_currency']
            line.price_tax = line.price_total - line.price_subtotal

    def _get_gp_sale_price(self):
        self.ensure_one()
        price = self.tax_id.compute_all(self.price_unit, currency=self.order_id.currency_id, quantity=self.product_uom_qty)['total_excluded']
        return price

    def _get_gp_purchase_price(self):
        self.ensure_one()
        price = self.price_unit_purchase
        return price

    def _get_gp_additional_price(self):
        self.ensure_one()
        price = self.amount_dealer_expense
        return price

    def _get_total_discount(self):
        self.ensure_one()
        return self.discount_regular
    
    def _get_amount_dealer_expense(self):
        self.ensure_one()
        return self.discount_regular
    
    def _get_total_discount_direct(self):
        self.ensure_one()
        return self.discount_total
    
    def _prepare_base_line_for_taxes_computation(self, **kwargs):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        additional_params = self._get_tax_base_line_additional_params()
        return self.env['account.tax']._prepare_base_line_for_taxes_computation(
            self,
            **additional_params,
        )
    
    def _get_tax_base_line_additional_params(self):
        self.ensure_one()
        return {
            'tax_ids': self.tax_id,
            'quantity': self.product_uom_qty,
            'partner_id': self.order_id.partner_id,
            'currency_id': self.order_id.currency_id or self.order_id.company_id.currency_id,
            'rate': self.order_id.currency_rate,
            'price_unit': self._get_price_after_discount(),
        }

    def _get_price_after_discount(self):
        self.ensure_one()
        return self.price_unit - self.discount_regular

    def _prepare_procurement_values(self, group_id=False):
        values = super()._prepare_procurement_values(group_id)
        self.ensure_one()
        if values.get('sale_line_id'):
            values.pop('sale_line_id')

        values.update({
            'dealer_sale_order_line_id': self.id,
            'location_src_id': self.location_id.id,
        })
        return values
    
    def _prepare_procurement_group_vals(self):
        return {
            'name': self.order_id.name,
            'move_type': self.order_id.picking_policy,
            'dealer_sale_order_id': self.order_id.id,
            'partner_id': self.order_id.partner_shipping_id.id,
        }

    def _create_procurements(self, product_qty, procurement_uom, origin, values):
        self.ensure_one()
        procurement = super()._create_procurements(product_qty, procurement_uom, origin, values)
        return procurement
    
    def _get_pricelist(self):
        self.ensure_one()
        pricelist = self.order_id.pricelist_id
        if not pricelist:
            raise Warning(_("Tidak ada pricelist yang dipilih untuk produk %s! Set pricelist sebelum memilih product.") % self.product_id.display_name)
        return pricelist
        
    def _get_price(self, pricelist, product):
        self.ensure_one()
        price = pricelist.with_company(self.order_id.company_id)._get_product_price(product, self.product_uom_qty, self.order_id.partner_id, company_id=self.order_id.company_id.id)
        if not price:
            raise Warning(_("Tidak ada pricelist line yang ditemukan untuk produk %s! Ubah product, quantity, atau pricelist.") % self.product_id.display_name)
        return price
    
    def _get_taxes(self):
        self.ensure_one()
        taxes = self.product_id.taxes_id or self.product_id.product_tmpl_id.taxes_id
        return taxes

    def _prepare_invoice_line(self, **optional_values):
        """Prepare the values to create the new invoice line for a sales order line.

        :param optional_values: any parameter that should be added to the returned invoice line
        :rtype: dict
        """
        self.ensure_one()
        res = super()._prepare_invoice_line(**optional_values)
        if res.get('sale_line_ids'):
            res.pop('sale_line_ids')
        
        if self.account_id:
            res['account_id'] = self.account_id.id

        res['company_id'] = self.order_id.company_id.id
        res['dealer_sale_order_line_ids'] = [Command.link(self.id)]
        return res
    
    def _prepare_update_lot(self):
        self.ensure_one()
        vals = {
            'dealer_sale_order_id': self.order_id.id,
            'partner_id': self.order_id.partner_id.id,
        }

        if self.downpayment > 0:
            vals['downpayment'] = self.downpayment

        # TODO: next development untuk menambahkan do_date
        # stock_picking = self.env['stock.picking'].search(
        #     [('dealer_sale_order_id', '=', self.order_id.id)],
        #     limit=1
        # )
        # if stock_picking:
        #     vals['do_date'] = stock_picking.date

        return vals
    
    def _prepare_update_lot_state(self):
        return 'paid'
    
