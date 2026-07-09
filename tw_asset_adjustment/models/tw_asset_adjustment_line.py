# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwAssetAdjustmentLine(models.Model):
    """
    Model untuk menyimpan kapitalisasi dari GR ke Asset Adjustment.
    
    Contoh: Adjustment untuk Asset Keramik
    - Kapitalisasi Line 1: GR/002 - Jasa Pemasangan Keramik
    - Kapitalisasi Line 2: GR/003 - Jasa Pengecatan
    
    Total value baru asset = nilai asset saat ini + nilai semua kapitalisasi lines
    """
    _name = "tw.asset.adjustment.line"
    _description = "Asset Adjustment Capitalization Line"
    _order = "id"

    # 7: defaults methods
    
    # 8: fields
    description = fields.Char('Description')
    qty = fields.Float(string='Qty',default=1.0,required=True,help="Jumlah unit kapitalisasi")
    price = fields.Float(string='Total Amount',compute='_compute_price',store=True,readonly=False,help="Total nilai kapitalisasi dari GR Line (qty * unit price)")
    price_unit = fields.Float(string='Unit Price',compute='_compute_price',store=True,help="Harga satuan dari GR Line")
    price_per_unit = fields.Float(string='Amount per Asset',compute='_compute_price_per_unit',store=True,help="Total Amount / qty asset di header (untuk adjustment = price karena 1 asset)")
    
    # 9: relation fields
    adjustment_id = fields.Many2one(comodel_name='tw.asset.adjustment',string='Adjustment',required=True,ondelete='cascade')
    good_receive_id = fields.Many2one(comodel_name='tw.good.receive',string='Good Receive',required=True,domain="[('company_id', '=', parent.company_id), ('state', 'in', ['open', 'done'])]")
    good_receive_line_id = fields.Many2one(comodel_name='tw.good.receive.asset.line',string='GR Line',required=True,domain="[('picking_id', '=', good_receive_id), ('qty_acquisition_available', '>', 0)]")
    product_id = fields.Many2one(related='good_receive_line_id.product_id',string='Product',store=True)
    company_id = fields.Many2one(related='adjustment_id.company_id', store=True)
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.depends('good_receive_line_id', 'good_receive_line_id.price_subtotal', 'qty')
    def _compute_price(self):
        for line in self:
            if line.good_receive_line_id:
                unit_price = line.good_receive_line_id.price_subtotal / (line.good_receive_line_id.qty or 1)
                line.price_unit = unit_price
                line.price = unit_price * (line.qty or 1)
            else:
                line.price_unit = 0.0
                line.price = 0.0
    
    @api.depends('price')
    def _compute_price_per_unit(self):
        """Hitung harga kapitalisasi per unit asset (adjustment = 1 asset)"""
        for line in self:
            # Adjustment selalu untuk 1 asset
            line.price_per_unit = line.price
    
    @api.onchange('good_receive_id')
    def _onchange_good_receive_id(self):
        """Reset GR Line when GR changes"""
        self.good_receive_line_id = False
    
    @api.onchange('good_receive_line_id')
    def _onchange_good_receive_line_id(self):
        """Set description from product name and default qty"""
        if self.good_receive_line_id:
            self.description = self.good_receive_line_id.description or self.good_receive_line_id.product_id.name
            # Default qty to available qty
            self.qty = self.good_receive_line_id.qty_acquisition_available
            
            # Check if this GR Line is already used in other adjustments
            existing_lines = self.env['tw.asset.adjustment.line'].search([
                ('good_receive_line_id', '=', self.good_receive_line_id.id),
                ('id', '!=', self._origin.id if self._origin else False),
                ('adjustment_id.state', '!=', 'post'),
            ])
            
            # Comment untuk testing di button RFA dan Confirm
            # if existing_lines:
            #     # Get adjustment names
            #     good_receive_line_id = self.good_receive_line_id
            #     self.good_receive_line_id = False
            #     adjustment_names = existing_lines.mapped('adjustment_id.name')
            #     return {
            #         'warning': {
            #             'title': _("GR Line Sudah Digunakan"),
            #             'message': _("GR Line %s sudah digunakan di Adjustment yang sudah Posted:\n%s\n\nPastikan tidak terjadi duplikasi kapitalisasi!") % (
            #                 good_receive_line_id.display_name or good_receive_line_id.product_id.name,
            #                 ', '.join(adjustment_names)
            #             )
            #         }
            #     }

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
