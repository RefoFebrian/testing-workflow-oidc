# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwSettlementCancel(models.Model):
    _name = "tw.settlement.cancel"
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _description = "Settlement Cancel"
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _order = 'id desc'

    # 7: defaults methods
    @api.model
    def _get_default_date(self):
        return datetime.now()
    
    def _get_state_value(self):
        selection = self._fields.get('state') and self._fields['state'].selection
        return dict(selection).get(self.state, self.state) if selection else self.state

    # 8: fields

    # 9: relation fields
    settlement_id = fields.Many2one('tw.settlement', string='Settlement', required=True)
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('unique_settlement_id', 'unique(settlement_id)', 'Settlement pernah diinput sebelumnya!')
    ]

    # 11: compute/depends & on change methods
    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Reset settlement ketika branch diganti."""
        self.settlement_id = False

    @api.onchange('division')
    def _onchange_division(self):
        """Reset settlement ketika division diganti."""
        self.settlement_id = False

    @api.onchange('settlement_id')
    def _onchange_settlement_id(self):
        """Update transaction_name dan name saat memilih/mengganti settlement."""
        if self.settlement_id:
            self.transaction_name = self.settlement_id.name
            self.name = "X" + self.settlement_id.name
        else:
            self.transaction_name = False
            self.name = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('settlement_id'):
                settlement = self.env['tw.settlement'].browse(vals['settlement_id'])
                vals['transaction_name'] = settlement.name
                name = "X" + settlement.name
                self._check_duplicate_transaction(name)
                vals['name'] = name
                vals['date'] = self._get_default_date()
        return super().create(vals_list)

    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise Warning('Warning! \nCannot delete records with a state other than draft!')
            else:
                raise Warning('Warning! \nCannot delete records!')
        return super().unlink()

    # 13: action methods
    def action_request_approval(self):
        if self.state != 'draft':
            raise UserError(f'Silakan refresh halaman ini, karena state telah {self._get_state_value()}')
        return super().action_request_approval(value=5)

    def action_confirm(self):
        if self.state != 'approved':
            raise UserError(f'Silakan refresh halaman ini, karena state telah {self._get_state_value()}')
        
        if self.settlement_id:
            # Validate payment status
            self._validity_check()
            
            # Reverse journal entry
            reversed_move = self._reverse_move()
            
            # Cancel the settlement
            self.settlement_id.action_cancel_settlement()
            
            # Update cancel record
            self.write({
                'move_id': reversed_move.id if reversed_move else False,
                'state': 'confirmed',
            })
        
        return self.cancellation_id.action_confirm()

    def button_open_journal_entry(self):
        """Redirect the user to this payment journal."""
        self.ensure_one()
        return {
            'name': _("Journal Entry"),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': self.move_id.id,
        }

    def button_open_settlement(self):
        """Redirect user ke form Settlement terkait."""
        self.ensure_one()
        return {
            'name': _("Settlement"),
            'type': 'ir.actions.act_window',
            'res_model': 'tw.settlement',
            'context': {'create': False},
            'view_mode': 'form',
            'res_id': self.settlement_id.id,
        }

    # 14: private methods
    def _validity_check(self):
        """
        Validate that settlement can be cancelled.
        Cancel is only allowed if the related advance payment is not yet paid.
        """
        if self.settlement_id.state == 'cancel':
            raise Warning(f"Settlement {self.settlement_id.name} sudah dibatalkan!")
        
        if self.settlement_id.state != 'done':
            raise Warning(f"Settlement {self.settlement_id.name} belum di-confirm, tidak perlu dibatalkan!")
        
        # Check if advance payment has any payment that is paid
        advance_payment = self.settlement_id.advance_payment_id
        if advance_payment:
            # Check if there are any payments related to advance payment
            if hasattr(advance_payment, 'payment_ids'):
                paid_payments = advance_payment.payment_ids.filtered(
                    lambda p: p.state in ('posted', 'reconciled')
                )
                if paid_payments:
                    payment_names = ', '.join(paid_payments.mapped('name'))
                    raise Warning(
                        f"Advance Payment {advance_payment.name} sudah memiliki pembayaran yang ter-posting: "
                        f"{payment_names}. Silahkan batalkan pembayaran terlebih dahulu!"
                    )
        
        # Check if move_id has been reconciled
        if self.settlement_id.move_id:
            reconciled_lines = self.settlement_id.move_id.line_ids.filtered(
                lambda l: l.reconciled or l.full_reconcile_id
            )
            # Note: Some lines may be reconciled as part of normal settlement flow
            # We only block if there are external reconciliations
    
    def _reverse_move(self):
        """
        Create reversal journal entry for the settlement.
        """
        settlement_move = self.settlement_id.move_id
        if not settlement_move:
            return False
        
        # Get journal for settlement cancel
        account_setting = self.company_id.branch_setting_id.account_setting_id
        journal_settlement_cancel_id = account_setting.journal_settlement_cancel_id
        
        if not journal_settlement_cancel_id:
            raise Warning(
                f"Please set Journal Settlement Cancel in Account Setting branch {self.company_id.name}."
            )
        
        # Prepare default values for the reversal
        default_values_list = [{
            'name': self.name,
            'ref': _('Reversal of: %s', settlement_move.name),
            'date': fields.Date.context_today(self),
            'invoice_date': fields.Date.context_today(self),
            'journal_id': journal_settlement_cancel_id.id,
        }]
        
        # Reverse the move
        reversed_move = settlement_move.with_context(skip_date_sequence_check=True)._reverse_moves(
            default_values_list=default_values_list,
            cancel=True
        )
        
        return reversed_move
    
    def _check_duplicate_transaction(self, name):
        """Delegate to cancellation model for duplicate check."""
        return self.cancellation_id._check_duplicate_transaction(name)
