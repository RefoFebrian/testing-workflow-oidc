# 1: imports of python lib
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.exceptions import ValidationError

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib


class BankReconcile(models.Model):
    _name = "tw.bank.reconcile"
    _description = 'Bank Reconcile'

    # 7: defaults methods
    def _get_default_branch(self):
        return self.env.user.company_ids[0].id if self.env.user.company_ids else False
    
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()
    
    def _get_default_datetime(self):
        return datetime.now()

    # 8: fields
    name = fields.Char(string='Name')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('auto_reconciled', 'Auto Reconcile'),
        ('cancel', 'Cancelled')
    ], string='State', default='draft')
    date = fields.Date(string='Date', default=_get_default_date)
    effective_date_reconcile = fields.Date(string='Effective Date Reconcile')

    # Audit Trail
    confirm_uid = fields.Many2one(comodel_name='res.users', string="Confirmed by")
    confirm_date = fields.Datetime(string='Confirmed on')
    cancel_uid = fields.Many2one(comodel_name='res.users', string="Cancelled by")
    cancel_date = fields.Datetime(string="Cancelled on")

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', default=_get_default_branch)
    account_id = fields.Many2one(comodel_name='account.account', string='Account', domain="[('account_type','in',('asset_cash', 'asset_current')), ('company_ids','parent_of',company_id)]")
    move_line_ids = fields.Many2many(comodel_name='account.move.line', relation='tw_bank_reconcile_account_move_line_rel', column1='bank_reconcile_id', column2='line_id', string='Move Line', copy=False)
    bank_mutasi_ids = fields.Many2many(comodel_name='tw.bank.mutasi', relation='tw_bank_reconcile_tw_bank_mutasi_rel', column1='bank_reconcile_id', column2='mutasi_bank_id', string='Bank Mutasi', copy=False)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.account_id = False

    @api.onchange('account_id')
    def _onchange_account_id(self):
        account_id = self.account_id.id
        if self.bank_mutasi_ids:
            for bank_mutasi_id in self.bank_mutasi_ids:
                if bank_mutasi_id.account_id != account_id:
                    self.bank_mutasi_ids = False
        if self.move_line_ids:
            for move_line_id in self.move_line_ids:
                if move_line_id.account_id != account_id:
                    self.move_line_ids = False

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            branch_obj = self.env['res.company'].sudo().browse(vals['company_id'])
            name = self.env['ir.sequence'].get_sequence_code('BRM', branch_obj.code)
            vals['name'] = name
            vals['date'] = self._get_default_date()

        return super(BankReconcile, self).create(vals_list)
    
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise Warning('Transaksi yang berstatus selain Draft tidak bisa dihapus.')
        return super(BankReconcile, self).unlink()
    
    def copy(self, default=None, context=None):
        raise Warning('Transaksi ini tidak dapat diduplikat.')
        return super(BankReconcile, self).copy()

    # 13: action methods
    def action_bank_reconcile_tree(self):
        domain = []
        name = 'Bank Reconcile'
        list_view_id = self.env.ref('tw_bank_reconcile.tw_bank_reconcile_list_view').id
        form_view_id = self.env.ref('tw_bank_reconcile.tw_bank_reconcile_form_view').id
        search_view_id = self.env.ref('tw_bank_reconcile.tw_bank_reconcile_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.bank.reconcile',
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'domain': domain,
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1,
                'search_default_state_draft': 1
            },
        }
    
    def action_confirm(self):
        bank_mutasi_objs = self.sudo().bank_mutasi_ids
        move_line_objs = self.sudo().move_line_ids
        if not bank_mutasi_objs and not move_line_objs:
            raise Warning('Line belum diisi !')
        
        if not move_line_objs:
            raise Warning('Detail Journal tidak boleh kosong !')
        
        move_line_ids, eff_date1, move_line_saldo = self.sudo().check_move_line()
        mutasi_ids, eff_date2, mutasi_saldo = self.sudo().check_mutasi()
        effective_date = max(eff_date1, eff_date2)
        if effective_date == date.min:
            effective_date = self._get_default_date()

        if bank_mutasi_objs or move_line_objs:
            if abs(move_line_saldo + mutasi_saldo) <= 10:
                move_line_objs.write({
                    'reconciled_rk': True,
                    'bank_reconcile_id': self.id,
                    'effective_date_reconcile': effective_date
                })
                bank_mutasi_objs.write({
                    'state': 'Reconciled',
                    'reconciled': True,
                    'bank_reconcile_id': self.id,
                    'effective_date_reconcile': effective_date
                })

                if self.state == 'auto_reconciled':
                    self.write({
                        'confirm_date': self._get_default_datetime(),
                        'effective_date_reconcile': effective_date
                    })
                else:
                    self.write({
                        'state': 'posted',
                        'confirm_uid': self._uid,
                        'confirm_date': self._get_default_datetime(),
                        'effective_date_reconcile': effective_date
                    })
            else:
                raise Warning(f'Saldo bank mutasi dan sistem tidak sesuai.\n Saldo bank {mutasi_saldo}, saldo sistem {move_line_saldo}')

        else :
            raise Warning(f'Saldo bank mutasi dan sistem tidak sesuai.\n Saldo bank {mutasi_saldo}, saldo sistem {move_line_saldo}')
    
    def check_move_line(self):
        total_debit = 0
        total_credit = 0
        ids = []
        effective_date = date.min
        for move_line in self.move_line_ids:
            if move_line.reconciled_rk == True:
                raise Warning(f'Maaf, Account {move_line.ref} sudah di reconcile')
            if move_line.date and move_line.date > effective_date:
                effective_date = move_line.date
            ids.append(move_line.id)
            total_credit += move_line.credit
            total_debit += move_line.debit
        saldo_akhir_mutasi = total_debit - total_credit
        
        return (ids, effective_date, saldo_akhir_mutasi)
    
    def check_mutasi(self):
        total_debit = 0
        total_credit = 0
        effective_date = date.min
        ids = []
        for lines_mutasi in self.bank_mutasi_ids:
            if lines_mutasi.reconciled == True:
                raise Warning(f'Maaf, No Sistem {lines_mutasi.no_sistem} sudah di reconcile')
            if lines_mutasi.date and lines_mutasi.date > effective_date:
                effective_date = lines_mutasi.date
            ids.append(lines_mutasi.id)
            total_credit += lines_mutasi.credit
            total_debit += lines_mutasi.debit
        saldo_akhir_mutasi = total_debit - total_credit
        
        return (ids, effective_date, saldo_akhir_mutasi)

    # 14: private methods