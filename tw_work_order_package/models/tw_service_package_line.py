# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwServicePackageLine(models.Model):
    _name = "tw.service.package.line"
    _description = "Detail Paket Service"

    # 7: defaults methods

    # 8: fields
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options_list(['Sparepart','Service']), string='Division', required=True)
    discount = fields.Float(string='Discount (%)')
    quantity = fields.Float(string='Quantity', default=1.0)
    active = fields.Boolean(string='Aktif', default=True)
    create_date = fields.Datetime(string='Created On', readonly=True)
    write_date = fields.Datetime(string='Last Update On', readonly=True)

    # 9: relation fields
    package_id = fields.Many2one('tw.service.package', string='Paket Service', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Produk', required=True)
    create_uid = fields.Many2one('res.users', string='Created By', readonly=True)
    write_uid = fields.Many2one('res.users', string='Last Update By', readonly=True)

    # 10: constraints & sql constraints
    _sql_constraints = [('unique_product_per_package', 'unique(package_id, product_id)', 'Produk yang sama sudah ada dalam paket layanan ini!')]

    # 11: compute/depends & on change methods
    @api.onchange('discount')
    def create_discount(self):
        if self.discount > 100:
            raise UserError("Perhatian! Maksimum Diskon adalah 100%")

        if self.discount < 0:
            raise UserError("Perhatian! Minimum Diskon tidak boleh minus.")

    @api.onchange('division')
    def category_id_by_division(self):
        self.product_id = False

    # 12: override methods

    # 13: action methods
    def toggle_active(self):
        for record in self:
            record.active = not record.active

    # 14: private methods