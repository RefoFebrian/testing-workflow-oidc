# Copyright (C) 2024 Tunas Group
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
import time
from lxml import etree

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError as Warning, ValidationError

# 4: imports from odoo modules
from odoo.tools import float_compare

# 5: local imports

# 6: Import of unknown third party lib
class TwJournalMemorial(models.Model):
    _name = "tw.journal.memorial"
    _description = "Journal Memorial"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    
    # 7: defaults methods
    def _get_default_branch(self):
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return company_ids[0].id
        return False  
        
    def _get_default_period(self):
        period_obj = self.env['tw.account.period']._get_current_periods()
        return period_obj.id
        
    def _get_default_date(self):
        return date.today()

    def _get_default_journal_id(self):
        if self.company_id:
            branch_setting_obj = self.env['tw.branch.setting'].get_branch_setting(self.company_id)
            if not branch_setting_obj.account_setting_id:
                raise Warning(
                    "Account setting is not set for branch %s.\n"
                    "- Go to the Master Branch Setting.\n"
                    "- Set the 'Account Setting' to proceed.\n"
                    "This configuration is required to create accounting entries." 
                    % self.company_id.name
                )
            if not branch_setting_obj.account_setting_id.journal_memorial_journal_id:
                raise Warning(
                        "Journal Memorial is not set for branch %s.\n"
                        "- Go to the Account Setting.\n"
                        "- Set the 'Journal Memorial'.\n"
                        "This configuration is required to create Journal Memorial." 
                        % self.company_id.name
                    )
            return branch_setting_obj.account_setting_id.journal_memorial_journal_id.id
        else: 
            return False

    # 8: fields
    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('cancel', 'Cancelled')
    ]

    # 8: fields
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    date = fields.Date(string='Date', required=True, default=_get_default_date, tracking=True, readonly=True)
    period_date = fields.Date(string='Period Date', compute='_compute_prev_period', store=True)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    state = fields.Selection(selection=STATE_SELECTION, string='State', default='draft', tracking=True)
    description = fields.Char(string='Description')
    code = fields.Selection(selection=[(' ', ' '), ('cancel', 'Cancel')], string='Code', default=' ')
    note = fields.Text('Notes')

    is_prev_period = fields.Boolean(string='Prev Periode',compute='_compute_prev_period', store=True)
    is_auto_reverse = fields.Boolean(string='Auto Reverse?')

    # Computed Fields
    total_debit = fields.Monetary(string='Total Debit', compute='_compute_totals', store=True, tracking=True)
    total_credit = fields.Monetary(string='Total Credit', compute='_compute_totals', store=True, tracking=True)
    
    # Audit Trail
    confirm_uid = fields.Many2one('res.users', string='Confirmed by', copy=False)
    confirm_date = fields.Datetime(string='Confirmed on', copy=False)
    

    # 9: Relational Fields
    company_id = fields.Many2one('res.company', string='Branch', required=True, tracking=True, default=_get_default_branch)
    period_id = fields.Many2one('tw.account.period', string='Period', default=_get_default_period)
    current_period_id = fields.Many2one('tw.account.period', string='Current Period', default=_get_default_period)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=True)
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, domain="[('company_id', 'parent_of', company_id), ('type', 'in', ['general', 'sale', 'purchase'])]", default=lambda self: self._get_default_journal_id())
    cancel_refered_id = fields.Many2one('tw.journal.memorial', string='Cancel Reference')
    
    line_ids = fields.One2many('tw.journal.memorial.line', 'journal_memorial_id', string='Journals', copy=True)
    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True, copy=False, tracking=True)
    move_line_ids = fields.One2many('account.move.line', related='move_id.line_ids', string='Journal Items', readonly=True)
    auto_reverse_move_id = fields.Many2one('account.move', string='Auto Reverse Entry', readonly=True, copy=False)
    auto_reverse_move_line_ids = fields.One2many('account.move.line', related='auto_reverse_move_id.line_ids', string='Auto Reverse Journal Items', readonly=True)
    
    # 10: constraints & sql constraints
    @api.constrains('line_ids')
    def _check_balanced(self):
        for record in self:
            if float_compare(
                record.total_debit,
                record.total_credit,
                precision_rounding=record.currency_id.rounding
            ) != 0:
                raise ValidationError(_(
                    'Total Debit and Credit must be equal!\n'
                    'Total Debit: %s\n'
                    'Total Credit: %s' %
                    (record.total_debit, record.total_credit)
                ))
    
    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            if record.id and record.company_id and record.state:
                if not record.name or record.state == 'draft':
                    seq_name = self.env['ir.sequence'].with_company(record.company_id).get_sequence_code_with_date('JM', record.company_id.code, record.period_date)
                    record.name = seq_name

    @api.depends('period_id')
    def _compute_prev_period(self):
        for record in self:
            if record.period_id and record.date:
                record.period_date = record.date if record.period_id.id == record.current_period_id.id else record.period_id.date_to
                if record.period_id.date_to < record.date:
                    record.is_prev_period = True
                    record.is_auto_reverse = False
                else:
                    record.is_prev_period = False
            else:
                record.period_date = False
                record.is_prev_period = False
                record.is_auto_reverse = False


    @api.depends('line_ids.amount', 'line_ids.type')
    def _compute_totals(self):
        for record in self:
            record.total_debit = sum(line.amount for line in record.line_ids if line.type == 'debit')
            record.total_credit = sum(line.amount for line in record.line_ids if line.type == 'credit')
    
    
    @api.onchange('company_id')
    def _onchange_company_journal_id(self):
        if self.company_id:
            self.journal_id = self._get_default_journal_id()
        else:
            self.journal_id = False
    
    # 12: Overides Method
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._check_balance()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'line_ids' in vals:
            self._check_balance()
        return res

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise Warning(_('You can only delete draft journal memorials!'))
            if record.move_id:
                raise Warning(_('You cannot delete a journal memorial with posted entries!'))
        return super().unlink()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        
        if view_type == 'form':
            period_domain = []
            Period = self.env['account.period']
            date = self._get_default_date()
            
            # Get current period
            current_period = Period.search([
                ('date_start', '<=', date),
                ('date_stop', '>=', date)
            ], limit=1)
            
            if current_period:
                period_domain.append(('id', '=', current_period.id))
                # Get previous draft periods
                prev_periods = Period.search([
                    ('date_start', '<', date),
                    ('id', '!=', current_period.id),
                    ('state', '=', 'draft')
                ])
                if prev_periods:
                    period_domain = ['|'] + period_domain + [('id', 'in', prev_periods.ids)]
            
            doc = etree.XML(res['arch'])
            nodes_period = doc.xpath("//field[@name='period_id']")
            for node in nodes_period:
                node.set('domain', str(period_domain) if period_domain else '[]')
            
            res['arch'] = etree.tostring(doc)
        return res
    

    # 13: action methods
    def action_draft(self):
        self.write({'state': 'draft'})

    def action_confirm(self):
        self.ensure_one()

        self._validate_journal_memorial()

        if self.state == 'confirm':
            raise Warning(_('Record already confirmed, please refresh!'))
        
        # Create account move
        move, reversed_move = self._create_account_move()

        # Handle asset depreciation
        self._recompute_depreciation()
        
        # Update the journal memorial
        self.write({
            'state': 'confirm',
            'confirm_uid': self.env.user.id,
            'confirm_date': datetime.now(),
            'move_id': move.id if move else False,
            'auto_reverse_move_id': reversed_move.id if reversed_move else False,
        })

    def action_cancel(self):
        """Cancel a confirmed Journal Memorial by creating a reciprocal record."""
        self.ensure_one()
        if self.state != 'confirm':
            raise Warning(_('Only confirmed Journal Memorials can be cancelled!'))
        self._create_reciprocal_record()

    # 14: private methods
    def _create_reciprocal_record(self):
        """Create a reciprocal JM record with reversed Debit/Credit lines, auto-confirm it,
        and mark the original record as cancelled.
        
        Mirrors the Odoo 8 logic from wtc_journal_memorial.action_create_memorial().
        """
        self.ensure_one()

        # Prepare reversed lines (swap Debit ↔ Credit)
        line_vals = []
        for line in self.line_ids:
            line_vals.append(Command.create({
                'account_id': line.account_id.id,
                'amount': line.amount,
                'type': 'debit' if line.type == 'credit' else 'credit',
                'name': line.name,
                'company_id': line.company_id.id,
                'partner_id': line.partner_id.id if line.partner_id else False,
                'asset_id': line.asset_id.id if line.asset_id else False,
            }))

        # Create reciprocal record
        reciprocal_vals = {
            'company_id': self.company_id.id,
            'period_id': self.period_id.id,
            'current_period_id': self.current_period_id.id,
            'description': 'Cancel Journal Memorial No %s' % self.name,
            'division': self.division,
            'date': date.today(),
            'is_auto_reverse': self.is_auto_reverse,
            'code': 'cancel',
            'journal_id': self.journal_id.id,
            'line_ids': line_vals,
        }
        reciprocal = self.sudo().create(reciprocal_vals)

        # Auto-confirm the reciprocal record
        reciprocal.action_confirm()

        # Update original record
        self.write({
            'state': 'cancel',
            'cancel_refered_id': reciprocal.id,
        })
    
    def _validate_journal_memorial(self):
        for record in self:
            if not record.line_ids:
                raise Warning(_('Please add some journal lines!'))

    def _check_balance(self):
        for record in self:
            if record.state == 'draft' and record.line_ids:
                precision = self.env['decimal.precision'].precision_get('Account')
                if float_compare(record.total_debit, record.total_credit, precision_digits=precision) != 0:
                    raise Warning(_('Total debit and credit must be balanced!'))

    def _create_account_move(self):
        self.ensure_one()
        move_vals = {
            'date': self.date if self.period_id.id == self.current_period_id.id else self.period_id.date_to, #? Jika menggunakan ini terkena validation error karena date dengan sequence nya tidak relate 
            # 'date': self.date,
            'journal_id': self.journal_id.id,
            'period_id': self.period_id.id,
            'division': self.division,
            'name': self.name,
            'ref': self.name,
            'company_id': self.company_id.id,
            'line_ids': [
                Command.create(line._prepare_move_line_vals())
                for line in self.line_ids
            ]
        }
        
        # Create and post the move
        move = self.env['account.move'].sudo().create(move_vals)
        move.sudo().action_post()
        self.move_id = move.id

        reversed_move = False
        if self.is_auto_reverse:    
            reversed_move = self._create_auto_reverse_move(move)
        return move, reversed_move

    def _create_auto_reverse_move(self, move):
        self.ensure_one()
        if not move or not self.is_auto_reverse or not self.period_id:
            return False

        # Create reverse move
        reverse_date = self.period_id.date_to
        prefix = move.name.split('/')[0]
        reverse_move = move.sudo()._reverse_moves(default_values_list=[{
            'date': reverse_date,
            'name': move.name.replace(prefix, prefix+'R'),
            'ref': _('Reversal of: %s') % move.name,
            'journal_id': self.journal_id.id,
            'period_id': self.period_id.id,
        }])
        
        self.auto_reverse_move_id = reverse_move.id
        if reverse_move:
            reverse_move.sudo().action_post()
        
        return reverse_move
    
    def _recompute_depreciation(self):
        for record in self:
            for line in record.line_ids:
                if line.asset_id:
                    line.asset_id.suspend_security().compute_depreciation_board()
    