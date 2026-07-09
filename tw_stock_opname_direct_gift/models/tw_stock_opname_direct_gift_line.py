# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, api, fields

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwStockOpnameDirectGiftLine(models.Model):
    _name = "tw.stock.opname.direct.gift.line"
    _description = "TW Stock Opname Direct Gift Line"

    # 7: defaults methods

    # 8: fields
    name = fields.Char('Description')
    unit_price = fields.Float('Harga Satuan')
    qty = fields.Float('Qty Sistem')
    amount = fields.Float('Amount Total Sistem', compute='_compute_amount')
    qty_physical_good = fields.Float('Qty Fisik Baik')
    qty_physical_broken = fields.Float('Qty Fisik Rusak')
    qty_physical_total = fields.Float('Total Qty Fisik',compute='_compute_fisik_total')
    amount_total = fields.Float('Amount Total Fisik',compute='_compute_amount_total')
    diff_qty = fields.Float('Selisih Qty',compute='_compute_selisih_qty')
    diff_amount = fields.Float('Selisih Amount',compute='_compute_selisih_amount')
    balance_log_book = fields.Float('Saldo Logbook')
    aging = fields.Integer('Aging')

    # 9: relation fields
    opname_id = fields.Many2one('tw.stock.opname.direct.gift', 'Stock Opname', ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Product')

    # 10: constraints & sql constraints
    @api.constrains('qty_physical_good', 'qty_physical_broken')
    def _check_qty_physical(self):
        for rec in self:
            if rec.qty_physical_good < 0 or rec.qty_physical_broken < 0:
                raise ValidationError('Qty Fisik Baik dan Qty Fisik Rusak tidak boleh negatif')

    @api.constrains('balance_log_book')
    def _check_balance_log_book(self):
        for rec in self:
            if rec.balance_log_book < 0:
                raise ValidationError('Saldo Logbook tidak boleh negatif')

    # 11: compute/depends & on change methods
    @api.depends('qty_physical_good', 'qty_physical_broken')
    def _compute_fisik_total(self):
        for rec in self:
            rec.qty_physical_total = rec.qty_physical_good + rec.qty_physical_broken

    @api.depends('unit_price', 'qty')
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.unit_price * rec.qty

    @api.depends('unit_price', 'qty_physical_total')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = rec.unit_price * rec.qty_physical_total

    @api.depends('qty', 'qty_physical_total')
    def _compute_selisih_qty(self):
        for rec in self:
            rec.diff_qty = rec.qty_physical_total - rec.qty

    @api.depends('unit_price', 'diff_qty')
    def _compute_selisih_amount(self):
        for rec in self:
            rec.diff_amount = rec.unit_price * rec.diff_qty

    # 12: override methods

    # 13: action methods

    # 14: private methods