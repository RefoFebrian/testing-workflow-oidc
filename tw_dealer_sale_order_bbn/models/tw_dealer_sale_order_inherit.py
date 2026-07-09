# -*- coding: utf-8 -*-

# 1: imports of python lib
import itertools

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, Command, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from itertools import groupby

# 5: local imports

# 6: Import of unknown third party lib


class TwSaleOrderBBN(models.Model):
    _inherit = "tw.dealer.sale.order"

    # 7: defaults methods

    # 8: fields
    amount_bbn = fields.Float(compute='_compute_amounts_bbn', string='Total BBN', store=True, help="The total amount.")
    amount_gp_bbn = fields.Float(compute='_compute_amounts_bbn', string='GP BBN', store=True, help="Total Gross Profit BBN.")
    amount_bbn_notice_pnbp = fields.Float(compute='_compute_amounts_bbn', string='Total BBN Notice + PNBP', store=True, help='Total BBN Notice + PNBP')
    amount_vat_gp_bbn = fields.Float(compute='_compute_amounts_bbn', string='Pajak BBN Margin', store=True, help='(GP BBN / Tax Amount Percentage) * Tax')

    # 9: relation fields
    accrue_bbn_move_id = fields.Many2one('account.move', string='Accrue BBN Move')
    city_ids = fields.Many2many('res.city', 'Kota / Kab', compute='_compute_partner_stnk_location')
    district_ids = fields.Many2many('res.district', 'Kecamatan', compute='_compute_partner_stnk_location')
    
    # 10: constraints & sql constraints
	
    # 11: compute/depends & on change methods
    @api.depends('order_line.city_id', 'order_line.district_id')
    def _compute_partner_stnk_location(self):
        for order in self:
            order.city_ids = order.order_line.mapped('city_id')
            order.district_ids = order.order_line.mapped('district_id')
    
    @api.depends('order_line', 'order_line.bbn_amount', 'order_line.gross_profit_bbn', 'order_line.bbn_notice_pnbp_amount')
    def _compute_amounts_bbn(self):
        for order in self:
            total_gp_bbn = total_bbn_notice_pnbp = total_bbn_amount = total_gp_bbn_vat = 0
            for line in order.order_line:
                total_bbn_amount += line.bbn_amount
                total_gp_bbn += line.gross_profit_bbn
                total_gp_bbn_vat += line.bbn_amount - line.bbn_purchase_amount - line.gross_profit_bbn
                total_bbn_notice_pnbp += line.bbn_notice_pnbp_amount
            order.amount_bbn = total_bbn_amount
            order.amount_gp_bbn = total_gp_bbn
            order.amount_bbn_notice_pnbp = total_bbn_notice_pnbp
            order.amount_vat_gp_bbn = total_gp_bbn_vat

    # 12: override base methods
    @api.model_create_multi
    def create(self, vals_list):
        create = super().create(vals_list)
        self._set_bbn_lines()
        return create
    
    def write(self, vals):
        write = super().write(vals)
        if vals.get('order_line'):
            self._set_bbn_lines()
        return write

    # 13: action methods
    def action_set_bbn_lines(self):
        self._set_bbn_lines()
	
    # 14: private methods
    def _validate_dealer_sale_order(self):
        super()._validate_dealer_sale_order()
        
        # Check if there are products with BBN lines but no BBN lines
        product_with_bbn_lines = self.order_line.filtered(lambda l: l.is_bbn)
        bbn_lines = self.order_line.filtered(lambda l: l.name.startswith('BBN') and l.item_type == 'additional')
        if product_with_bbn_lines and not bbn_lines:
            self._set_bbn_lines()

    def _set_bbn_lines(self):
        for order in self:
            if order.state == 'draft':
                product_with_bbn_lines = order.order_line.filtered(lambda l: l.is_bbn)
                to_remove_bbn_lines = order.order_line.filtered(lambda l: l.name.startswith('BBN') and l.item_type == 'additional')
                if product_with_bbn_lines:
                    account_conf = self.company_id.branch_setting_id.account_setting_id
                    account_id = account_conf.account_dso_sales_bbn_id.id
                    if not account_id:
                        raise Warning(_("Akun untuk penjualan BBN belum dikonfigurasi.\nSilakan konfigurasikan di menu pengaturan cabang."))
                    
                    sequence = max(product_with_bbn_lines.mapped('sequence'))
                    bbn_section = order.order_line.filtered(lambda l: l.name == 'BBN' and l.item_type == 'line_section')
                    if not bbn_section:
                        sequence += 1
                        order.order_line = [Command.create({
                            'name': 'BBN',
                            'item_type': 'line_section',
                            'is_bbn': False,
                            'tax_id': False,
                            'display_type': 'line_section',
                            'sequence': sequence,
                        })]

                    for product, lines in groupby(product_with_bbn_lines, key=lambda x: x.product_id):
                        lines = sum(lines, self.env['tw.dealer.sale.order.line'])
                        # qty = sum([rec.product_uom_qty for rec in line])
                        line_count = len(lines)
                        total_notice_pnbp = sum(line.bbn_notice_pnbp_amount for line in lines)/line_count
                        total_serv_margin = sum(line.bbn_serv_margin_amount for line in lines)/line_count
                        product_uom = lines[0].product_uom.id
                        sequence += 1
                        
                        bbn_order_line_vals = []
                        existing_bbn_notice_pnbp = order.order_line.filtered(lambda l: l.name == f'BBN Notice + PNBP {product.default_code}')
                        if existing_bbn_notice_pnbp:
                            to_remove_bbn_lines -= existing_bbn_notice_pnbp
                            if existing_bbn_notice_pnbp.price_unit != total_notice_pnbp:
                                existing_bbn_notice_pnbp.write({
                                    'price_unit': total_notice_pnbp,
                                    'product_uom_qty': line_count,
                                })
                        else:
                            bbn_order_line_vals.append(Command.create({
                                'name': f'BBN Notice + PNBP {product.default_code}',
                                'item_type': 'additional',
                                'price_unit': total_notice_pnbp,
                                'product_id': False,
                                'account_id': account_id,
                                'product_uom_qty': line_count,
                                'product_uom': product_uom,
                                'discount': 0,
                                'tax_id': False,
                                'sequence': sequence,
                            }))
                        
                        # BBN JASA + OTHERS
                        existing_bbn_jasa_others = order.order_line.filtered(lambda l: l.name == f'BBN Jasa + Others {product.default_code}')
                        if existing_bbn_jasa_others:
                            to_remove_bbn_lines -= existing_bbn_jasa_others
                            if existing_bbn_jasa_others.price_unit != total_serv_margin:
                                sequence += 1
                                existing_bbn_jasa_others.write({
                                    'price_unit': total_serv_margin,
                                    'product_uom_qty': line_count,
                                    'sequence': sequence,
                                })
                        else:
                            sequence += 1
                            bbn_order_line_vals.append(Command.create({
                                'name': f'BBN Jasa + Others {product.default_code}',
                                'item_type': 'additional',
                                'price_unit': total_serv_margin,
                                'product_id': False,
                                'account_id': account_id,
                                'product_uom_qty': line_count,
                                'product_uom': product_uom,
                                'discount': 0,
                                'tax_id': [Command.set(lines.mapped('tax_id').ids)],
                                'sequence': sequence,
                            }))

                        order.order_line = bbn_order_line_vals
                
                if to_remove_bbn_lines:
                    to_remove_bbn_lines.unlink()

    def _prepare_main_invoice_line(self):
        invoice_line = super()._prepare_main_invoice_line()
        return invoice_line
    
    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped, final, date)
        bbn_move = self._create_accrue_bbn_invoice()
        # Simpan untuk di sync ke lot
        self.accrue_bbn_move_id = bbn_move
        # Tambahkan ke moves
        moves += bbn_move
        return moves

    def _create_accrue_bbn_invoice(self):
        move = self.env['account.move']
        invoice_vals = self._prepare_accrue_bbn_invoice()
        if invoice_vals:
            move = self._create_account_invoices(invoice_vals, final=True)
        return move

    def _prepare_accrue_bbn_invoice(self):
        account_conf = self.company_id.branch_setting_id.account_setting_id
        invoice_vals = {}
        bbn_lines = self.order_line.filtered(lambda l: l.is_bbn)
        if bbn_lines:
            # Check configuration
            if not account_conf.journal_dso_purchase_bbn_id:
                raise Warning(_("Journal untuk Journal Pembelian BBN belum dikonfigurasi.\nSilakan konfigurasikan di menu pengaturan akun."))
            debit_account_id = account_conf.journal_dso_purchase_bbn_id.default_debit_account_id.id
            if not debit_account_id:
                raise Warning(_("account debit default untuk Journal Pembelian BBN belum dikonfigurasi.\nSilakan konfigurasikan di menu pengaturan akun."))
            credit_account_id = account_conf.journal_dso_purchase_bbn_id.default_credit_account_id.id
            if not credit_account_id:
                raise Warning(_("account kredit default untuk Journal Pembelian BBN belum dikonfigurasi.\nSilakan konfigurasikan di menu pengaturan akun."))

            for biro_jasa, record in groupby(bbn_lines, key=lambda x: x.biro_jasa_id):
                invoice_vals.update(self._prepare_invoice_biro_jasa(biro_jasa))
                invoice_vals['invoice_line_ids'] = []
                
                sorted_record = sorted(record, key=lambda x: x.product_id)
                grouped_record = itertools.groupby(iterable=sorted_record, key=lambda x: x.product_id)
                
                total = 0
                for product, rec in grouped_record:    
                    bbn_notice_amount = bbn_process_amount = bbn_serv_amount = qty = 0
                    lines = list(rec)
                    for line in lines:
                        bbn_notice_amount += line.bbn_notice_amount
                        bbn_process_amount += line.bbn_process_amount
                        bbn_serv_amount += line.bbn_serv_amount
                        total += line.bbn_notice_amount + line.bbn_process_amount + line.bbn_serv_amount

                    invoice_vals['invoice_line_ids'] += [
                        lines[0]._prepare_biro_jasa_invoice_line('BBN Notice', product, bbn_notice_amount, 0, debit_account_id),
                        lines[0]._prepare_biro_jasa_invoice_line('BBN PNBP', product, bbn_process_amount, 0, debit_account_id),
                        lines[0]._prepare_biro_jasa_invoice_line('BBN Jasa', product, bbn_serv_amount, 0, debit_account_id)
                    ]

                invoice_vals['invoice_line_ids'] += [lines[0]._prepare_biro_jasa_invoice_line(self.name, product, 0, total, credit_account_id)]

        return invoice_vals
    
    def _prepare_sumary_discount_data(self, product_id, lines):
        data = super()._prepare_sumary_discount_data(product_id, lines)
        data.update({
            'bbn_amount': sum(lines.mapped('bbn_amount')),
            'bbn_purchase_amount': sum(lines.mapped('bbn_purchase_amount')),
            'bbn_taxed_amount': sum(lines.mapped('bbn_taxed_amount')),
            'gross_profit_bbn': sum(lines.mapped('gross_profit_bbn')),
        })
        return data
    
    def _prepare_invoice_biro_jasa(self, biro_jasa):
        account_conf = self.company_id.branch_setting_id.account_setting_id
        bbn_invoice = self._prepare_invoice()
        code = account_conf.journal_dso_purchase_bbn_id.code
        prefix = self.company_id.code
        bbn_invoice.update({
            'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
            'move_type': 'entry',
            'journal_id': account_conf.journal_dso_purchase_bbn_id.id,
            'partner_id': biro_jasa.id,
            'partner_shipping_id': biro_jasa.id
        })
        
        return bbn_invoice
