# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
from odoo.fields import Command

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwPaymentCancel(models.Model):
    _name = "tw.payment.cancel"
    # _inherit = ['mail.thread']
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _description = 'Payment Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _order = 'id desc'  

    # 7: defaults methods
    @api.model
    def _get_default_date(self):
        return datetime.now()
    
    def _get_state_value(self):
        # Mengambil value yang sesuai dengan key di state
        selection = self._fields.get('state') and self._fields['state'].selection
        return dict(selection).get(self.state, self.state) if selection else self.state

    # 8: fields

    # 9: relation fields
    payment_type = fields.Selection([
        ('account_payment', 'Payment/HL'),
        ('other_receivable', 'Other Receivable'),
        ('payment_request', 'Payment Request')
    ], string='Payment Type', default='account_payment')
    account_payment_id = fields.Many2one('tw.account.payment', 'Payment')
    other_receivable_id = fields.Many2one('tw.other.receivable', 'Other Receivable')
    payment_request_id = fields.Many2one('tw.payment.request', 'Payment Request')
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    # 10: constraints & sql constraints

    _sql_constraints = [
        ('unique_account_payment_id', 'unique(account_payment_id)', 'Account Payment pernah diinput sebelumnya !')
    ]
    
    # 11: compute/depends & on change methods
    @api.onchange('payment_type', 'division')
    def _onchange_payment_type(self):
        self.account_payment_id = False
        self.other_receivable_id = False
        self.payment_request_id = False
        self.transaction_name = False

    @api.onchange('account_payment_id')
    def _onchange_account_payment_id(self):
        if self.account_payment_id:
            self.transaction_name = self.account_payment_id.name
        else:
            self.transaction_name = False   

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            trx_id = False
            if vals.get('payment_type') == 'account_payment':
                if vals.get('account_payment_id'):
                    trx_id = self.env['tw.account.payment'].browse(vals['account_payment_id'])
            elif vals.get('payment_type') == 'other_receivable':
                if vals.get('other_receivable_id'):
                    trx_id = self.env['tw.other.receivable'].browse(vals['other_receivable_id'])
            elif vals.get('payment_type') == 'payment_request':
                if vals.get('payment_request_id'):
                    trx_id = self.env['tw.payment.request'].browse(vals['payment_request_id'])
            if not trx_id:
                raise Warning('Transaction Not Found')
                
            vals['transaction_name'] = trx_id.name
            name = "X" + trx_id.name
            self._check_duplicate_transaction(name)
            vals['name'] = "X" + trx_id.name
            vals['date'] = self._get_default_date()
        return super().create(vals_list)
    
    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise Warning('Warning! \nCannot delete records with a state other than draft!')
            else:
                raise Warning('Warning! \nCannot delete records!')

        return super().unlink()

    def action_request_approval(self):
        if self.state != 'draft':
            raise Warning(f'Silakan refresh halaman ini, karena state telah {self._get_state_value()}')
        self.validity_check()
        return super().action_request_approval(value=5)

    def action_confirm(self):
        self.validity_check()
        if self.state != 'approved':
            raise Warning(f'Silakan refresh halaman ini, karena state telah {self._get_state_value()}')

        if self.account_payment_id:
            move_id = self.account_payment_id.move_id
            transaction_id = self.account_payment_id
        elif self.payment_request_id:
            # Pembatalan payment proposal sudah di handle di tw_payment_request_proposal
            move_id = self.payment_request_id.move_id
            transaction_id = self.payment_request_id
        elif self.other_receivable_id:
            move_id = self.other_receivable_id.move_id
            transaction_id = self.other_receivable_id
        else:
            raise Warning("Gagal Confirm, silahkan periksa kembali data anda.")

        # Unreconcile semua move lines payment
        # agar payment_state invoice kembali ke "not_paid"
        payment_move_lines = transaction_id.sudo().move_id.line_ids.filtered(
            lambda l: l.matched_credit_ids or l.matched_debit_ids
        )
        if payment_move_lines:
            payment_move_lines.sudo().remove_move_reconcile()

        reversed_move = self.sudo().with_company(self.company_id).reverse_move()
        # Link the reversal to the original payment
        transaction_id.write({
            'state': 'canceled',
        })

        if self.account_payment_id:
            # Hanya proses untuk Hutang Lain (type = receive_payment)
            if self.account_payment_id.type == 'receive_payment':
                # Cari DSO yang menggunakan payment ini sebagai DP
                dso_payment_lines = self._get_dso_payment_lines()
                # Cancel DP invoice dan AL move yang terkait (hanya untuk Hutang Lain)
                if dso_payment_lines:
                    self.sudo()._cancel_dso_dp_and_allocation(dso_payment_lines)
                    self.sudo()._clear_dso_payment_allocation(dso_payment_lines)
            else:
                # Revert DSO state to 'sale' if applicable
                move_line = self.account_payment_id.line_ids.mapped('move_line_id')
                invoice_refs = move_line.mapped('ref')
                if invoice_refs:
                    dso_ids = self.env['tw.dealer.sale.order'].sudo().search([('client_order_ref', 'in', invoice_refs)])
                    for dso in dso_ids:
                        dso.sudo()._check_dso_revert_sale()
        
        self.write({
            'move_id': reversed_move.id,
            'state': 'confirmed',
        })

        return self.cancellation_id.sudo().action_confirm()
    
    def button_open_journal_entry(self):
        ''' Redirect the user to this payment journal.
        :return:    An action on account.move.
        '''
        self.ensure_one()
        return {
            'name': _("Journal Entry"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': self.move_id.id,
        }
        
    # 14: private methods 
    def reverse_move(self):
        if self.payment_type == 'account_payment':
            trx_id = self.account_payment_id
        elif self.payment_type == 'other_receivable':
            trx_id = self.other_receivable_id
        elif self.payment_type == 'payment_request':
            trx_id = self.payment_request_id
        
        payment_move = trx_id.move_id
        if not payment_move:
            raise Warning("No accounting entry found for this payment.")
        
        account_setting = self.company_id.branch_setting_id.account_setting_id
        journal_payment_cancel_id = account_setting.journal_payment_cancel_id
        if not journal_payment_cancel_id:
            raise Warning("Please set Journal Payment Cancel in Account Setting branch %s." % self.company_id.name)
        
        # Prepare default values for the reversal
        default_values_list = [{
            'name': self.name,
            'ref': _('Reversal of: %s', payment_move.name),
            'date': fields.Date.context_today(self),
            'invoice_date': fields.Date.context_today(self),
            'journal_id': journal_payment_cancel_id.id,
        }]
        
        # Reverse the move
        reversed_move = payment_move.with_context(skip_date_sequence_check=True)._reverse_moves(
            default_values_list=default_values_list,
            cancel=True
        )
        return reversed_move

    def check_reconcile(self):   
        message = ""
        checked_transaction = set()
        move_id = False
        if self.payment_type == 'other_receivable':
            move_id = self.other_receivable_id.move_id
        elif self.payment_type == 'payment_request':
            move_id = self.payment_request_id.move_id
        
        if move_id:
            for line_id in move_id.line_ids:
                if line_id.reconciled or line_id.full_reconcile_id:
                    message += line_id.name + ", "
                    checked_transaction.add(line_id.name)
                    break
        return message.rstrip(", ")
    
    def validity_check(self):
        transaction_warning = ""
        transaction_number = self.sudo().check_reconcile()
        
        if transaction_number:
            transaction_warning = "Transaksi " + transaction_number + " sudah dibayar, silahkan lakukan pembatalan Customer/Supplier Payment terlebih dahulu!"
        if transaction_warning:
            raise Warning(transaction_warning)
    
    def _check_duplicate_transaction(self,name):
        return self.cancellation_id._check_duplicate_transaction(name)

    def _get_dso_payment_lines(self):
        """
        Cari semua tw.dealer.sale.order.payment yang menggunakan
        account.move.line dari payment yang di-cancel.

        :return: recordset of tw.dealer.sale.order.payment
        """
        self.ensure_one()
        if not self.account_payment_id or not self.account_payment_id.move_id:
            return self.env['tw.dealer.sale.order.payment']

        # Cari move lines dari payment yang di-cancel
        payment_move_lines = self.account_payment_id.move_id.line_ids

        # Cari DSO payment lines yang menggunakan move lines ini
        dso_payment_lines = self.env['tw.dealer.sale.order.payment'].search([
            ('payment_entry_id', 'in', payment_move_lines.ids)
        ])

        return dso_payment_lines

    def _cancel_dso_dp_and_allocation(self, dso_payment_lines):
        """
        Cancel DP invoice dan AL (allocation) move yang terkait dengan
        DSO yang menggunakan HL payment yang di-cancel.

        Urutan:
        1. Unreconcile & cancel AL move (allocation entry)
        2. Unreconcile & cancel DP invoice

        :param dso_payment_lines: recordset of tw.dealer.sale.order.payment
        """
        dso_orders = dso_payment_lines.mapped('order_id')

        for dso in dso_orders:
            # 1. Cari AL move (entry type, posted, ref = DSO name)
            al_moves = dso.invoice_ids.filtered(
                lambda inv: inv.move_type == 'entry' and inv.state == 'posted'
            )

            # 2. Cari DP invoice (name contains 'DP/', posted)
            dp_invoices = dso.invoice_ids.filtered(
                lambda inv: inv.name and 'DP/' in inv.name
                and inv.state == 'posted'
            )

            # 3. Unreconcile & cancel AL move
            for al_move in al_moves:
                reconciled_lines = al_move.line_ids.filtered(
                    lambda l: l.matched_credit_ids or l.matched_debit_ids
                )
                if reconciled_lines:
                    reconciled_lines.remove_move_reconcile()
                al_move.button_draft()
                al_move.button_cancel()

            # 4. Unreconcile & cancel DP invoice
            for dp_inv in dp_invoices:
                reconciled_lines = dp_inv.line_ids.filtered(
                    lambda l: l.matched_credit_ids or l.matched_debit_ids
                )
                if reconciled_lines:
                    reconciled_lines.remove_move_reconcile()
                dp_inv.button_draft()
                dp_inv.button_cancel()

            # 5. Cari SL invoice (name contains 'SL/', posted)
            sl_invoices = dso.invoice_ids.filtered(
                lambda inv: inv.name and 'SL/' in inv.name
                and inv.state == 'posted'
            )

            # 6. Unreconcile SL invoice (without cancelling)
            for sl_inv in sl_invoices:
                reconciled_lines = sl_inv.line_ids.filtered(
                    lambda l: l.matched_credit_ids or l.matched_debit_ids
                )
                if reconciled_lines:
                    reconciled_lines.remove_move_reconcile()

    def _clear_dso_payment_allocation(self, dso_payment_lines):
        """
        Clear payment allocation di DSO yang terpengaruh oleh cancel payment (Hutang Lain).
        Juga handle unreconcile invoice yang terkait.
        TIDAK unlink payment lines untuk menjaga history.

        :param dso_payment_lines: recordset of tw.dealer.sale.order.payment
        """
        dso_orders = dso_payment_lines.mapped('order_id')

        for dso in dso_orders:
            # Dapatkan payment lines yang harus di-clear
            lines_to_clear = dso.payment_ids.filtered(
                lambda x: x.payment_entry_id in self.account_payment_id.move_id.line_ids
            )

            # Unreconcile invoice yang terkait sebelum clear payment
            for payment_line in lines_to_clear:
                move_line = payment_line.payment_entry_id
                if move_line and (move_line.matched_credit_ids or move_line.matched_debit_ids):
                    move_line.remove_move_reconcile()

            # Set allocation amount ke 0 (TIDAK unlink untuk menjaga history)
            if lines_to_clear:
                lines_to_clear.write({
                    'amount_allocation': 0.0,
                    'amount_original': 0.0,
                    'amount_balance': 0.0,
                })

            # Note: TIDAK update state DSO karena ini akan di-handle di DSO cancel workflow
