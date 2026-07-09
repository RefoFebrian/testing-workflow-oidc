# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwDealerSaleOrderInherit(models.Model):
    _inherit = "tw.dealer.sale.order"

    # 7: defaults methods

    # 8: fields
    amount_commission = fields.Float(compute='_compute_amounts', string='Total Commission', store=True, help="The total amount.")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('order_line.price_subtotal', 'currency_id', 'company_id')
    def _compute_amounts(self):
        super()._compute_amounts()
        for order in self:
            amt_commission = 0
            for line in order.order_line:
                amt_commission += line.amount_commission_pph
            order.amount_commission = amt_commission
    
    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        create = super().create(vals_list)
        return create

    def write(self, vals):
        write = super().write(vals)
        return write

    # 13: action methods

    # 14: private methods
    def _validate_dealer_sale_order(self):
        super()._validate_dealer_sale_order()
        for line in self.order_line:
            if line.item_type == 'main':
                if self.mediator_id:
                    if not all([line.commission_id, line.amount_commission]):
                        raise Warning(_("Jika Mediator di isi, Commission harus di isi!"))
                if line.commission_id and not self.mediator_id:
                    raise Warning(_("Jika Commission di isi, Mediator harus di isi!"))
    
    def _prepare_sumary_discount_data(self, product_id, lines):
        data = super()._prepare_sumary_discount_data(product_id, lines)
        expense_commission = 0
        # Process all lines for this product
        for line in lines:
            # Calculate total commission for this line
            expense_commission += line.amount_commission

        data.update({
            'expense_commission': expense_commission,
        })
        return data
    
    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped, final, date)
        moves += self._create_commission_invoice()
        return moves

    def _create_commission_invoice(self):
        move = self.env['account.move']
        if self.amount_commission > 0:
            inv_commission = False
            account_setting_obj = self.company_id.branch_setting_id.account_setting_id
            if not account_setting_obj.journal_dso_commission_id:
                raise Warning('Konfigurasi Journal Commission belum disetting!')
            if not self.mediator_id:
                raise Warning('Mediator belum diisi! Harus di isi jika hutang komisi di isi.')
            if not account_setting_obj.journal_dso_commission_id.default_debit_account_id.id:
                raise Warning('Konfigurasi default debit account pada journal %s belum disetting!' %(account_setting_obj.journal_dso_commission_id.name))

            prefix = self.company_id.code
            code = account_setting_obj.journal_dso_commission_id.code

            inv_commission = self._prepare_invoice()
            inv_commission.update({
                'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
                'move_type': 'in_invoice',
                'journal_id': account_setting_obj.journal_dso_commission_id.id,
                'partner_id': self.mediator_id.id,
                'partner_shipping_id': self.mediator_id.id,
                'invoice_line_ids': []
            })

            line_vals = []
            order_line = self.order_line.filtered(lambda l: l.item_type == 'main')
            for line in order_line:
                if line.amount_commission:
                    if not line.commission_tax_id:
                        raise Warning('Konfigurasi Pajak Hutang Komisi belum disetting!')
                    line_vals.append(Command.create(line._prepare_invoice_line(**{
                        'name': 'Hutang Komisi %s' % str(line.product_id.name),
                        'product_id': False,
                        'discount': 0,
                        'quantity': line.product_uom_qty,
                        'account_id': account_setting_obj.journal_dso_commission_id.default_debit_account_id.id,
                        'price_unit': line.amount_commission_pph / line.product_uom_qty,
                        'tax_ids': [Command.set([line.commission_tax_id.id])]
                    })))
            inv_commission['invoice_line_ids'] = line_vals
            move = self._create_account_invoices(inv_commission, final=True)
        return move