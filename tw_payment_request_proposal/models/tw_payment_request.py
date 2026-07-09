# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class InheritAccountPaymentRequest(models.Model):
    _inherit = "tw.payment.request"

    # 8: fields

    # 9: relation fields
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    
    @api.depends('payable_move_line_ids.full_reconcile_id')
    def _compute_is_paid(self):
        super()._compute_is_paid()
            
    @api.onchange('proposal_id')
    def _onchange_proposal_id(self):
        self.memo = False
        self.proposal_limit_amount = 0
        self.line_dr_ids = []
        for line in self.line_dr_ids:
            if line.proposal_line_id.proposal_id != self.proposal_id:
                line.proposal_line_id = False
                
        if self.proposal_id:
            self.memo = self.proposal_id.event
            self.action_update_proposal_limit()
    # 12: override methods
    
    # 13: action methods

    def action_validate(self):
        
        validate = super().action_validate()
        
        for payment in self:
            if payment.proposal_id:
                payment._check_proposal_state()
                payment._check_proposal_amount()
                payment._update_proposal_payment()
                payment.action_update_proposal_limit()

        return validate

    def action_request_approval(self):
        for payment in self:
            if payment.proposal_id:
                payment._check_proposal_state()
                payment._check_proposal_amount()
        return super().action_request_approval()
    
    
    # 14: private methods
    
    def _update_proposal_payment_paid(self):
        item_update = []
        for line in self.line_dr_ids:
            if line.proposal_line_id:
                amount_paid = line.proposal_line_id.suspend_security().amount_paid
                item_update.append([1, line.proposal_line_id.id, {
                    'amount_paid': amount_paid + line.amount,
                }])
        self.proposal_id.suspend_security().write({'line_ids': item_update})

    def _update_proposal_payment(self):
        self.env['tw.proposal.payment'].suspend_security().create({
            'proposal_id': self.proposal_id.id,
            'name': str(self.name),
            'payment_model_id': self.env['ir.model'].suspend_security().search([('model','=',str(self.__class__.__name__))]).id,
            'payment_transaction_id': self.id,
            'payment_date': self.date,
            'payment_amount': self.amount
        })
        # update item proposal
        item_update = []
        for line in self.line_dr_ids:
            if line.proposal_line_id:
                amount_reserved = line.proposal_line_id.suspend_security().amount_reserved
                #TODO: dikomen karena diupdate di saat payment request sudah paid di supplier payment, sebelumnya di update disini pada saat payment request di validate
                # amount_paid = line.proposal_line_id.suspend_security().amount_paid
                item_update.append([1, line.proposal_line_id.id, {
                    'amount_reserved': amount_reserved + line.amount,
                    # 'amount_paid': amount_paid,
                    'payment_ids': [[0, 0, {
                        'name': line.payment_id.name,
                        'supplier_id': line.payment_id.partner_id.id,
                        'pay_to': 'vendor',
                        # 'amount_paid': line.amount,
                    }]]
                }])
        self.proposal_id.suspend_security().write({'line_ids': item_update})

    def _get_proposal_limit(self):
        amount = super()._get_proposal_limit()
        supplier_line = self.proposal_id.line_ids.filtered(lambda pl: pl.supplier_id.id == self.partner_id.id)
        if supplier_line:
            amount_supplier_total = sum(pl.amount_total for pl in supplier_line)
            amount_supplier_paid_reserved = sum(pl.amount_paid - pl.amount_reserved for pl in supplier_line)
            amount_supplier_limit = amount_supplier_total - amount_supplier_paid_reserved
            if self.proposal_id.state == 'approved':
                amount = amount_supplier_limit
            elif self.proposal_id.state == 'waiting_for_approval':
                amount_approved = self.proposal_id.amount_approved - (self.proposal_id.amount_paid + self.proposal_id.amount_reserved)
                amount = min(amount_approved, amount_supplier_limit)
        return amount

    def _update_proposal_amount_paid(self, reconciled_amount=0):
        """
        Update amount_paid dan amount_reserved di proposal setiap pembayaran (partial/full).
        Dipanggil dari tw.account.payment.action_validate setelah reconcile.
        """
        if not reconciled_amount:
            return
        total_line_amount = sum(line.amount for line in self.line_dr_ids if line.proposal_line_id)
        if not total_line_amount:
            return
        item_update = []
        for line in self.line_dr_ids:
            if line.proposal_line_id:
                ratio = line.amount / total_line_amount
                paid_increment = reconciled_amount * ratio
                amount_reserved = line.proposal_line_id.suspend_security().amount_reserved
                amount_paid = line.proposal_line_id.suspend_security().amount_paid
                item_update.append([1, line.proposal_line_id.id, {
                    'amount_reserved': max(amount_reserved - paid_increment, 0),
                    'amount_paid': amount_paid + paid_increment,
                }])
        if item_update:
            self.proposal_id.suspend_security().write({'line_ids': item_update})