
# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwDealerSaleOrderVoucher(models.Model):
    _name = "tw.dealer.sale.order.line.voucher"
    _description = "Dealer Sale Order Line Voucher"

    # 7: defaults methods
    def _get_domain_subsidy(self):
        # TODO : Domain tanggal, dan produk
        return [('sales_program_type_id.value', '=', 'Program Voucher')]

    # 8: fields
    amount = fields.Float(string='Discount', compute='_compute_amount', store=True)
    
    # 9: relation fields
    order_line_id = fields.Many2one(comodel_name='tw.dealer.sale.order.line', ondelete='cascade')
    voucher_id = fields.Many2one(comodel_name='tw.sales.program', string="Sales Voucher", domain=_get_domain_subsidy)

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.depends('voucher_id')
    def _compute_amount(self):
        for vouch in self:
            product_template = vouch.order_line_id.product_id.product_tmpl_id
            voucher_line = vouch.voucher_id.line_ids.filtered(lambda x: x.product_tmpl_id == product_template)
            if voucher_line:
                vouch.amount = voucher_line.discount_total
    
    @api.onchange('voucher_id')
    def _onchange_amount(self):
        for vouch in self:
            if vouch.voucher_id:
                existing_voucher = vouch.order_line_id.voucher_ids.filtered(lambda x: x.voucher_id == vouch.voucher_id and str(x.id) != str(vouch.id))
                if existing_voucher:
                    raise Warning(_("Voucher %s sudah ada! Tidak bisa menginput voucher yang sama") % vouch.voucher_id.name)

    
    # 12: override methods
    
    # 13: action methods
    
    # 14: private methods
    
    # 15: public methods
    
    # 16: sudo methods
    