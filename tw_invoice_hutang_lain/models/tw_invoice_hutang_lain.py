# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError as Warning


class TwInvoiceHutangLain(models.Model):
    _name = "tw.invoice.hutang.lain"
    _description = "Invoice Hutang Lain"
    _order = "id desc"

    # 7: default methods
    def _get_default_branch(self):
        company = self.env.company
        return company.id if company.parent_id else False

    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    # 8: fields
    name = fields.Char(string="Name", readonly=True, copy=False)
    date = fields.Date(string="Date", readonly=True, default=_get_default_date)
    description = fields.Char(string="Description")
    amount = fields.Float(string="Paid Amount", digits="Product Price")
    no_hp = fields.Char(string="No HP")

    partner_type = fields.Selection([
        ('principle', 'Principle'),
        ('biro_jasa', 'Biro Jasa'),
        ('forwarder', 'Forwarder'),
        ('supplier', 'General Supplier'),
        ('finance_company', 'Finance Company'),
        ('customer', 'Customer'),
        ('dealer', 'Dealer'),
        ('ahass', 'Ahass'),
    ], string="Partner Type", default="customer")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_for_payment', 'Waiting For Payment'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'),
    ], string="State", readonly=True, default="draft", copy=False)
    division = fields.Selection(
        selection=lambda self: self.env['tw.selection'].get_division_options(),
        string="Division",
        default="Unit",
        required=True,
    )

    # 9: relation fields
    branch_id = fields.Many2one(
        'res.company',
        string="Branch",
        required=True,
        default=_get_default_branch,
        domain="[('parent_id', '!=', False)]",
    )
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    journal_id = fields.Many2one(
        'account.journal',
        string="Journal",
        domain="[('company_id', 'parent_of', branch_id), ('type', 'in', ('bank', 'cash'))]",
    )
    account_id = fields.Many2one(
        'account.account',
        string="Hutang Lain Account",
        domain="[('account_type', '=', 'liability_payable'), ('company_ids', 'parent_of', branch_id)]",
    )
    currency_id = fields.Many2one('res.currency', string="Currency")
    company_id = fields.Many2one('res.company', string="Company")
    hutang_lain_id = fields.Many2one('tw.account.payment', string="Hutang Lain", readonly=True, copy=False)

    # Audit Trails
    paid_uid = fields.Many2one('res.users', string="Paid by", readonly=True, copy=False)
    paid_date = fields.Datetime(string="Paid on", readonly=True, copy=False)
    cancel_uid = fields.Many2one('res.users', string="Cancelled by", readonly=True, copy=False)
    cancel_date = fields.Datetime(string="Cancelled on", readonly=True, copy=False)

    # 11: onchange methods
    @api.onchange('branch_id')
    def _onchange_branch_id(self):
        self.company_id = self.branch_id
        if self.branch_id:
            self.currency_id = self.branch_id.currency_id.id
            self.account_id = self._get_hutang_lain_account(self.branch_id).id

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        if not self.journal_id:
            return

        journal = self.journal_id
        journal_account = journal.default_credit_account_id or journal.default_debit_account_id or journal.default_account_id
        if not journal_account:
            raise Warning(_("Konfigurasi jurnal account belum dibuat, silahkan setting dulu!"))

        self.currency_id = journal.currency_id.id or journal.company_id.currency_id.id
        self.company_id = journal.company_id.id
        account = self._get_hutang_lain_account(self.branch_id)
        if not self.account_id and account.account_type == 'liability_payable':
            self.account_id = account.id

    # 12: CRUD methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            branch = self.env['res.company'].browse(vals.get('branch_id')) if vals.get('branch_id') else self.env.company
            if branch:
                vals.setdefault('company_id', branch.id)
                vals.setdefault('currency_id', branch.currency_id.id)
                if not vals.get('account_id'):
                    account = self._get_hutang_lain_account(branch)
                    if account:
                        vals['account_id'] = account.id
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].with_company(branch).get_sequence_code(
                    'INVHL',
                    branch.code or branch.name or '',
                    sequence_date=vals.get('date'),
                )
        return super().create(vals_list)

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise Warning(_("Transaksi yang berstatus selain Draft tidak bisa dihapus."))
        return super().unlink()

    def copy(self, default=None):
        raise Warning(_("Transaksi ini tidak dapat diduplikat."))

    # 13: action methods
    def action_rfp(self):
        self.ensure_one()
        self.write({'state': 'waiting_for_payment'})

    def action_paid(self):
        self.ensure_one()
        self._validate_paid_values()

        payment_vals = self._prepare_hutang_lain_payment_vals()
        payment = self.env['tw.account.payment'].with_company(self.branch_id).create(payment_vals)

        self.write({
            'hutang_lain_id': payment.id,
            'state': 'paid',
            'paid_date': datetime.now(),
            'paid_uid': self.env.uid,
        })

    def action_cancel(self):
        self.ensure_one()
        self.write({
            'state': 'cancel',
            'cancel_date': datetime.now(),
            'cancel_uid': self.env.uid,
        })

    def action_open_hutang_lain(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.account.payment',
            'name': _('Hutang Lain'),
            'view_mode': 'form',
            'res_id': self.hutang_lain_id.id,
        }

    # 14: private methods
    def _get_hutang_lain_account(self, branch):
        branch_setting = False
        if branch and 'branch_setting_id' in branch._fields:
            branch_setting = branch.branch_setting_id
        if not branch_setting and branch:
            branch_setting = self.env['tw.branch.setting'].sudo().search([('company_id', '=', branch.id)], limit=1)
        account_setting = branch_setting.account_setting_id if branch_setting else False
        if account_setting and 'hutang_lain_account_line_id' in account_setting._fields:
            return account_setting.hutang_lain_account_line_id
        return self.env['account.account']

    def _validate_paid_values(self):
        if self.state != 'waiting_for_payment':
            raise Warning(_("Hanya transaksi Waiting For Payment yang bisa dibayar."))
        if self.hutang_lain_id:
            raise Warning(_("Hutang Lain sudah dibuat untuk transaksi ini."))
        if not self.amount or self.amount <= 0:
            raise Warning(_("Paid Amount harus lebih dari 0."))
        if not self.journal_id:
            raise Warning(_("Journal harus diisi."))
        if not self.account_id:
            raise Warning(_("Hutang Lain Account harus diisi."))

    def _prepare_hutang_lain_payment_vals(self):
        description = self.description or self.name
        return {
            'company_id': self.branch_id.id,
            'beneficiary_company_id': self.branch_id.id,
            'division': self.division,
            'payment_type': 'inbound',
            'type': 'receive_payment',
            'partner_type': self.partner_type,
            'partner_id': self.partner_id.id,
            'amount': self.amount,
            'journal_id': self.journal_id.id,
            'memo': description,
            'narration': description,
            'currency_id': self.currency_id.id or self.branch_id.currency_id.id,
            'line_cr_ids': [(0, 0, {
                'account_id': self.account_id.id,
                'company_id': self.branch_id.id,
                'beneficiary_company_id': self.branch_id.id,
                'name': description,
                'type': 'cr',
                'amount': self.amount,
            })],
        }
