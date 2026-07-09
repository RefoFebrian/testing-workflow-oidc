# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from ast import Store
from signal import valid_signals
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwSaleOrderLineBBN(models.Model):
    _inherit = "tw.dealer.sale.order.line"

    # 7: defaults methods

    # 8: fields
    is_bbn = fields.Boolean(string="BBN?", default=False)

    bbn_amount = fields.Float(string="Harga BBN Jual", compute='_compute_bbn_amount', store=True)
    bbn_purchase_amount = fields.Float(string="Harga BBN Beli", compute='_compute_bbn_prices', store=True)
    bbn_notice_amount = fields.Float(string="Notice", compute='_compute_bbn_prices', store=True)
    bbn_process_amount = fields.Float(string="Process", compute='_compute_bbn_prices', store=True)
    bbn_serv_amount = fields.Float(string="Jasa", compute='_compute_bbn_prices', store=True)
    bbn_serv_area_amount = fields.Float(string="Jasa Area", compute='_compute_bbn_prices', store=True)
    bbn_capital_fee_amount = fields.Float(string="Capital Fee", compute='_compute_bbn_prices', store=True)
    bbn_notice_pnbp_amount = fields.Float("Notice + PNBP", compute='_compute_notice_pnbp_amount', store=True)
    bbn_serv_margin_amount = fields.Float("Jasa + Other", compute='_compute_serv_margin_amount', store=True)
    bbn_taxed_amount = fields.Float("BBN Taxes", compute='_compute_bnn_taxed_amount', store=True)
    bbn_force_cogs = fields.Float("BBN Force Cogs", compute='_compute_bbn_force_cogs', store=True)
    
    accrue_bbn_process = fields.Float('Accrue Proses BBN', compute='_compute_accrue_proses_bbn_amount', store=True)
    gross_profit_bbn = fields.Float(compute='_compute_gross_profit_bbn', string='Gross Profit BBN', store=True, help="Gross profit for BBN, calculated as BBN amount minus notice PNBP amount, service amount, and taxes.")
    net_margin = fields.Float(string='Net Margin', compute='_compute_net_margin', store=True)

    # 9: relation fields
    plate_id = fields.Many2one('tw.selection', string='Plate', domain=[('type', '=', 'PlateType')])
    partner_stnk_id = fields.Many2one('res.partner', string="Customer STNK", domain=[('category_id.name', '=', 'Customer')])
    biro_jasa_id = fields.Many2one('res.partner', string='Biro Jasa', domain="[('id', 'in', allowed_biro_jasa_ids)]")
    
    is_city_changed = fields.Boolean('City Changed?', compute='_compute_is_city_changed')
    state_id = fields.Many2one('res.country.state', 'Provinsi', compute='_compute_partner_stnk_location', store=True)
    city_id = fields.Many2one('res.city', 'Kota / Kab', compute='_compute_partner_stnk_location', inverse='_inverse_partner_stnk_location', store=True)
    district_id = fields.Many2one('res.district', 'Kecamatan', compute='_compute_partner_stnk_location', inverse='_inverse_partner_stnk_location', store=True)
    sub_district_id = fields.Many2one('res.sub.district', 'Kelurahan', compute='_compute_partner_stnk_location', inverse='_inverse_partner_stnk_location', store=True)
    
    allowed_biro_jasa_ids = fields.Many2many('res.partner', string='Allowed Biro Jasa', compute='_compute_allowed_birojasa', store=False)
    
    # 10: constraints & sql constraints
	
    # 11: compute/depends & on change methods
    @api.depends('gross_profit_unit', 'gross_profit_bbn', 'tax_id')
    def _compute_net_margin(self):
        """
        Compute the net margin for each sale order line.
        The net margin is calculated as the gross profit unit plus the total included taxes.
        """
        for line in self:
            gp_unit = line.gross_profit_unit
            gp_bbn = line.gross_profit_bbn
            line.net_margin = gp_unit + gp_bbn

    @api.depends('plate_id', 'biro_jasa_id')
    def _compute_bbn_amount(self):
        for line in self:
            if line.plate_id and line.biro_jasa_id:
                line.bbn_amount = line._get_bbn_sales_pricelist_item()
            else:
                line.bbn_amount = 0

    @api.depends('partner_stnk_id', 'biro_jasa_id', 'product_id', 'city_id', 'is_bbn')
    def _compute_bbn_prices(self):
        for line in self:
            if line.partner_stnk_id and line.biro_jasa_id and line.product_id and line.city_id and line.is_bbn:
                purchase_pricelist = line._get_bbn_purchase_pricelist_item()
                line.bbn_purchase_amount = purchase_pricelist.fixed_price
                line.bbn_notice_amount = purchase_pricelist.notice_price
                line.bbn_process_amount = purchase_pricelist.process_price
                line.bbn_serv_amount = purchase_pricelist.serv_price
                line.bbn_serv_area_amount = purchase_pricelist.serv_area_price
                line.bbn_capital_fee_amount = purchase_pricelist.capital_fee_price
            else:
                line.bbn_purchase_amount = 0
                line.bbn_notice_amount = 0
                line.bbn_process_amount = 0
                line.bbn_serv_amount = 0
                line.bbn_serv_area_amount = 0
                line.bbn_capital_fee_amount = 0
    
    @api.depends('is_bbn')
    def _compute_accrue_proses_bbn_amount(self):
        for line in self:
            if line.is_bbn:
                account_conf = line.company_id.branch_setting_id.account_setting_id
                line.accrue_bbn_process = account_conf.accrue_bbn_process if account_conf.is_accrue_proses_bbn else 0
            else:
                line.accrue_bbn_process = 0

    @api.depends('bbn_notice_amount', 'bbn_process_amount')
    def _compute_notice_pnbp_amount(self):
        for line in self:
            line.bbn_notice_pnbp_amount = line._get_bbn_notice_pnbp_amount()

    @api.depends('bbn_amount', 'bbn_notice_amount', 'bbn_process_amount')
    def _compute_serv_margin_amount(self):
        for line in self:
            line.bbn_serv_margin_amount = line._get_bbn_serv_margin_amount()

    @api.depends('is_bbn', 'tax_id', 'biro_jasa_id', 'bbn_amount')
    def _compute_bnn_taxed_amount(self):
        for line in self:
            price_tax = 0
            if line.is_bbn:
                price_tax  = (line.bbn_amount - line.bbn_notice_amount - line.bbn_process_amount) / (1 + line.tax_id.amount/100) * (line.tax_id.amount/100)
            line.bbn_taxed_amount = price_tax

    @api.depends('currency_id', 'company_id', 'bbn_amount',
                 'bbn_serv_amount', 'bbn_notice_amount', 'bbn_process_amount')
    def _compute_bbn_force_cogs(self):
        for line in self:
            line.bbn_force_cogs = line._get_bbn_force_cogs()

    @api.depends('bbn_amount', 'bbn_notice_pnbp_amount', 'bbn_serv_amount', 'accrue_bbn_process', 'tax_id' )
    def _compute_gross_profit_bbn(self):
        """
        Compute the gross profit for BBN.
        The gross profit is calculated as the BBN amount minus the notice PNBP amount,
        service amount, and taxes.
        """
        for line in self:
            line.gross_profit_bbn = line._get_gross_profit_amount_bbn()
    
    @api.depends('is_bbn', 'order_id.company_id')
    def _compute_allowed_birojasa(self):
        for record in self:
            allowed_ids = []
            if record.is_bbn and record.order_id and record.order_id.company_id:
                branch_settings = self.env['tw.branch.setting'].search([
                    ('company_id', '=', record.order_id.company_id.id)
                ], limit=1)
                if branch_settings:
                    allowed_ids = self.env['tw.branch.setting.birojasa'].search([
                        ('branch_setting_id', '=', branch_settings.id)
                    ]).mapped('biro_jasa_id').ids

            record.allowed_biro_jasa_ids = allowed_ids
    
    @api.depends('partner_stnk_id','city_id')
    def _compute_is_city_changed(self):
        for record in self:
            if record.partner_stnk_id:
                record.is_city_changed = record.partner_stnk_id.city_id.id != record.city_id.id
            else:
                record.is_city_changed = False

    @api.depends('partner_stnk_id')
    def _compute_partner_stnk_location(self):
        for record in self:
            if record.partner_stnk_id:
                record.state_id = record.partner_stnk_id.state_id.id
                record.city_id = record.partner_stnk_id.city_id.id
                record.district_id = record.partner_stnk_id.district_id.id
                record.sub_district_id = record.partner_stnk_id.sub_district_id.id
            else:
                record.city_id = False
                record.district_id = False
                record.state_id = False
                record.sub_district_id = False
    
    def _inverse_partner_stnk_location(self):
        for record in self:
            if record.partner_stnk_id:
                if record.city_id != record.partner_stnk_id.city_id.id:
                    record.partner_stnk_id.city_id = record.city_id
                if record.district_id != record.partner_stnk_id.district_id.id:
                    record.partner_stnk_id.district_id = record.district_id
                if record.sub_district_id != record.partner_stnk_id.sub_district_id.id:
                    record.partner_stnk_id.sub_district_id = record.sub_district_id

    @api.onchange('city_id')
    def _onchange_city_id(self):
        if self.city_id and self.city_id.id == self.partner_stnk_id.city_id.id:
            self.district_id = self.partner_stnk_id.district_id.id
            self.sub_district_id = self.partner_stnk_id.sub_district_id.id
        else:
            self.district_id = False
            self.sub_district_id = False

    @api.onchange('district_id')
    def _onchange_district_id(self):
        if self.district_id and self.district_id.id == self.partner_stnk_id.district_id.id:
            self.sub_district_id = self.partner_stnk_id.sub_district_id.id
        else:
            self.sub_district_id = False

    @api.onchange('is_bbn')
    def _onchange_is_bbn(self):
        if not self.is_bbn:
            self.biro_jasa_id = False
            self.plate_id = False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.partner_stnk_id = False
        self.biro_jasa_id = False
        super()._onchange_product_id()

    @api.onchange('partner_stnk_id')
    def _onchange_partner_stnk_id(self):
        self.biro_jasa_id = False
        self.plate_id = False
        if self.partner_stnk_id:
            if not self.partner_stnk_id.city_id:
                raise Warning(_("Silakan set Kota/Kabupaten untuk STNK pelanggan terlebih dahulu"))
            
    @api.onchange('biro_jasa_id')
    def _onchange_biro_jasa_id(self):
        if not self.biro_jasa_id:
            self.plate_id = False
        if self.biro_jasa_id:
            self.order_id._set_bbn_lines()

    # 12: override methods
    def write(self, vals):
        write = super().write(vals)
        if vals.get('product_id') or vals.get('biro_jasa_id') or vals.get('partner_stnk_id') or vals.get('bbn_amount'):
            self.order_id._set_bbn_lines()
        return write

    # 13: action methods
	
    # 14: private methods
    def _get_bbn_notice_pnbp_amount(self):
        self.ensure_one()
        return self.bbn_notice_amount + self.bbn_process_amount
    
    def _get_bbn_serv_margin_amount(self):
        self.ensure_one()
        return self.bbn_amount - (self.bbn_notice_amount + self.bbn_process_amount)
    
    def _get_bbn_taxed_amount(self):
        self.ensure_one()
        currency = self.currency_id or self.company_id.currency_id
        sale_tax = self.company_id.account_sale_tax_id or self.env.user.company_id.account_sale_tax_id

        margin = self.bbn_amount - self._get_bbn_force_cogs()
        margin_taxes = sale_tax.compute_all(margin, currency=currency, quantity=1.0)
        
        return sum([t['amount'] for t in margin_taxes['taxes']])
    
    def _get_bbn_force_cogs(self):
        self.ensure_one()
        currency = self.currency_id or self.company_id.currency_id
        sale_tax = self.company_id.account_sale_tax_id or self.env.user.company_id.account_sale_tax_id
        taxes = sale_tax.compute_all(self.bbn_serv_amount, currency=currency, quantity=1.0)
        bbn_serv_amount = taxes['total_included']
        
        return self.bbn_notice_amount + self.bbn_process_amount + bbn_serv_amount
    
    def _get_gross_profit_amount_bbn(self):
        self.ensure_one()
        harga_jual = self.bbn_amount
        harga_beli = self.bbn_notice_amount + self.bbn_process_amount + self.bbn_serv_amount + self.accrue_bbn_process
        pajak_pengurang = self.bbn_taxed_amount
        total = harga_jual - harga_beli - pajak_pengurang
        return total
    
    def _get_bbn_sales_pricelist_item(self):
        self.ensure_one()
        branch = self.order_id.company_id
        product = self.product_id
        quantity = self.product_uom_qty
        plate = self.plate_id
        pricelist_obj = self.env['product.pricelist']._get_bbn_sales_pricelist(branch, plate)
        
        pricelist = pricelist_obj.with_company(branch.id)
        price_rule = pricelist._compute_price_rule(product, quantity)
        price, rule_id = price_rule.get(product.id, (0, False))

        if not rule_id:
            raise Warning(
                f"Tidak ada pricelist BBN Sales yang ditemukan untuk produk '{product.display_name}'.\n"
                f"- Pricelist: '{pricelist_obj.name}'\n"
                f"- Cabang: '{branch.name}'\n"
                f"- Tipe Plat: '{plate.name}'\n"
                "Silakan konfigurasikan item pricelist yang benar untuk produk ini."
            )

        return price
    
    def _get_bbn_purchase_pricelist_item(self):
        self.ensure_one()
        biro_jasa = self.biro_jasa_id
        branch = self.order_id.company_id
        product = self.product_id
        date_order = self.order_id.date_order
        city = self.city_id
        if not city:
            raise Warning(_("Silakan set Kota/Kabupaten untuk STNK pelanggan terlebih dahulu"))
            
        pricelists = self.env['product.pricelist']._get_bbn_purchase_pricelist(biro_jasa, branch)
        for pricelist in pricelists:
            pricelist_item = pricelist._get_applicable_rules(product, date_order, city_id=city.id)
            if pricelist_item:
                break
            
        if not pricelist_item:
            raise Warning(_(f"Tidak ada aturan yang berlaku untuk produk {product.name} dan kota {city.name} di {pricelist.name}"))
        return pricelist_item
    
    def _prepare_biro_jasa_invoice_line(self, name, product, debit, credit, account_id):
        self.ensure_one()
        return Command.create(self._prepare_invoice_line(**{
            'name': f'{name} {product.default_code}',
            'debit': debit,
            'credit': credit,
            'product_id': False,
            'discount': 0,
            'account_id': account_id,
            'tax_ids': False
        }))
    
    def _prepare_update_lot(self):
        self.ensure_one()
        vals = super()._prepare_update_lot()
        if self.order_id.accrue_bbn_move_id:
            vals['accure_bbn_move_id'] = self.order_id.accrue_bbn_move_id.id
            vals['accrue_bbn_move_line_ids'] = [(6, 0, self.order_id.accrue_bbn_move_id.line_ids.filtered(lambda x: x.credit > 0).ids)]
            vals['service_amount'] = self.bbn_serv_amount
            vals['estimation_amount'] = self.bbn_notice_amount + self.bbn_process_amount + self.bbn_serv_amount

        if self.partner_stnk_id:
            vals['customer_stnk_id'] = self.partner_stnk_id.id
        
        if self.biro_jasa_id:
            vals['biro_jasa_id'] = self.biro_jasa_id.id
        return vals
    
    def _prepare_update_lot_state(self):
        self.ensure_one()
        res = super()._prepare_update_lot_state()
        if not self.is_bbn:
            return 'paid_offtr'
        return res