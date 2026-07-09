from locale import currency
import pytz
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError as Warning
from odoo.addons.tw_base.models.amount_to_text import convert

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('paid', 'Paid'),
    ('cancel', 'Cancelled'),
]


class TwReimbursementPettyCash(models.Model):
    _name = "tw.reimbursement.petty.cash"
    _description = "Reimbursement Petty Cash"
    _inherit = ["mail.thread","mail.activity.mixin"]
    _order = 'id desc'

    def _get_default_date_tz(self):
        return pytz.UTC.localize(fields.Datetime.now()).astimezone(pytz.timezone(self.env.user.tz or 'Asia/Jakarta'))

    name = fields.Char(string="Name", readonly=True, default=False, copy=False)
    state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft')
    petty_cash_out_count = fields.Integer(compute='_count_detail_payslip', string="Items")
    document_claim_filename = fields.Char(string='Filename')
    document_claim_file = fields.Binary(string='File')
    document_claim_upload_filename = fields.Char(string='Filename Upload')
    document_claim_upload_file = fields.Binary('File Upload')
    amount_total = fields.Monetary(string='Total Amount Real', currency_field = 'currency_id', store=True, readonly=True,
                                compute='_compute_amount')
    amount_pco = fields.Monetary(string='Total Amount PCO', currency_field = 'currency_id', store=True, readonly=True,
                                compute='_compute_amount')
    date = fields.Date(
        string='Date',
        default=_get_default_date_tz)

    confirm_uid = fields.Many2one('res.users', string="Approved by")
    confirm_date = fields.Datetime('Date Approved')
    cancel_uid = fields.Many2one('res.users', string="Cancelled by")
    cancel_date = fields.Datetime('Date Cancelled')

    currency_id = fields.Many2one('res.currency', string='Currency', compute="_compute_amount", store=True,
                             default=lambda self: self.env.company.currency_id,)
    company_id = fields.Many2one('res.company', string='Branch', required=True, domain=[('parent_id', '!=', False)])
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    journal_id = fields.Many2one('account.journal', string="Payment Method", domain="[('type', '=', 'petty_cash'), ('company_id', 'parent_of', company_id)]")
    petty_cash_out_ids = fields.Many2many('tw.petty.cash.out',string='Petty Cash Out')

    @api.depends('petty_cash_out_ids')
    def _compute_amount(self):
        for rec in self:
            rec.amount_total = sum(line.amount_real for line in rec.petty_cash_out_ids)
            rec.amount_pco = sum(line.amount for line in rec.petty_cash_out_ids)
            if rec.petty_cash_out_ids:
                rec.currency_id = rec.petty_cash_out_ids[0].currency_id
            else:
                rec.currency_id = self.env.company.currency_id

    @api.depends('petty_cash_out_ids')
    def _count_detail_payslip(self):
        for rec in self:
            rec.petty_cash_out_count = len(rec.petty_cash_out_ids)

    @api.onchange(
        'company_id',
        'journal_id',
        'division',
    )
    def onchange_fill_petty_cash(self):
        petty_cash_out_ids = self.env['tw.petty.cash.out'].search([
            ('company_id', '=', self.company_id.id),
            ('journal_petty_id', '=', self.journal_id.id),
            ('division', '=', self.division),
            ('state', '=', 'posted'),
            ('reimbursed_id', '=', False)
        ], order='id ASC')
        self.petty_cash_out_ids = petty_cash_out_ids

    def action_open_petty_cash_out(self):
        self.ensure_one() 
        return {
            'name': 'Petty Cash Out',
            'type': 'ir.actions.act_window',
            'view_mode': 'list,form',
            'res_model': 'tw.petty.cash.out',
            'domain': [('id', 'in', self.petty_cash_out_ids.ids)],
            'context': {'default_reimbursed_id': self.id},
            'target': 'current',
        }

    def convert_number_format_rupiah(self):
        return convert(self.amount_total)

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('company_id'):
                branch_src = self.env['res.company'].suspend_security().search([
                    ('id', '=', values['company_id'])
                ], limit=1)
                values['name'] = self.env['ir.sequence'].get_sequence_code('PCR', str(branch_src.code))
        res = super().create(vals_list)
        return res

    def write(self, values):
        return super(TwReimbursementPettyCash, self).write(values)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("Tidak dapat menghapus data yang tidak dalam status draft."))
