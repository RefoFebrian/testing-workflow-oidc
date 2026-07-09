# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwDisbursementCancel(models.Model):
    _name = "tw.disbursement.cancel"
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _description = 'Disbursement Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _order = 'id desc'

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now()

    # 8: fields

    # 9: relation fields
    disbursement_id = fields.Many2one('tw.disbursement', 'Disbursement')
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('unique_disbursement_id', 'unique(disbursement_id)', 'Disbursement pernah diinput sebelumnya !')
    ]
    
    # 11: compute/depends & on change methods
    @api.onchange('disbursement_id')
    def _onchange_disbursement_id(self):
        if self.disbursement_id:
            self.transaction_name = self.disbursement_id.name
        else:
            self.transaction_name = False

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('disbursement_id'):
                disbursement_id = self.env['tw.disbursement'].browse(vals['disbursement_id'])
                vals['transaction_name'] = disbursement_id.name
                name = "X" + disbursement_id.name
                self._check_duplicate_transaction(name)
                vals['name'] = "X" + disbursement_id.name
                vals['date'] = self._get_default_date()
        return super(TwDisbursementCancel, self).create(vals_list)

    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise Warning('Warning! \nCannot delete records with a state other than draft!')
            else:
                raise Warning('Warning! \nCannot delete records!')

        return super(TwDisbursementCancel, self).unlink()

    # 13: action methods

    # 14: private methods
    def action_request_approval(self):
        return super().action_request_approval(value=5)

    def validity_check(self):
        if self.disbursement_id.id :
            if self.disbursement_id.state != 'posted' :
                raise Warning("Attention !\nDisbursement can't be cancelled, status Disbursement is not Posted !")
            elif self.disbursement_id.state == 'cancel' :
                raise Warning("Attention !\nDisbursement is already cancelled!")

    def action_confirm(self):
        if self.state != 'approved' :
            raise Warning("Attention !\nDisbursement can't be cancelled, status Disbursement is not Approved!")

        self.validity_check()
        reversed_move = self.reverse_move()
        self.disbursement_id.suspend_security().write({'state': 'cancel'})
        self.write({
            'state':'confirmed',
            'move_id': reversed_move.id,
            'confirm_uid':self._uid, 
            'confirm_date':datetime.now(),
        })
        return True

    def reverse_move(self):
        move = self.disbursement_id.move_id
        if not move:
            raise Warning("No accounting entry found for this payment.")
        
        # Unreconcile Disbursement Entries
        move_line_disbursement = move.line_ids
        move_line_disbursement.action_unreconcile_match_entries()

        account_setting = self.company_id.branch_setting_id.account_setting_id
        journal_disbursement_id = account_setting.journal_disbursement_cancel_id
        if not journal_disbursement_id:
            raise Warning("Please set Journal Disbursement Cancel in Account Setting branch %s." % self.company_id.name)
        
        # Prepare default values for the reversal
        default_values_list = [{
            'name': self.name,
            'ref': f"Reversal of: {move.name}",
            'date': fields.Date.context_today(self),
            'invoice_date': fields.Date.context_today(self),
            'journal_id': journal_disbursement_id.id,
        }]
        
        # Reverse the move
        reversed_move = move._reverse_moves(
            default_values_list=default_values_list,
            cancel=True
        )
        return reversed_move

    def _check_duplicate_transaction(self,name):
        return self.cancellation_id._check_duplicate_transaction(name)

