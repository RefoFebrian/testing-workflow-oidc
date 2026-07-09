# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, Command, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class InheritTwDealerSaleOrderLine(models.Model):
    _inherit = "tw.dealer.sale.order.line"
    
    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    voucher_ids = fields.One2many(comodel_name='tw.dealer.sale.order.line.voucher', inverse_name='order_line_id', string="Voucher Program")
    amount_voucher = fields.Float(compute='_compute_amount_voucher', string="Amount Voucher", help="Total of voucher amount given each line. Previously this field was called amount_voucher", store=True)
    

    @api.depends('voucher_ids','voucher_ids.amount')
    def _compute_amount_voucher(self):
        for order_line in self:
            total_voucher = 0
            for voucher in order_line.voucher_ids:
                total_voucher += voucher.amount
            order_line.recompute_helper += 1
            order_line.amount_voucher = total_voucher
    
    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for order_line in res:
            order_line._insert_voucher()
        return res

    def write(self, vals):
        res = super().write(vals)
        for order_line in self:
            if vals.get('product_id') or vals.get('discount_regular'):
                order_line._insert_voucher()
            if not getattr(order_line.order_id, 'is_dgi', False):
                order_line._validate_voucher()
        return res

    # 13: action methods
    def action_set_voucher(self):
        for order_line in self:
            order_line._insert_voucher()
            order_line._validate_voucher()

    # 14: private methods
    def _get_price_after_discount(self):
        self.ensure_one()
        price = super()._get_price_after_discount()
        # Angka voucher mengambil dari diskon reguler (EX : Diskon reguler 500.000 voucher 150.000. Maka harga unit = 20.000.000 - (500.000 - 150.000))
        return price + self.amount_voucher
    
    def _get_total_discount_direct(self):
        self.ensure_one()
        discount = super()._get_total_discount_direct()
        return discount - self.amount_voucher

    def _insert_voucher(self):
        for line in self:
            if line.order_id.state == 'draft':
                voucher = []
                branch = line.order_id.company_id
                voucher_master_obj = self.env['tw.sales.program'].search([
                    ('company_id', 'in', [branch.id, branch.parent_id.id] if branch.parent_id else [branch.id]),
                    ('sales_program_type_id.value', '=', 'Program Voucher'),
                    ('state', '=', 'approved'),
                    ('active', '=', True),
                    ('end_date', '>=', date.today()),
                    ('start_date', '<=', date.today())
                    ], limit=1)

                if voucher_master_obj:
                    if line.voucher_ids and line.voucher_ids.mapped('voucher_id.id') != [voucher_master_obj.id]:
                        line.voucher_ids.unlink()

                    if voucher_master_obj.id not in line.voucher_ids.mapped('voucher_id.id'):
                        voucher_line = voucher_master_obj.line_ids.filtered(lambda x: x.product_tmpl_id == line.product_id.product_tmpl_id)
                        if voucher_line:
                            voucher.append(Command.create({
                                'voucher_id': voucher_master_obj.id,
                                'amount': voucher_line.discount_total,
                            }))
                            line.voucher_ids = voucher
                        else:
                            line.voucher_ids.unlink()
                else:
                    line.voucher_ids.unlink()

    def _validate_voucher(self):
        for line in self:
            if line.amount_voucher:
                if line.amount_voucher > line.discount_regular:
                    raise Warning(_("Transaksi ini memiliki voucher, Jumlah diskon Pelanggan %s tidak boleh kurang dari nominal voucher %s !"% (line.discount_regular, line.amount_voucher)))