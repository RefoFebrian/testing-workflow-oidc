# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class InheritSaleOrder(models.Model):
    """
    Inherit Sale Order untuk menambahkan fitur Faktur Pajak.
    Field is_combined_tax dan faktur_pajak_out_id sudah ada dari mixin.
    """
    _name = "tw.sale.order"
    _inherit = ["tw.sale.order", "tw.faktur.pajak.mixin"]
    _description = "Sale Order"

    # 7: defaults methods

    # 8: fields
    # is_combined_tax dan faktur_pajak_out_id sudah ada dari mixin

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & onchange methods

    # 12: override methods

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('order_line'):
                if self._check_lines_for_taxes(vals.get('order_line')):
                    vals['is_combined_tax'] = True
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('order_line'):
            if self._check_lines_for_taxes(vals.get('order_line')):
                vals['is_combined_tax'] = True
            else:
                vals['is_combined_tax'] = False
        return super().write(vals)

    # 13: action methods
    def action_confirm(self):
        """
        Override action_confirm untuk auto-generate faktur pajak
        jika ada pajak dan bukan faktur gabungan.
        """
        result = super().action_confirm()

        for order in self:
            if order.amount_tax and not order.is_combined_tax:
                self.env['tw.faktur.pajak.out'].get_number_of_faktur_pajak(
                    'tw.sale.order', order.id
                )

        return result

    # 14: private methods
    @api.model
    def _check_lines_for_taxes(self, order_lines):
        """
        Helper method to check if any of the order lines contain taxes.
        Compatible with Odoo 18 create/write line commands formats.
        """
        for line in order_lines:
            # Check Odoo ORM command structure for one2many/many2many fields
            # Format is usually (Command, ID, Values_Dict) -> i.e (0, 0, {'product_id': 1, 'tax_id': [...]})
            if len(line) == 3 and isinstance(line[2], dict):
                vals = line[2]
                if vals.get('tax_id'):
                    return True
        return False