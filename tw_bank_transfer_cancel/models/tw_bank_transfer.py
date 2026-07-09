# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwBankTransferCancel(models.Model):
    _name = "tw.bank.transfer.cancel"
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _description = 'Bank Transfer Cancel'
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _order = 'id desc'

    # 7: defaults methods
    @api.model
    def _get_default_date(self):
        return datetime.now()

    # 8: fields

    # 9: relation fields
    bank_transfer_id = fields.Many2one('tw.bank.transfer', 'Bank Transfer')
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    @api.onchange('bank_transfer_id')
    def _onchange_bank_transfer_id(self):
        if self.bank_transfer_id:
            self.transaction_name = self.bank_transfer_id.name
        else:
            self.transaction_name = False

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.bank_transfer_id = False
        
    # 12: override methods
    def unlink(self):
        for record in self:
            if record.state and record.state != 'draft':
                raise Warning('Warning! \nCannot delete records with a state other than draft!')
            else:
                raise Warning('Warning! \nCannot delete records!')

        return super(TwBankTransferCancel, self).unlink()

    # 13: action methods

    # 14: private methods

    _sql_constraints = [
        ('unique_bank_transfer_id', 'unique(bank_transfer_id)', 'Bank Transfer pernah diinput sebelumnya !')
    ]
    
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('bank_transfer_id'):
                bank_transfer_id = self.env['tw.bank.transfer'].browse(vals['bank_transfer_id'])
                vals['transaction_name'] = bank_transfer_id.name
                name = "X" + bank_transfer_id.name
                self._check_duplicate_transaction(name)
                vals['name'] = "X" + bank_transfer_id.name
                vals['date'] = self._get_default_date()
        return super(TwBankTransferCancel, self).create(vals_list)
    
    def action_request_approval(self):
        return super().action_request_approval(value=5)
    
    def validity_check(self):
       if self.bank_transfer_id.state=='cancel':
        raise Warning('Bank Transfer %s sudah dibatalkan !' % (self.bank_transfer_id.name))

    def reverse_move(self):
        move = self.bank_transfer_id.move_id
        if not move:
            raise Warning('No accounting entry found for this payment.')
        
        # Unreconcile Collecting Entries
        move_line_bank_transfer = move.line_ids
        move_line_bank_transfer.action_unreconcile_match_entries()
        branch_config_obj = self.company_id.branch_setting_id
        journal_bank_transfer_cancel_id = branch_config_obj.account_setting_id.journal_bank_transfer_cancel_id.id
        if not journal_bank_transfer_cancel_id:
            raise Warning("Attention! The Bank Transfer Cancel Journal hasn't been Created. Please Set it up First.")
        
        # Prepare default values for the reversal
        default_values_list = [{
            'name': self.name,
            'ref': _('Reversal of: %s', move.name),
            'date': fields.Date.context_today(self),
            'invoice_date': fields.Date.context_today(self),
            'journal_id': journal_bank_transfer_cancel_id
        }]
        
        # Reverse the move
        reversed_move = move._reverse_moves(
            default_values_list=default_values_list,
            cancel=True
        )
        return reversed_move
        
    def action_confirm(self):
        bank_transfer_obj = self.sudo().bank_transfer_id
        if bank_transfer_obj:
            try:       
                self.sudo().validity_check()
                self.sudo().reverse_move()
            except Exception as e:
                raise Warning(str(e))
            
            bank_transfer_obj.action_cancel()
         
            self.move_id.sudo().action_post()
        return self.cancellation_id.action_confirm()
        

    def _check_duplicate_transaction(self,name):
        return self.cancellation_id._check_duplicate_transaction(name)
