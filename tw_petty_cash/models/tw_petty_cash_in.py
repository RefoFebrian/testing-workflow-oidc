from datetime import datetime
from locale import currency
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError as Warning

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('posted', 'Posted'),
    ('cancel', 'Cancelled'),
]


class TwPettyCashIn(models.Model):
    _name = "tw.petty.cash.in"
    _inherit = ['account.payment',"mail.thread","mail.activity.mixin"]
    _description = "Petty Cash In"
    _order = "id desc"

    def _get_period(self):
        period_id = self.env['tw.account.period']._get_current_periods()
        return period_id.id

    def _get_default_date(self):
        return datetime.now()

    name = fields.Char(string="Name", readonly=True, default='New', copy=False, compute=False, inverse=False)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    state = fields.Selection(
        selection_add=STATE_SELECTION, string='State', readonly=True, default='draft',
        ondelete = {
            'draft': 'set default',
            'posted': 'set default',
            'cancel': 'set default',
        }
    )
    
    # Audit trail
    account_id = fields.Many2one('account.account', string="Account")
    confirm_uid = fields.Many2one('res.users', string="Posted by")
    confirm_date = fields.Datetime('Posted on')
    cancel_uid = fields.Many2one('res.users', string="Cancelled by")
    cancel_date = fields.Datetime('Cancelled on')
    
    # Relational Field
    company_id = fields.Many2one('res.company', string='Branch', required=True, domain=[('parent_id', '!=', False)])
    branch_destination_id = fields.Many2one(related='petty_cash_out_id.branch_destination_id', store=True)
    journal_id = fields.Many2one(related='petty_cash_out_id.journal_petty_id', store=True, required=False, readonly=True)
    petty_cash_in_line_ids = fields.One2many('tw.petty.cash.in.line', 'petty_cash_in_id', string="Petty Cash In Line", copy=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user.id)
    move_line_ids = fields.One2many('account.move.line', related='move_id.line_ids', string='Journal Items', readonly=True)
    period_id = fields.Many2one('tw.account.period', string="Period", related='move_id.period_id', store=True, readonly=True)
    invoice_ids = fields.Many2many(
        string="Invoices",
        comodel_name='account.move',
        relation='account_move__tw_petty_cash_in',
        column1='payment_id',
        column2='petty_cash_in_id',
        copy=False,
    )
    petty_cash_out_id = fields.Many2one('tw.petty.cash.out', string="Petty Cash Out")
    available_account_ids = fields.Many2many(comodel_name='account.account',compute='_compute_available_account_ids')
    pco_amount = fields.Monetary(string="Amount PCO", related="petty_cash_out_id.amount", readonly=True,store=False, currency_field = 'currency_id')

    @api.depends('company_id')
    def _compute_available_account_ids(self):
        for record in self:
            domain = ['|', ('company_ids', 'in', record.company_id.id), ('company_ids', 'parent_of', record.company_id.id)]
            filter_type = 'petty_cash_in'
            account_filter_domain = self.env['tw.account.filter'].get_account_domain(filter_type)
            if account_filter_domain:
                domain += account_filter_domain
            record.available_account_ids = self.env['account.account'].search(domain)

    @api.depends('move_id.name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name or _('Draft Petty Cash In')

    def _compute_refunds_count(self):
        rg_data = self.env[self._name]._read_group(
            domain=[
                ('source_payment_id', 'in', self.ids),
                ('payment_transaction_id.operation', '=', 'refund')
            ],
            groupby=['source_payment_id'],
            aggregates=['__count']
        )
        data = {source_payment.id: count for source_payment, count in rg_data}
        for payment in self:
            payment.refunds_count = data.get(payment.id, 0)

    @api.onchange('petty_cash_out_id')
    def onchange_petty_cash_out(self):
        self.petty_cash_in_line_ids = False

    def action_post_petty_cash_in(self):
        for rec in self.filtered(lambda r: r.state == 'draft'):
            rec.validate_order()
            rec.write({
                'period_id': self._get_period(),
                'date': fields.Date.today(),
                'state': 'posted',
                'confirm_uid': self.env.uid,
                'confirm_date': datetime.now()
            })
            rec.sudo()._action_move_line_in_create()
            if rec._is_inter_company():
                rec.sudo()._action_aml_inter_company_create()
            rec.move_id.sudo().action_post()
            rec.petty_cash_out_id.sudo().action_recalculate_amount_real()

    def action_cancel(self):
        self.write({
            'state': 'cancel',
            'cancel_uid': self.env.uid,
            'cancel_date': datetime.now()
        })
        draft_moves = self.move_id.filtered(lambda m: m.state == 'draft')
        draft_moves.unlink()
        (self.move_id - draft_moves).button_cancel()
        self.mapped('petty_cash_out_id').sudo().action_recalculate_amount_real()

    
    def validate_order(self):
        for rec in self:
            if not rec.amount:
                raise ValidationError('Silakan masukkan (amount).')
            if not rec.petty_cash_in_line_ids:
                raise ValidationError('Silakan masukkan detail line.')
            if rec.amount > rec.petty_cash_out_id.amount_real:
                raise ValidationError(f'Amount tidak boleh melebihi sisa petty cash out. Sisa: {"{:,.2f}".format(rec.petty_cash_out_id.amount_real)}')
            line_amount = 0
            for line in rec.petty_cash_in_line_ids:
                line_amount += line.amount
                petty_cash_out_line_id = self.env['tw.petty.cash.out.line'].search([
                    ('petty_cash_out_id', '=', line.petty_cash_in_id.petty_cash_out_id.id),
                    ('account_id', '=', line.account_id.id),
                ], limit=1)
                if line.amount > petty_cash_out_line_id.amount:
                    raise ValidationError(f'Amount akun {line.account_id.display_name} lebih besar dari Amount petty cash out.')
            if rec.amount != line_amount:
                raise ValidationError('Total Amount harus sama.')

    def get_total_value(self):
        total = 0
        for line in self.petty_cash_in_line_ids:
            total = total + line.amount
        return total

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('company_id'):
                branch_src = self.env['res.company'].suspend_security().search([
                    ('id', '=', values['company_id'])
                ], limit=1)
                values['name'] = self.env['ir.sequence'].get_sequence_code('PCI', str(branch_src.code))
        res = super().create(vals_list)
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("Tidak dapat menghapus data yang tidak dalam status draft."))

    def _is_inter_company(self):
        self.ensure_one()
        if self.company_id.id != self.branch_destination_id.id:
            return True
        return False

    def _action_move_line_in_create(self):
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        for rec in self:
            name = rec.name
            date = rec.date
            journal_id = rec.journal_id.id
            account_id = rec.journal_id.default_credit_account_id.id or rec.journal_id.default_debit_account_id.id
            period_id = rec.period_id.id
            if not account_id:
                raise ValidationError(
                    _(f'Silakan masukkan akun debit dan kredit default untuk journal {rec.journal_id.display_name}'))
            move_id = move_obj.sudo().search([
                ('journal_id', '=', journal_id),
                ('name', '=', name),
                ('ref', '=', name)
            ], limit=1)
            if not move_id:
                move_vals = {
                    'name': name,
                    'journal_id': journal_id,
                    'company_id': rec.company_id.id,
                    'date': date,
                    'ref': name,
                    'period_id': period_id,
                    'partner_id': rec.company_id.partner_id.id,
                    'division': rec.division,
                }
                move_id = move_obj.sudo().create(move_vals)
                move_line1 = {
                    'name': _('Petty Cash In'),
                    'ref': name,
                    'account_id': account_id,
                    'move_id': move_id.id,
                    'journal_id': journal_id,
                    'period_id': period_id,
                    'date': date,
                    'debit': rec.amount,
                    'credit': 0.0,
                    'company_id': rec.company_id.id,
                    'division': rec.division,
                    'partner_id': rec.company_id.partner_id.id,
                }
                move_line_obj.sudo().with_context(check_move_validity=False).create(move_line1)
                for line in rec.petty_cash_in_line_ids:
                    move_line_2 = {
                        'name': line.name,
                        'ref': name,
                        'account_id': line.account_id.id,
                        'move_id': move_id.id,
                        'journal_id': journal_id,
                        'period_id': period_id,
                        'date': date,
                        'debit': 0.0,
                        'credit': line.amount,
                        'company_id': rec.branch_destination_id.id,
                        'division': rec.division,
                        'partner_id': rec.company_id.partner_id.id,
                    }
                    move_line_obj.sudo().with_context(check_move_validity=False).create(move_line_2)
            rec.write({
                'move_id': move_id.id,
                'account_id': account_id
            })

    def _action_aml_inter_company_create(self):
        self.ensure_one()
        if not self.company_id.branch_setting_id.inter_company_account_id:
            raise Warning(_(f'Account intercompany branch {self.company_id.name} belum diisi.'))
        if not self.branch_destination_id.branch_setting_id.inter_company_account_id:
            raise Warning(_(f'Account intercompany branch {self.branch_destination_id.name} belum diisi.'))
        inter_branch_header_account_id = self.company_id.branch_setting_id.inter_company_account_id
        inter_branch_detail_account_id = self.branch_destination_id.branch_setting_id.inter_company_account_id
        move_line_ids = self.move_id.line_ids.filtered(lambda l: l.company_id.id == self.branch_destination_id.id)
        balance = sum(move_line_ids.mapped('debit')) - sum(move_line_ids.mapped('credit'))
        debit = abs(balance) if balance < 0 else 0
        credit = balance if balance > 0 else 0
        if balance:
            move_line_obj = self.env['account.move.line']
            move_line1 = {
                'name': _(f'Interco Petty Cash In {self.branch_destination_id.name}'),
                'ref': _(f'Interco Petty Cash In {self.branch_destination_id.name}'),
                'account_id': inter_branch_header_account_id.id,
                'move_id': self.move_id.id,
                'journal_id': self.journal_id.id,
                'period_id': self.period_id.id,
                'date': self.date,
                'debit': debit,
                'credit': credit,
                'company_id': self.branch_destination_id.id,
                'division': self.division
            }
            move_line_obj.sudo().with_context(check_move_validity=False).create(move_line1)
            move_line_2 = {
                'name': _(f'Interco Petty Cash In {self.company_id.name}'),
                'ref': _(f'Interco Petty Cash In {self.company_id.name}'),
                'account_id': inter_branch_detail_account_id.id,
                'move_id': self.move_id.id,
                'journal_id': self.journal_id.id,
                'period_id': self.period_id.id,
                'date': self.date,
                'debit': credit,
                'credit': debit,
                'company_id': self.company_id.id,
                'division': self.division
            }
            move_line_obj.sudo().with_context(check_move_validity=False).create(move_line_2)
