# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwAdvancePaymentCancel(models.Model):
    _name = "tw.advance.payment.cancel"
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _description = 'Advance Payment Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _order = 'id desc'

    # 7: defaults methods
    @api.model
    def _get_default_date(self):
        return datetime.now()

    # 8: fields

    # 9: relation fields
    advance_payment_id = fields.Many2one('tw.advance.payment', string='Advance Payment', required=True)
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('unique_advance_payment_id', 'unique(advance_payment_id)', 'Advance Payment pernah diinput sebelumnya !')
    ]

    # 11: compute/depends & on change methods
    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.advance_payment_id = False

    @api.onchange('division')
    def _onchange_division(self):
        self.advance_payment_id = False

    @api.onchange('advance_payment_id')
    def _onchange_advance_payment_id(self):
        if self.advance_payment_id:
            self.transaction_name = self.advance_payment_id.name
            if self.state == 'draft' or not self.state:
                self.name = 'X' + self.advance_payment_id.name
        else:
            self.transaction_name = False
            self.name = False

    # 12: override methods
    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise Warning('Warning! \nCannot delete records with a state other than draft!')
            else:
                raise Warning('Warning! \nCannot delete records!')

        return super(TwAdvancePaymentCancel, self).unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('advance_payment_id'):
                avp_id = self.env['tw.advance.payment'].browse(vals['advance_payment_id'])
                vals['transaction_name'] = avp_id.name
                name = "X" + avp_id.name
                self._check_duplicate_transaction(name)
                vals['name'] = name
                vals['date'] = self._get_default_date()
        return super(TwAdvancePaymentCancel, self).create(vals_list)

    # 13: action methods
    def action_request_approval(self):
        if self.state != 'draft':
            raise UserError(f'Silakan refresh halaman ini. State sudah {self.state}')
        return super().action_request_approval(value=5)

    def action_confirm(self):
        self.ensure_one()
        if self.advance_payment_id:
            try:
                # 1. Validity Check
                self._validity_check()
                
                # 2. Reverse journal entry
                reversed_move = self._reverse_move()
                
                # 3. Update Advance Payment State
                self.advance_payment_id.sudo().write({
                    'state': 'canceled',
                })
                
                # 4. Update Cancel Record
                self.write({
                    'move_id': reversed_move.id if reversed_move else False,
                })
                
            except Exception as e:
                raise Warning(str(e))
        
        return self.cancellation_id.action_confirm()

    # 14: private methods
    def _validity_check(self):
        """
        Validity checks:
        1. Settlement Check: No non-cancelled settlement related to AVP.
        2. Payment Check: No posted/paid payments (PV) related to AVP.
        3. AVP Done Check: Cannot cancel Done advance payment.
        """
        errors = []

        # 1. Settlement Check
        settlement_obj = self.env['tw.settlement'].sudo().search([
            ('advance_payment_id', '=', self.advance_payment_id.id),
            ('state', '!=', 'cancel')
        ], limit=1)
        if settlement_obj:
            errors.append(_("- Harus cancel settlement %s dahulu!") % settlement_obj.name)

        # 2. Payment Check
        if self.advance_payment_id.payment_ids:
            paid_payments = self.advance_payment_id.payment_ids.filtered(lambda p: p.state in ('paid', 'posted'))
            if paid_payments:
                payment_names = ', '.join(paid_payments.mapped('name'))
                errors.append(_("- Gagal cancel, silakan batalkan PV (%s) terlebih dahulu!") % payment_names)

        # 3. Done Check
        if self.advance_payment_id.state == 'done':
            errors.append(_("- Advance Payment sudah Done. Status Done tidak dapat dibatalkan."))

        if errors:
            error_message = _("Tidak dapat melakukan cancel karena:\n") + "\n".join(errors)
            raise Warning(error_message)

    # 13: Action Methods
    def action_view_advance_payment(self):
        """Open the source Advance Payment"""
        self.ensure_one()
        return {
            'name': _('Advance Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'tw.advance.payment',
            'view_mode': 'form',
            'res_id': self.advance_payment_id.id,
        }
    def action_view_journal_entry(self):
        """Open the reversed journal entry (move_id)"""
        self.ensure_one()
        return {
            'name': _('Journal Items'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'list,form',
            'domain': [('move_id', '=', self.move_id.id)],
            'context': {'create': False},
        }

    def _reverse_move(self):
        """
        Create reversal journal entry for Advance Payment.
        """
        # Get journal from branch setting
        branch_setting = self.env['tw.branch.setting'].get_branch_setting(self.company_id)
        if not branch_setting.account_setting_id:
            raise Warning(_("Konfigurasi Account Setting belum dibuat untuk branch %s!") % self.company_id.name)
        
        journal_cancel = branch_setting.account_setting_id.journal_avp_cancel_id
        if not journal_cancel:
            raise Warning(_("Journal Advance Payment Cancel belum di-set di Account Setting!"))

        move = self.advance_payment_id.move_id
        if not move:
            raise Warning(_("Advance Payment tidak memiliki Journal Entry untuk di-reverse!"))

        # Create reversal
        reversal_wiz = self.env['account.move.reversal'].sudo().with_context(
            active_model='account.move',
            active_ids=move.ids
        ).create({
            'date': self.date or fields.Date.today(),
            'journal_id': journal_cancel.id,
            'reason': self.reason or _("Cancellation of %s") % self.advance_payment_id.name
        })
        
        reversal_action = reversal_wiz.sudo().reverse_moves()
        if reversal_action and reversal_action.get('res_id'):
            return self.env['account.move'].browse(reversal_action['res_id'])
        return False

    def _check_duplicate_transaction(self, name):
        """Delegate to cancellation model for duplicate check."""
        return self.cancellation_id._check_duplicate_transaction(name)
