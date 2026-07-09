# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class TwSaleOrderPayment(models.Model):
    _name = "tw.dealer.sale.order.payment"
    _description = "Dealer Sale Order Payment"

    # 7: defaults methods

    # 8: fields
    amount_original = fields.Float(string='Original Amount')
    amount_balance = fields.Float(string='Balance')
    amount_allocation = fields.Float(string='Allocated Amount')
    
    # 9: relation fields
    order_id = fields.Many2one(
        comodel_name='tw.dealer.sale.order',
        string='Dealer Sales Order',
        required=True,
        ondelete='cascade')
    payment_entry_id = fields.Many2one(
        comodel_name='account.move.line',
        string='Other Liability',
        copy=False)

    # 10: constraints & sql constraints
    @api.constrains('payment_entry_id', 'amount_allocation')
    def _check_amount_allocation(self):
        for record in self:
            balance = abs(record.payment_entry_id.amount_residual)
            if record.amount_allocation > balance:
                raise ValidationError(_(f"Alokasi amount tidak boleh melebihi sisa balance. \n\nEntry: {record.payment_entry_id.display_name} \nTotal Alokasi: {record.amount_allocation} \nSisa Balance: {balance}"))
            if record.amount_allocation < 0:
                raise ValidationError(_("Alokasi amount harus bernilai positif!"))
    
    # 11: compute/depends & on change methods
    @api.onchange('payment_entry_id')
    def _onchange_payment_entry_id(self):
        if self.payment_entry_id and abs(self.payment_entry_id.amount_residual) > 0:
            self.amount_original = self.payment_entry_id.credit
            self.amount_balance = abs(self.payment_entry_id.amount_residual)
            self.amount_allocation = abs(self.payment_entry_id.amount_residual)

    # 12: override methods

    # 13: action methods

    # 14: private methods
    def _prepare_move_line(self):
        self.ensure_one()
        move_line = self.payment_entry_id.read()[0]
        
        return {
            'debit': move_line.get('credit'),
            'credit': 0,
            'name': self.payment_entry_id.name,
            'ref': self.order_id.name,
            'account_id': move_line.get('account_id')[0],
            'company_id': move_line.get('company_id')[0],
            'division': move_line.get('division')
        }
    
    def _validate_allocation_amount(self):
        payment_amounts = {}
        for payment in self:
            total_allocation = payment.amount_allocation + payment_amounts.get(payment.payment_entry_id.id, 0)
            payment_amounts[payment.payment_entry_id.id] = total_allocation
            if round(total_allocation, 2) > round(payment.amount_balance, 0):
                raise Warning(_(f"Alokasi amount tidak boleh melebihi sisa balance. \n\nEntry: {payment.payment_entry_id.display_name} \nTotal Alokasi: {total_allocation} \nSisa Balance: {payment.amount_balance}"))

