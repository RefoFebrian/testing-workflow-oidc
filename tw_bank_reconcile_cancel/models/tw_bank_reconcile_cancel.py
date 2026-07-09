# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class BankReconcileCancel(models.Model):
    _name = "tw.bank.reconcile.cancel"
    _inherit = ['mail.thread', 'tw.approval.mixin']
    _description = 'Bank Reconcile Cancel'

    # 7: defaults methods
    def _get_default_branch(self):
        return self.env.user.company_ids[0].id if self.env.user.company_ids else False
    
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()

    # 8: fields
    name = fields.Char(string='Name')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_for_approval', 'Waiting For Approval'),
        ('approved', 'Approved'),
        ('confirmed', 'Confirmed')
    ], string='State', default='draft')
    date = fields.Date(string='Date', default=_get_default_date)
    reason = fields.Text(string='Reason')

    # Audit Trail
    approve_uid = fields.Many2one(comodel_name='res.users', string='Approved by')
    approve_date = fields.Datetime(string='Approved on')
    confirm_uid = fields.Many2one(comodel_name='res.users', string='Confirmed by')
    confirm_date = fields.Datetime(string='Confirmed on')

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', default=_get_default_branch)
    bank_reconcile_id = fields.Many2one(comodel_name='tw.bank.reconcile', string='Bank Reconcile')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('bank_reconcile_id'):
                bank_reconcile_obj = self.env['tw.bank.reconcile'].sudo().browse(vals['bank_reconcile_id'])
                vals['name'] = f'X{bank_reconcile_obj.name}'

        return super(BankReconcileCancel, self).create(vals_list)

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise Warning(f'Bank Reconcile Cancel tidak bisa dicancel, state saat ini {record.state} !')
        return super(BankReconcileCancel, self).unlink()

    # 13: action methods
    def action_bank_reconcile_cancel_tree(self):
        domain = []
        name = 'Bank Reconcile Cancel'
        list_view_id = self.env.ref('tw_bank_reconcile_cancel.tw_bank_reconcile_cancel_list_view').id
        form_view_id = self.env.ref('tw_bank_reconcile_cancel.tw_bank_reconcile_cancel_form_view').id
        search_view_id = self.env.ref('tw_bank_reconcile_cancel.tw_bank_reconcile_cancel_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.bank.reconcile.cancel',
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'domain': domain,
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def action_request_approval(self):
        self._check_bank_mutation()
        return super().action_request_approval(value=5)

    def action_approval(self):
        self._check_bank_mutation()
        return super().action_approval()

    def action_confirm(self):
        self.sudo()._check_bank_mutation()
        self.sudo()._process_cancel_bank_mutation()
        self.sudo()._process_cancel_move_lines()
        self.sudo()._process_cancel_bank_reconcile_trx()

        self.write({
            'state': 'confirmed',
            'confirm_uid': self._uid,
            'confirm_date': datetime.now()
        })

    # 14: private methods
    def _check_bank_mutation(self):
        if self.bank_reconcile_id.state not in ('posted', 'auto_reconciled'):
            raise Warning(f'Bank Reconcile tidak bisa dicancel, state saat ini {self.bank_reconcile_id.state} !')
        
    def _process_cancel_bank_mutation(self):
        for bank_mutasi_obj in self.bank_reconcile_id.bank_mutasi_ids:
            bank_mutasi_obj.write({
                'state': 'Outstanding',
                'reconciled': False,
                'bank_reconcile_id': False,
                'effective_date_reconcile': False
            })
    
    def _process_cancel_move_lines(self):
        for move_line_obj in self.bank_reconcile_id.move_line_ids:
            move_line_obj.write({
                'reconciled_rk': False,
                'bank_reconcile_id': False,
                'effective_date_reconcile': False
            })
    
    def _process_cancel_bank_reconcile_trx(self):
        self.bank_reconcile_id.write({
            'cancel_uid': self._uid,
            'cancel_date': datetime.now(),
            'state': 'cancel'
        })