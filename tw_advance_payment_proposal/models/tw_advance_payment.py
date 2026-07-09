# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT
# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwAdvancePaymentInheritProposal(models.Model):
    _inherit = "tw.advance.payment"

    # 7: default methods

    # 8: fields
    proposal_total_amount = fields.Float(string='Proposal Total Amount',compute='_compute_proposal_amount', digits='Product Price',store=True)

    # 9: relation fields
    proposal_item_ids = fields.One2many('tw.advance.payment.proposal', 'advance_payment_id', string='Detail Proposal')

    # 10: constraints & sql constraints
    @api.constrains('amount')
    def _check_amount(self):
        if self.type == 'advance_payment':
            if not self.proposal_id and self.amount <= 0:
                raise Warning('Total amount harus lebih dari 0.')

            if self.proposal_id:
                if self.amount != self.proposal_total_amount:
                    raise Warning('Total amount tidak sesuai dengan total proposal.')
    
    @api.constrains('proposal_item_ids')
    def _check_empty_proposal_line(self):
        if self.type == 'advance_payment':
            if self.proposal_id and len(self.proposal_item_ids) <= 0:
                raise Warning('Detail Proposal harus diisi.')

    # 11: compute/depends & on change methods
    @api.depends('proposal_item_ids.amount_total', 'proposal_id')
    def _compute_proposal_amount(self):
        for record in self:
            if record.type == 'advance_payment' and record.proposal_id:
                total, paid, reserved = record.proposal_id.get_proposal_amounts_by_pay_to('pic')
                record.proposal_total_amount = total
            else:
                record.proposal_total_amount = 0.0


    @api.onchange('proposal_id')
    def _onchange_description_and_limit(self):
        if self.type == 'advance_payment':
            self.description = False
            self.amount = 0
            self.proposal_limit_amount = 0
            self.proposal_item_ids = []
            if self.proposal_id:
                self.description = self.proposal_id.event
                self.update_proposal_limit()

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('proposal_id', False):
                amount = 0
                for x in vals['proposal_item_ids']:
                    if x[2]: # 0 Create
                        amount += x[2]['amount_total']
                vals['amount_total'] = amount
                vals['amount'] = amount
        create = super().create(vals_list)
        create._check_proposal_amount()
        return create
    
    def write(self, values):
        if values.get('proposal_item_ids', False):
            amount = 0
            amount_total = 0
            for x in values['proposal_item_ids']:
                if x[0] == 0: # 0 Create
                    amount_total = x[2]['amount_total']
                elif x[0] in [1,4]:
                    item_obj = self.proposal_item_ids.suspend_security().browse(x[1])
                    if x[2]:
                        amount_total = x[2]['amount_total'] if x[2].get('amount_total', False) else item_obj.amount_total
                    else:
                        amount_total = item_obj.amount_total
                amount +=  amount_total
            values['amount_total'] = amount
        write = super().write(values)
        # Hanya cek proposal amount saat data proposal berubah
        if values.get('proposal_item_ids') or values.get('amount') or values.get('proposal_id'):
            for avp in self:
                avp._check_proposal_amount()
        return write

    def copy(self):
        raise Warning('Tidak bisa duplikat data.')

    # 13: action methods
    def action_set_to_draft(self):
        if self.proposal_id:
            self._unset_amount_reserved()
        super().action_set_to_draft()

    def action_validate(self):
        for avp in self:
            if avp.type == 'advance_payment' and avp.proposal_id:
                if avp.employee_id != avp.proposal_id.pic_id:
                    raise Warning(
                        'Employee pada Advance Payment harus sama dengan PIC pada Proposal %s.' % avp.proposal_id.name
                    )
                avp._process_proposal()
        return super().action_validate()

    def action_confirm(self):
        if self.type == 'advance_payment':
            # amount_reserved sudah di-set saat validate via _process_proposal
            # listing pembayaran sudah dibuat saat validate via _process_proposal
            if self.proposal_id:
                self._check_proposal_state()
                # setup item proposal: pindahkan amount_reserved ke amount_paid
                item_update = []
                for item in self.proposal_item_ids:
                    amount_reserved = item.proposal_line_id.suspend_security().amount_reserved
                    amount_paid = item.proposal_line_id.suspend_security().amount_paid
                    item_update.append([1, item.proposal_line_id.id, {
                        'amount_reserved': amount_reserved - item.amount_total,
                        'amount_paid': amount_paid + item.amount_total,
                    }])
                # update proposal
                try:
                    self.proposal_id.suspend_security().write({'line_ids': item_update})
                except Exception:
                    self._cr.rollback()
                    raise Warning('Terjadi kesalahan saat update item Proposal %s.' % self.proposal_id.name)

        return True

    

    # 14: private methods

    def _process_proposal(self):
        # Dijalankan saat validate, buat listing pembayaran di proposal (sama seperti Payment Request)
        if self.proposal_id:
            self._check_proposal_state()
            self.update_proposal_limit()
            self._check_proposal_amount()

            # Buat listing pembayaran di proposal header
            self.env['tw.proposal.payment'].suspend_security().create({
                'proposal_id': self.proposal_id.id,
                'name': str(self.name),
                'payment_model_id': self.env['ir.model'].suspend_security().search([('model','=',str(self.__class__.__name__))]).id,
                'payment_transaction_id': self.id,
                'payment_date': self.date,
                'payment_amount': self.amount
            })

            # setup item proposal
            item_update = []
            for proposal_item in self.proposal_item_ids:
                amount_reserved = proposal_item.proposal_line_id.suspend_security().amount_reserved
                item_update.append([1, proposal_item.proposal_line_id.id, {
                    'amount_reserved': amount_reserved + proposal_item.amount_total,
                    'payment_ids': [[0, 0, {
                        'name': self.name,
                        'supplier_id': False,
                        'pay_to': 'pic',
                    }]]
                }])
            # update proposal
            try:
                self.proposal_id.suspend_security().write({'line_ids': item_update})
            except Exception:
                self._cr.rollback()
                raise Warning('Terjadi kesalahan saat update proposal %s.' % (self.proposal_id.suspend_security().name))

    def update_proposal_limit(self):
        if self.type == 'advance_payment' and self.proposal_id:
            total, paid, reserved = self.proposal_id.get_proposal_amounts_by_pay_to('pic')
            self.proposal_limit_amount = total - (paid + reserved)
   
    def _unset_amount_reserved(self):
        item_update = []
        for proposal_item in self.proposal_item_ids:
            amount_reserved = proposal_item.proposal_line_id.suspend_security().amount_reserved
            item_update.append([1, proposal_item.proposal_line_id.id, {
                'amount_reserved': amount_reserved - proposal_item.amount_total,
            }])
        try:
            self.proposal_id.suspend_security().write({'line_ids': item_update})
        except Exception:
            self._cr.rollback()
            raise Warning('Terjadi kesalahan saat update proposal %s.' % (self.proposal_id.suspend_security().name))

    def _update_proposal_amount_paid(self, reconciled_amount=0):
        """
        Update amount_paid dan amount_reserved di proposal setiap pembayaran (partial/full).
        Dipanggil dari tw.account.payment.action_validate setelah reconcile.
        Listing pembayaran sudah dibuat saat validate via _process_proposal.
        """
        if not reconciled_amount:
            return
        total_item_amount = sum(item.amount_total for item in self.proposal_item_ids if item.proposal_line_id)
        if not total_item_amount:
            return

        item_update = []
        for item in self.proposal_item_ids:
            if item.proposal_line_id:
                ratio = item.amount_total / total_item_amount
                paid_increment = reconciled_amount * ratio
                amount_reserved = item.proposal_line_id.suspend_security().amount_reserved
                amount_paid = item.proposal_line_id.suspend_security().amount_paid
                item_update.append([1, item.proposal_line_id.id, {
                    'amount_reserved': max(amount_reserved - paid_increment, 0),
                    'amount_paid': amount_paid + paid_increment,
                }])
        if item_update:
            self.proposal_id.suspend_security().write({'line_ids': item_update})
    