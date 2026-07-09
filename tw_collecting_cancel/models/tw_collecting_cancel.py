# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class CollectingApproval(models.Model):
    _name = "tw.collecting.cancel"
    _inherit = ["mail.thread", "tw.approval.mixin"]
    _inherits = {'tw.cancellation': 'cancellation_id'}
    _description = 'Collecting Cancel'
    _order = 'id desc'

    @api.model
    def _get_default_date(self):
        return datetime.now()

    # 8: fields

    # 9: relation fields
    collecting_id = fields.Many2one('tw.collecting', 'Collecting')
    cancellation_id = fields.Many2one('tw.cancellation', required=True, ondelete='cascade')

    # 10: constraints & sql constraints
    _sql_constraints = [
        ('unique_collecting_id', 'unique(collecting_id)', 'Collecting pernah diinput sebelumnya !')
    ]
    
    # 11: compute/depends & on change methods
    @api.onchange('collecting_id')
    def _onchange_collecting_id(self):
        if self.collecting_id:
            self.transaction_name = self.collecting_id.name
        else:
            self.transaction_name = False   

    # 12: override methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if vals.get('collecting_id'):
                trx_id = self.env['tw.collecting'].browse(vals['collecting_id'])
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
    
    # 13: action methods
    def action_request_approval(self):
        return super().action_request_approval(value=5)
    
    def action_confirm(self):
        if self.collecting_id:           
            reversed_move = self.reverse_move()
            # Link the reversal to the original payment
            self.collecting_id.write({
                'state': 'cancel',
            })
            self.write({
                'move_id': reversed_move.id,
                'state': 'confirmed',
            })
        
        return self.cancellation_id.action_confirm()
    
    # 14: private methods 
    def reverse_move(self):
        move = self.collecting_id.collected_move_id
        if not move:
            raise Warning("No accounting entry found for this payment.")
        
        # Unreconcile Collecting Entries
        move_line_collecting = move.line_ids
        move_line_collecting.action_unreconcile_match_entries()


        # 
        account_setting = self.company_id.branch_setting_id.account_setting_id
        journal_collecting_id = account_setting.journal_collecting_id
        if not journal_collecting_id:
            raise Warning("Please set Journal Collecting Cancel in Account Setting branch %s." % self.company_id.name)
        
        # Prepare default values for the reversal
        default_values_list = [{
            'name': self.name,
            'ref': _('Reversal of: %s', move.name),
            'date': fields.Date.context_today(self),
            'invoice_date': fields.Date.context_today(self),
            'journal_id': journal_collecting_id.id,
        }]
        
        # Reverse the move
        reversed_move = move._reverse_moves(
            default_values_list=default_values_list,
            cancel=True
        )
        return reversed_move
    
    def _check_duplicate_transaction(self,name):
        return self.cancellation_id._check_duplicate_transaction(name)