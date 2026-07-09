# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import re

# 2: import of known third party lib
from datetime import date, timedelta, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib

class TwDisbursement(models.Model):
    _name = "tw.disbursement"
    _description = "Disbursement EDC"
    _order = "id desc"
    
    # 7: defaults methods
    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('posted','Posted'),
        ('cancel','Cancelled')
    ]

    def _get_default_date(self):
        return self.env['res.company'].suspend_security().get_default_date()
    
    def _get_default_branch(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1:
            return company_ids[0].id
        return False

    def _get_current_periods(self):
        return self.env['tw.account.period'].suspend_security()._get_current_periods()

    # 8: fields
    name = fields.Char(string="Name", compute='_compute_name',store=True)
    amount = fields.Float(string="Paid Amount", digits='Account')
    diff_amount = fields.Float(string='Difference Amount', digits='Account', compute='_compute_amount', store=True)
    date = fields.Date(string="Date", default=_get_default_date)
    description = fields.Text(string="Note")
    memo = fields.Char(string="Memo")
    state= fields.Selection(STATE_SELECTION, string='State', readonly=True,default='draft')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())

    # Audit Trail
    confirm_uid = fields.Many2one('res.users',string="Posted by")
    confirm_date = fields.Datetime('Posted on')

    # 9: relation fields
    disbursement_line_ids = fields.One2many('tw.disbursement.line','disbursement_id', string='Disbursement Lines')
    company_id = fields.Many2one('res.company', string='Branch', default=_get_default_branch)
    journal_id = fields.Many2one('account.journal', string="Payment Method", domain="[('company_id','parent_of',company_id),('type','in',['cash','bank'])]")
    edc_journal_id = fields.Many2one('account.journal', string="Journal EDC", domain="[('company_id','parent_of',company_id),('type','=','edc')]")    
    move_id = fields.Many2one('account.move', string='Account Entry')
    move_line_ids = fields.One2many('account.move.line', related='move_id.line_ids', string='Journal Items')    
    period_id = fields.Many2one('tw.account.period', string="Period", default=_get_current_periods)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            branch_obj = record.company_id
            seq_name = self.env['ir.sequence'].with_company(branch_obj).get_sequence_code('EDC', branch_obj.code)
            record.name = seq_name
    
    @api.depends('disbursement_line_ids.debit','amount')
    def _compute_amount(self):
        debit_amount = 0.00
        for line in self.disbursement_line_ids :
            debit_amount += line.debit
        
        self.diff_amount = self.amount - debit_amount 

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._validate_values(vals)
        create = super().create(vals_list)
        create._validate_amount()
        return create

    def write(self, vals):
        self._validate_values(vals)
        write = super().write(vals)
        self._validate_amount()
        return write
    
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise Warning("Perhatian !\nReimbursement EDC sudah diproses, data tidak bisa didelete !")
        return super().unlink()   

    # 13: action methods
    def action_post_disbursement(self):
        if not self.disbursement_line_ids:
            raise Warning("Perhatian !\nDetail belum diisi. Data tidak bisa di post.")
        if self.state == 'posted':
            raise Warning("Perhatian !\nData sudah di post. Data tidak bisa di post kembali.")

        self._validate_amount()
        self.action_create_move_line()
        self.write({
            'state':'posted',
            'confirm_uid': self.env.uid,
            'confirm_date': datetime.now()
        })        
        return True

    def action_create_move_line(self):
        """Create account moves and reconcile lines"""
        if not self.journal_id.default_debit_account_id:
            raise Warning("Perhatian !\nAccount belum diisi dalam journal %s!") % (self.journal_id.name)
        
        pl_account = self._get_pl_account()
        
        move_line_vals = []
        
        move_line_vals.append(self._get_move_line_vals(
            name=_('%s') % (self.journal_id.name),
            debit=self.amount,
            account_id=self.journal_id.default_debit_account_id.id
        ))

        if self.diff_amount:
            diff_name = _('Shortage Pencairan') if self.diff_amount < 0 else _('Excess Disbursement')
            move_line_vals.append(self._get_move_line_vals(
                name=diff_name,
                debit=abs(self.diff_amount) if self.diff_amount < 0 else 0.0,
                credit=self.diff_amount if self.diff_amount > 0 else 0.0,
                account_id=pl_account
            ))
        
        reconcile_by_account = {}
        for line in self.disbursement_line_ids:
            move_line_vals.append(self._get_move_line_vals(
                name=_('Disbursement %s') % (line.ref),
                credit=line.debit,
                account_id=line.account_id.id,
            ))
        
        move = self.env['account.move'].suspend_security().create({
            'name': self.name,
            'journal_id': self.journal_id.id,
            'division': self.division,
            'ref': self.name,
            'period_id': self.period_id.id,
            'line_ids': [Command.create(line) for line in move_line_vals]
        })
        move.sudo().action_post()
        disbursement_lines = self.disbursement_line_ids.mapped('move_line_id')
        disbursement_lines_account = self.disbursement_line_ids.mapped('account_id')
        move_lines = move.line_ids.filtered(lambda l: l.account_id in disbursement_lines_account and l.name.startswith('Disbursement '))
        all_lines = disbursement_lines + move_lines
        for line in all_lines:
            if not line.account_id:
                raise Warning(f"Line {line.name} has no account_id")
            if line.account_id.id not in reconcile_by_account:
                reconcile_by_account[line.account_id.id] = self.env['account.move.line']
            reconcile_by_account[line.account_id.id] |= line
        
        for account_id, lines in reconcile_by_account.items():
            if len(lines) < 2:
                raise Warning(f"Reconciliation failed for account {account_id}:\n"
                             f"  - Reason: At least 2 lines required for reconciliation\n"
                             f"  - Detail: Only found {len(lines)} line(s)")
            
            if not all(line.move_id.state == 'posted' for line in lines):
                posted_lines = len([l for l in lines if l.move_id.state == 'posted'])
                unposted_lines = len(lines) - posted_lines
                raise Warning(f"Reconciliation failed for account {account_id}:\n"
                                f"  - Reason: Some lines are not posted\n"
                                f"  - Detail: {posted_lines} line(s) posted, {unposted_lines} line(s) not posted")
            
            debit_lines = lines.filtered(lambda l: l.debit > 0)
            credit_lines = lines.filtered(lambda l: l.credit > 0)
            if not (debit_lines and credit_lines):
                raise Warning(f"Reconciliation failed for account {account_id}:\n"
                                f"  - Reason: Missing opposite signs (debit and credit)\n"
                                f"  - Detail: Found {len(debit_lines)} debit line(s)\n"
                                f"  - Detail: Found {len(credit_lines)} credit line(s)")
            
            lines.reconcile()
        self.move_id = move.id
        return True

    # 14: private methods
    def _validate_amount(self):
        #? Tidak perlu validate kesamaan amount, karena bisa jadi ada potongan biaya admin atau tambahan bunga
        # amount_line = sum(self.disbursement_line_ids.mapped('debit'))
        # if amount_line != self.amount:
        #     raise Warning("Perhatian !\nPaid Amount (%s) tidak sesuai dengan total disbursement line (%s)!" % (self.currency_format(self.amount), self.currency_format(amount_line)))
        return True

    def _validate_values(self, vals):
        """Validate common fields in create and write operations"""
        if vals.get('amount') and vals['amount'] <= 0:
            raise Warning("Perhatian !\nPaid Amount tidak boleh kurang dari Rp.1 ")

    def _get_pl_account(self):
        """Get or raise PL account from branch config"""
        branch_config = self.company_id.branch_setting_id
        if not branch_config:
            raise Warning(f"Branch Setting {self.company_id.name} not found!")
        
        account_config = branch_config.account_setting_id
        if not account_config:
            raise Warning(f"Account Setting {self.company_id.name} not found!")
        
        if not account_config.account_disbursement_pl_id:
            raise Warning(f"Account Disbursement PL in branch {self.company_id.name} not found! Please set it on account setting")
        
        return account_config.account_disbursement_pl_id.id

    def _get_move_line_vals(self, name, debit=0.0, credit=0.0, account_id=None):
        """Helper to create move line values"""
        amount = debit if debit > 0 else -credit
        return {
            'name': name,
            'ref': self.name,
            'account_id': account_id,
            'journal_id': self.journal_id.id,
            'period_id': self.period_id.id,
            'date': self.date,
            'currency_id': self.company_id.currency_id.id,
            'amount_currency': amount,
            'debit': debit,
            'credit': credit,
            'partner_id': self.edc_journal_id.partner_id.id,
            'company_id': self.company_id.id,
            'division': self.division,
        }
    
