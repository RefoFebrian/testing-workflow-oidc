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
import odoo.addons.decimal_precision as dp

# 4: imports from odoo modules
from odoo.tools import float_compare

# 5: local imports

# 6: Import of unknown third party lib

# 7: variable declarations

# 8: class definitions
class TwNetOff(models.Model):
    _name = "tw.net.off"
    _description = "Net Off"
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

    # 8: fields - Basic Fields
    name = fields.Char(string='Name', compute='_compute_name', store=True)
    date = fields.Date(string="Date", required=True, default=_get_default_date, tracking=True, readonly=True)
    state = fields.Selection(selection=STATE_SELECTION, string="State", default="draft", tracking=True)
    description = fields.Char(string="Description")
    
    # Computed Fields
    total_debit = fields.Monetary(string="Total Debit", compute="_compute_totals", store=True, tracking=True)
    total_credit = fields.Monetary(string="Total Credit", compute="_compute_totals", store=True, tracking=True)
    total_residual = fields.Monetary(string="Total Residual", compute="_compute_totals", store=True, tracking=True)
    is_full_reconcile = fields.Boolean(string="Is Full Reconcile", compute="_compute_totals", store=True, tracking=True)
    
    # Audit Trail
    confirm_uid = fields.Many2one('res.users', string="Confirmed by", copy=False)
    confirm_date = fields.Datetime(string="Confirmed on", copy=False)
    
    # 9: Relational Fields
    company_id = fields.Many2one('res.company', string="Branch", required=True, tracking=True, default=_get_default_branch)
    currency_id = fields.Many2one('res.currency', string="Currency", related="company_id.currency_id", readonly=True)
    account_id = fields.Many2one('account.account', string="Account", required=True)
    partner_id = fields.Many2one('res.partner', string="Partner")
    
    line_ids = fields.One2many('tw.net.off.line', 'net_off_id', string="Journals", copy=True)
    move_line_ids = fields.One2many('account.move.line', compute='_compute_move_line_ids', string="Journal Items", readonly=True)
    
    # 10: compute and search fields, in the same order of fields declaration
    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            if record.id and not record.name and record.state:
                seq_name = self.env['ir.sequence'].with_company(record.company_id).get_sequence_code('NO', record.company_id.code)
                record.name = seq_name

    @api.depends('line_ids.move_line_id', 'line_ids.credit', 'line_ids.debit')
    def _compute_totals(self):
        for record in self:
            record.total_debit = sum(line.debit for line in record.line_ids)
            record.total_credit = sum(line.credit for line in record.line_ids)
            record.total_residual = sum(line.move_line_id.amount_residual for line in record.line_ids)
            record.is_full_reconcile = record.total_debit == record.total_credit
    
    @api.depends('line_ids.move_line_id','state')
    def _compute_move_line_ids(self):
        for record in self:
            if record.state == 'confirm':
                record.move_line_ids = record.line_ids.move_line_id
            else:
                record.move_line_ids = False

    @api.onchange('company_id','account_id','partner_id')
    def _onchange_reset_line(self):
        for record in self:
            record.line_ids = False
            
    # 11: CRUD methods (and name_get, name_search, ...) overrides
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._validate_entries()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'line_ids' in vals:
            self._validate_entries()
        return res

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise Warning(_('You can only delete draft journal memorials!'))
            if record.move_id:
                raise Warning(_('You cannot delete a journal memorial with posted entries!'))
        return super().unlink()

    # 12: action methods
    def action_confirm(self):
        self.ensure_one()
        
        if self.state == 'confirm':
            raise Warning(_('Record already confirmed, please refresh!'))

        if not self.line_ids:
            raise Warning(_('Please add some journal lines!'))
        
        # Create account move
        self._reconcile_move()
        
        # Update the journal memorial
        self.write({
            'state': 'confirm',
            'confirm_uid': self.env.user.id,
            'confirm_date': datetime.now(),
        })

    # 13: private methods
    def _validate_entries(self):
        for record in self:
            if not record.line_ids:
                raise Warning(_('Please add some journal lines!'))
            if record.state == 'draft' and record.line_ids:
                total_debit = 0
                total_credit = 0
                for line in record.line_ids:
                    total_debit += line.debit
                    total_credit += line.credit
                    if line.move_line_id.move_id.state != 'posted':
                        raise Warning(_('Journal line %s (%s) is not posted!') % (line.move_line_id.name, line.move_line_id.move_id.name))
                    if line.move_line_id.reconciled:
                        raise Warning(_('Journal line %s (%s) is reconciled!') % (line.move_line_id.name, line.move_line_id.move_id.name))
                
                if total_debit <= 0:
                    raise Warning(_('Total Debit harus lebih dari 0!'))
                if total_credit <= 0:
                    raise Warning(_('Total Credit harus lebih dari 0!'))

    def _reconcile_move(self):
        self.ensure_one()
        move_line_ids = self.line_ids.mapped('move_line_id')
        move_line_ids.sudo().reconcile()
        return True
            