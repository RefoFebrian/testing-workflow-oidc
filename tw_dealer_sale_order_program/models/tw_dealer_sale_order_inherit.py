# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date
from itertools import groupby

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwDealerSaleOrderProgram(models.Model):
    _inherit = "tw.dealer.sale.order"

    # 7: defaults methods

    # 8: fields
    for_reason_payment = fields.Char('Untuk Pembayaran', help="Formerly known as 'untuk_pembayaran'")
    amount_subsidy = fields.Float(compute='_compute_amount_subsidy', string="Program Subsidi",help="Total of program subsidy amount given for Customer",store=True)
    amount_subsidy_md = fields.Float(compute='_compute_amount_subsidy', string="Program Subsidi MD",help="Total of program subsidy amount given by Main Dealer",store=True)
    amount_subsidy_finco = fields.Float(compute='_compute_amount_subsidy', string="Program Subsidi Finco",help="Total of program subsidy amount given by Finance Company",store=True)
    amount_subsidy_dealer = fields.Float(compute='_compute_amount_subsidy', string="Program Subsidi Dealer",help="Total of program subsidy amount given by Dealer",store=True)
    
    # 9: relation fields
	
    # 10: constraints & sql constraints
	
    # 11: compute/depends & on change methods
    @api.depends('order_line','order_line.sales_program_ids','order_line.amount_subsidy')
    def _compute_amount_subsidy(self):
        for order in self:
            order.amount_subsidy = sum(order.order_line.mapped('amount_subsidy'))
            order.amount_subsidy_md = sum(order.order_line.mapped('amount_subsidy_md'))
            order.amount_subsidy_finco = sum(order.order_line.mapped('amount_subsidy_finco'))
            order.amount_subsidy_dealer = sum(order.order_line.mapped('amount_subsidy_dealer'))
    
    # 12: override methods

    # 13: action methods
    def action_print_report_subsidi_leasing(self):
        self.ensure_one()
        return self.env.ref('tw_dealer_sale_order_discount.subsidi_leasing_dso_report').report_action(self.id)
    
    def action_print_report_subsidi_leasing_wizard(self):
        form_id = self.env.ref('tw_dealer_sale_order_discount.tw_dealer_sale_order_subsidi_leasing_wizard_view').id
        return {
            'name': 'Subsidi Leasing',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dealer.sale.order',
            'views': [(form_id, 'form')],
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
        }
	
    # 14: private methods
    def _validate_dealer_sale_order(self):
        super()._validate_dealer_sale_order()
        for line in self.order_line:
            prod_tmpl = line.product_id.product_tmpl_id
            for program in line.sales_program_ids:
                sales_program = program.sales_program_id.line_ids.filtered(lambda x: x.product_tmpl_id == prod_tmpl)
                if not sales_program:
                    raise Warning(_("Sales Program %s untuk produk %s tidak ditemukan!"%(program.sales_program_id.name, prod_tmpl.name)))
                if not self.finco_id and sales_program.discount_finco > 0:
                    raise Warning(_(f'{sales_program.sales_program_id.name} adalah sales program untuk pembelian kredit.'))

    def _prepare_sumary_discount_data(self, product_id, lines):
        data = super()._prepare_sumary_discount_data(product_id, lines)
        data.update({
            'amount_subsidy': sum(lines.mapped('amount_subsidy')),
            'amount_subsidy_dealer': sum(lines.mapped('amount_subsidy_dealer')),
            'amount_subsidy_md': sum(lines.mapped('amount_subsidy_md')),
            'amount_subsidy_finco': sum(lines.mapped('amount_subsidy_finco')),
        })
        return data
    
    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped, final, date)
        moves += self._create_discount_subsidy_invoice()
        return moves
    
    def _create_discount_subsidy_invoice(self):
        move = self.env['account.move']
        for line in self.order_line:
            move += line.create_subsidy_invoice()
        return move
    
    def _prepare_main_invoice_line(self):
        invoice_line = super()._prepare_main_invoice_line()
        invoice_line += self._prepare_discount_quotation_invoice_line()
        return invoice_line

    def _prepare_discount_quotation_invoice_line(self):
        discount_quotation = self.amount_subsidy
        account_conf = self.company_id.branch_setting_id.account_setting_id
        discount_inv = []
        if discount_quotation > 0:
            if not account_conf.account_dso_discount_quotation_id:
                raise Warning('Konfigurasi Account Discount Quotation pada branch %s belum disetting!' %(self.company_id.name))
            discount_inv += [Command.create(self.order_line[0]._prepare_invoice_line(**{
                'name': 'Discount Quotation',
                'company_id': self.company_id.id,
                'price_unit': -discount_quotation,
                'product_id': False,
                'discount': 0,
                'quantity': 1,
                'account_id': account_conf.account_dso_discount_quotation_id.id
            }))]

        return discount_inv