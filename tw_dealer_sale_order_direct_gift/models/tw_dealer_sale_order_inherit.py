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

class TwDealerSaleOrder(models.Model):
    _inherit = "tw.dealer.sale.order"

    # 7: defaults methods

    # 8: fields
    amount_direct_gift = fields.Float(compute='_compute_amount_direct_gift', string="Amount Direct Gift", help="Total of direct gift amount given each line.", store=True)
    
    # 9: relation fields
	
    # 10: constraints & sql constraints
	
    # 11: compute/depends & on change methods
    @api.depends('order_line.direct_gift_total')
    def _compute_amount_direct_gift(self):
        for order in self:
            total_direct_gift = 0
            for line in order.order_line:
                total_direct_gift += line.direct_gift_total

            order.amount_direct_gift = total_direct_gift
    
    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        create = super().create(vals_list)
        create._set_direct_gift_lines()
        return create
    
    def write(self, vals):
        write = super().write(vals)
        if vals.get('order_line'):
            self._set_direct_gift_lines()
        return write
    
    # 13: action methods
    def action_set_direct_gift_lines(self):
        self._set_direct_gift_lines()

    # 14: private methods
    def _validate_dealer_sale_order(self):
        super()._validate_dealer_sale_order()
        for line in self.order_line:
            prod_tmpl = line.product_id.product_tmpl_id
            for gift in line.direct_gift_ids:
                direct_gift = gift.direct_gift_id.line_ids.filtered(lambda x: x.product_tmpl_id == prod_tmpl)
                if not direct_gift:
                    raise Warning(_("Direct Gift %s untuk produk %s tidak ditemukan!"%(gift.direct_gift_id.name, prod_tmpl.name)))
                if not self.finco_id and direct_gift.discount_finco > 0:
                    raise Warning(_(f'{direct_gift.sales_program_id.name} adalah direct gift untuk pembelian kredit.'))

    def _set_direct_gift_lines(self):
        for order in self:
            if order.state == 'draft':
                line_with_dg = [disc for line in order.order_line for disc in line.direct_gift_ids]
                to_remove_dg_lines = order.order_line.filtered(lambda l: l.name and l.name.startswith('Direct Gift : ') and l.item_type == 'additional')
                
                if line_with_dg:
                    sequence = max(order.order_line.mapped('sequence')) if order.order_line else 0
                    
                    dg_section = order.order_line.filtered(lambda l: l.name == 'Direct Gift' and l.item_type == 'line_section')
                    if not dg_section:
                        sequence += 1
                        order.order_line = [Command.create({
                            'name': 'Direct Gift',
                            'item_type': 'line_section',
                            'display_type': 'line_section',
                            'sequence': sequence,
                        })]

                    line_with_dg.sort(key=lambda x: x.product_id.id)
                    dg_order_line_vals = []

                    for product, vals in groupby(line_with_dg, key=lambda x: x.product_id):
                        vals_list = list(vals)
                        total_price = sum([val.unit_price * val.quantity for val in vals_list])
                        quantity = sum([val.quantity for val in vals_list])
                        unit_price = total_price / quantity if quantity else 0
                        product_uom = vals_list[0].product_tmpl_id.uom_id.id if vals_list[0].product_tmpl_id else False

                        sequence += 1
                        line_name = f'Direct Gift : {product.name}'
                        existing_dg_line = order.order_line.filtered(lambda l: l.name == line_name and l.item_type == 'additional')
                        
                        if existing_dg_line:
                            to_remove_dg_lines -= existing_dg_line
                            if existing_dg_line.price_unit != unit_price or existing_dg_line.product_uom_qty != quantity:
                                existing_dg_line.write({
                                    'price_unit': unit_price,
                                    'product_uom_qty': quantity,
                                    'sequence': sequence,
                                })
                        else:
                            dg_order_line_vals.append(Command.create({
                                'name': line_name,
                                'item_type': 'additional',
                                'price_unit': unit_price,
                                'product_id': product.id,
                                'product_uom_qty': quantity,
                                'product_uom': product_uom,
                                'discount': 100,
                                'tax_id': False,
                                'sequence': sequence,
                            }))

                    if dg_order_line_vals:
                        order.order_line = dg_order_line_vals
                
                if to_remove_dg_lines:
                    to_remove_dg_lines.unlink()

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped, final, date)
        moves += self._create_direct_gift_invoice()
        return moves
    
    def _prepare_main_invoice_line(self):
        invoice_line = super()._prepare_main_invoice_line()
        return invoice_line

    def _create_direct_gift_invoice(self):
        moves = self.env['account.move'].sudo()
        order_line_direct_gift = self.order_line.filtered(lambda l: l.direct_gift_ids)
        if order_line_direct_gift:
            account_conf = self.company_id.branch_setting_id.account_setting_id
            if not account_conf.journal_dso_direct_gift_md_id:
                raise Warning(_("Journal Direct Gift MD belum di setting di Account Setting!"))
            if not account_conf.journal_dso_direct_gift_md_id.default_credit_account_id:
                raise Warning(_("Default Credit Account di Journal Direct Gift MD belum di setting!"))
            if not account_conf.journal_direct_gift_finco_id:
                raise Warning(_("Journal Direct Gift Finco belum di setting di Account Setting!"))
            if not account_conf.journal_direct_gift_finco_id.default_credit_account_id:
                raise Warning(_("Default Credit Account di Journal Direct Gift Finco belum di setting!"))
            if not self.company_id.default_supplier_id:
                raise Warning(_("Default Supplier belum di setting di Company!"))
            
            # create direct gift invoices
            for line in order_line_direct_gift:
                for gift in line.direct_gift_ids:
                    prefix = self.company_id.code
                    if gift.direct_gift_md > 0 or gift.direct_gift_ahm > 0:
                        code = account_conf.journal_dso_direct_gift_md_id.code
                        md_invoice_vals = self._prepare_invoice()
                        md_invoice_vals.update({
                            'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
                            'move_type': 'out_invoice',
                            'journal_id': account_conf.journal_dso_direct_gift_md_id.id,
                            'partner_id': self.company_id.default_supplier_id.id,
                            'partner_shipping_id': self.company_id.default_supplier_id.id,
                            'invoice_line_ids': [
                                Command.create(line._prepare_invoice_line(**{
                                    'name': f'Subsidi {gift.direct_gift_id.name} {gift.product_tmpl_id.name}',
                                    'price_unit': gift.direct_gift_md + gift.direct_gift_ahm,
                                    'product_id': False,
                                    'discount': 0,
                                    'quantity': 1,
                                    'tax_ids': False,
                                    'account_id': account_conf.journal_dso_direct_gift_md_id.default_credit_account_id.id
                                }))
                            ]
                        })
                        md_invoice = self._create_account_invoices([md_invoice_vals], final=True)
                        moves += md_invoice
                        
                    if gift.direct_gift_finco > 0:
                        if not self.finco_id:
                            raise Warning(_("Direct gift %s tidak bisa digunakan karena DSO tidak menggunakan Finco!"%(gift.direct_gift_id.name)))
                        code = account_conf.journal_direct_gift_finco_id.code
                        finco_invoice_vals = self._prepare_invoice()
                        finco_invoice_vals.update({
                            'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
                            'move_type': 'out_invoice',
                            'journal_id': account_conf.journal_direct_gift_finco_id.id,
                            'partner_id': self.finco_id.id,
                            'partner_shipping_id': self.finco_id.id,
                            'invoice_line_ids': [
                                Command.create(line._prepare_invoice_line(**{
                                    'name': f'Subsidi {gift.direct_gift_id.name} {gift.product_tmpl_id.name}',
                                    'price_unit': gift.direct_gift_finco,
                                    'product_id': False,
                                    'discount': 0,
                                    'quantity': 1,
                                    'tax_ids': False,
                                    'account_id': account_conf.journal_direct_gift_finco_id.default_credit_account_id.id
                                }))
                            ]
                        })
                        
                        finco_invoice = self._create_account_invoices([finco_invoice_vals], final=True)
                        moves += finco_invoice
        
        return moves

    def _prepare_sumary_discount_data(self, product_id, lines):
        data = super()._prepare_sumary_discount_data(product_id, lines)
        data.update({
            'expense_direct_gift': sum(lines.mapped('direct_gift_total')),
        })
        return data
    