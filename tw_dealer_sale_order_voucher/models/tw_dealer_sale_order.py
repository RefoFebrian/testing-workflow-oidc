# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class InheritTwDealerSaleOrder(models.Model):
    _inherit = "tw.dealer.sale.order"

    # 7: defaults methods

    # 8: fields
    amount_voucher = fields.Float(compute='_compute_amount_voucher', string="Amount Voucher", help="Total of voucher amount given each line. Previously this field was called amount_voucher", store=True)
    
    # 9: relation fields
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.depends('order_line.amount_voucher','order_line')
    def _compute_amount_voucher(self):
        for order in self:
            total_voucher = 0
            for line in order.order_line:
                total_voucher += line.amount_voucher
            order.amount_voucher = total_voucher

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        return res

    def write(self, vals):
        res = super().write(vals)
        return res

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            order._update_lot_with_voucher()
        return res
        
    # 14: private methods 
    def _update_lot_with_voucher(self):
        self.ensure_one()
        if not self.order_line:
            return

        # Prepare batch data
        voucher_vals_list = []
        lot_vouchers = {}  # {lot_id: [voucher_vals]}
        
        for line in self.order_line.filtered('lot_id'):
            if not line.voucher_ids:
                continue
                
            lot_id = line.lot_id.id
            if lot_id not in lot_vouchers:
                lot_vouchers[lot_id] = {'lot': line.lot_id, 'vouchers': []}
                
            for voucher in line.voucher_ids:
                vals = {
                    'name': voucher.voucher_id.name,
                    'voucher_id': voucher.voucher_id.id,
                    'lot_id': lot_id,
                    'sale_order_id': self.id,
                    'amount': voucher.amount,
                    'date': date.today()
                }
                voucher_vals_list.append(vals)
                lot_vouchers[lot_id]['vouchers'].append(vals)
        
        if voucher_vals_list:
            # Create all vouchers in one query
            vouchers = self.env['tw.sales.voucher'].suspend_security().create(voucher_vals_list)
            
            # Update lots with their vouchers
            voucher_mapping = {
                (voucher['lot_id'], voucher['voucher_id']): voucher_id 
                for voucher, voucher_id in zip(voucher_vals_list, vouchers.ids)
            }
            
            # Update each lot with its vouchers
            for lot_id, data in lot_vouchers.items():
                lot = data['lot']
                voucher_ids = [
                    voucher_mapping[(lot_id, voucher['voucher_id'])]
                    for voucher in data['vouchers']
                ]
                if voucher_ids:
                    lot.suspend_security().write({
                        'voucher_ids': [(6, 0, voucher_ids)]  # Replace all existing with new ones
                    })
    
    def _validate_dealer_sale_order(self):
        super()._validate_dealer_sale_order()
        for order in self:
            for line in self.order_line:
                if line.amount_voucher > 0:
                    if line.amount_voucher > line.discount_regular:
                        raise Warning(_("Transaksi ini memiliki voucher, Jumlah diskon Pelanggan %s tidak boleh kurang dari nominal voucher %s !"% (order.discount_regular, order.amount_voucher)))
    
    def _prepare_sumary_discount_data(self, product_id, lines):
        data = super()._prepare_sumary_discount_data(product_id, lines)
        data.update({
            'amount_voucher': sum(lines.mapped('amount_voucher')),
        })
        return data

    def _get_direct_discount(self):
        discount = super()._get_direct_discount()
        discount -= self.amount_voucher
        return discount

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped, final, date)
        moves += self.create_voucher_invoice()
        return moves
    
    def create_voucher_invoice(self):
        move = self.env['account.move']
        if self.amount_voucher > 0:
            account_setting_obj = self.company_id.branch_setting_id.account_setting_id
            journal_voucher = account_setting_obj.journal_dso_voucher_id
                    
            if not journal_voucher:
                raise Warning('Konfigurasi Journal Voucher belum disetting!')
            if not journal_voucher.default_credit_account_id.id:
                raise Warning('Konfigurasi default credit account pada journal %s belum disetting!' %(journal_voucher.name))
            
            for line in self.order_line:
                for voucher in line.voucher_ids:              
                    voucher_name = voucher.voucher_id.name if voucher.voucher_id.name else ''
                    product_name = line.product_id.name if line.product_id.name else ''
                    inv_vals = self._prepare_invoice()

                    code = journal_voucher.code
                    prefix = self.company_id.code
                    name = self.env['ir.sequence'].get_sequence_code(code, prefix)
                    inv_vals.update({
                        'name': name,
                        'move_type': 'entry',
                        'division': 'Sparepart',
                        'journal_id': journal_voucher.id,
                        'partner_id': line.partner_stnk_id.id if line.partner_stnk_id.id else self.partner_id.id,
                        'partner_shipping_id': self.partner_shipping_id.id,
                        'line_ids': [
                            Command.create(line._prepare_invoice_line(**{
                                'name': 'Voucher %s %s' % (voucher_name, product_name),
                                'division': 'Sparepart',
                                'credit': voucher.amount,
                                'debit': 0,
                                'product_id': False,
                                'discount': 0,
                                'quantity': 1,
                                'account_id': journal_voucher.default_credit_account_id.id,
                                'tax_ids': False
                            })),
                            Command.create(line._prepare_invoice_line(**{
                                'name': name,
                                'division': 'Sparepart',
                                'credit': 0,
                                'debit': voucher.amount,
                                'product_id': False,
                                'discount': 0,
                                'quantity': 1,
                                'account_id': journal_voucher.default_debit_account_id.id,
                                'tax_ids': False
                            })),
                        ],
                    })

            if inv_vals:
                move = self._create_account_invoices([inv_vals], final=True)
        return move