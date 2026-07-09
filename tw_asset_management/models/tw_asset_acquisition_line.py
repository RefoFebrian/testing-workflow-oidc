# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwAssetAcquisitionLine(models.Model):
    """
    Model untuk menyimpan kapitalisasi dari GR tambahan.
    
    Contoh: Akuisisi Keramik (GR/001)
    - Kapitalisasi Line 1: GR/002 - Jasa Pemasangan Keramik
    - Kapitalisasi Line 2: GR/003 - Jasa Pengecatan
    
    Total value asset = nilai Keramik + nilai semua kapitalisasi lines
    """
    _name = "tw.asset.acquisition.line"
    _description = "Asset Acquisition Capitalization Line"
    _order = "id"

    # 7: defaults methods
    
    # 8: fields
    description = fields.Char('Description')
    qty = fields.Float(
        string='Qty',
        default=1.0,
        required=True,
        help="Jumlah unit kapitalisasi"
    )
    price = fields.Float(
        string='Total Amount',
        compute='_compute_price',
        store=True,
        readonly=False,
        help="Total nilai kapitalisasi dari GR Line (qty * unit price)"
    )
    price_unit = fields.Float(
        string='Unit Price',
        compute='_compute_price',
        store=True,
        help="Harga satuan dari GR Line"
    )
    price_tax = fields.Float(
        string='Tax Amount',
        compute='_compute_price',
        store=True,
        help="Jumlah pajak dari kapitalisasi line"
    )
    price_subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_price',
        store=True,
        help="Subtotal sebelum pajak"
    )
    price_total = fields.Float(
        string='Total (Inc. Tax)',
        compute='_compute_price',
        store=True,
        help="Total termasuk pajak"
    )
    price_per_unit = fields.Float(
        string='Amount per Asset',
        compute='_compute_price_per_unit',
        store=True,
        help="Total Amount / qty asset di header (untuk dibagi ke masing-masing asset)"
    )
    
    # 9: relation fields
    acquisition_id = fields.Many2one(
        comodel_name='tw.asset.acquisition',
        string='Acquisition',
        required=True,
        ondelete='cascade'
    )
    good_receive_id = fields.Many2one(
        comodel_name='tw.good.receive',
        string='Good Receive',
        required=True,
        domain="[('company_id', '=', parent.company_id), ('state', 'in', ['open', 'done']), ('move_asset_ids.is_acquired', '=', False)]"
    )
    good_receive_line_id = fields.Many2one(
        comodel_name='tw.good.receive.asset.line',
        string='GR Line',
        required=True,
        domain="[('picking_id', '=', good_receive_id), ('is_acquired', '=', False)]"
    )
    product_id = fields.Many2one(
        related='good_receive_line_id.product_id',
        string='Product',
        store=True
    )
    tax_ids = fields.Many2many(
        'account.tax',
        'tw_asset_acquisition_line_tax',
        'acquisition_line_id',
        'tax_id',
        string='Taxes'
    )
    company_id = fields.Many2one(related='acquisition_id.company_id', store=True)
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.depends('good_receive_line_id', 'good_receive_line_id.price_subtotal', 'qty', 'tax_ids')
    def _compute_price(self):
        for line in self:
            if line.good_receive_line_id:
                unit_price = line.good_receive_line_id.price_subtotal / (line.good_receive_line_id.qty or 1)
                line.price_unit = unit_price
                subtotal = unit_price * (line.qty or 1)
                line.price = subtotal

                # Hitung pajak mengikuti dari GR Line
                tax_amount = 0.0
                price_total = subtotal
                if line.tax_ids:
                    currency = line.company_id.currency_id
                    computed_tax = line.tax_ids.compute_all(subtotal, currency)
                    price_total = computed_tax.get('total_included', subtotal)
                    tax_amount = sum(t['amount'] for t in computed_tax.get('taxes', []))

                line.price_tax = tax_amount
                line.price_subtotal = subtotal
                line.price_total = price_total
            else:
                line.price_unit = 0.0
                line.price = 0.0
                line.price_tax = 0.0
                line.price_subtotal = 0.0
                line.price_total = 0.0
    
    @api.depends('price', 'acquisition_id.qty')
    def _compute_price_per_unit(self):
        """Hitung harga kapitalisasi per unit asset"""
        for line in self:
            acquisition_qty = line.acquisition_id.qty or 1
            line.price_per_unit = line.price / acquisition_qty if acquisition_qty > 0 else line.price
    
    @api.onchange('good_receive_id')
    def _onchange_good_receive_id(self):
        """Reset GR Line when GR changes"""
        self.good_receive_line_id = False
    
    @api.onchange('good_receive_line_id')
    def _onchange_good_receive_line_id(self):
        """Set description, tax, and qty from GR Line. Validate not same as header."""
        if self.good_receive_line_id:
            # Check if this is the same GR Line as header (self-capitalization not allowed)
            if self.acquisition_id.good_receive_line_id and self.good_receive_line_id.id == self.acquisition_id.good_receive_line_id.id:
                self.good_receive_line_id = False
                return {
                    'warning': {
                        'title': _("Tidak Diperbolehkan"),
                        'message': _("GR Line ini sama dengan GR Line di header akuisisi. Tidak bisa mengkapitalisasi dirinya sendiri!")
                    }
                }
            
            self.description = self.good_receive_line_id.product_id.name
            # Default qty to available qty
            self.qty = self.good_receive_line_id.qty_acquisition_available
            # Auto-fill tax dari GR Line
            self.tax_ids = [(6, 0, self.good_receive_line_id.tax_ids.ids)]

    @api.onchange('qty')
    def _onchange_qty(self):
        """Warn if qty exceeds available"""
        if self.good_receive_line_id and self.qty > self.good_receive_line_id.qty_acquisition_available:
            self.qty = self.good_receive_line_id.qty_acquisition_available
            return {
                'warning': {
                    'title': _("Warning"),
                    'message': _("Qty Kapitalisasi (%d) melebihi Qty Available (%d) pada GR Line %s!") % (
                        self.qty, self.good_receive_line_id.qty_acquisition_available, self.good_receive_line_id.name)
                }
            }
    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods
