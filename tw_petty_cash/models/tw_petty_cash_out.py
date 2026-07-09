from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError as Warning
from markupsafe import Markup

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('posted', 'Posted'),
    ('reimbursed', 'Reimbursed'),
    ('cancel', 'Cancelled'),
]


class TwPettyCashOut(models.Model):
    _name = "tw.petty.cash.out"
    _inherit = ['account.payment',"mail.thread","mail.activity.mixin"]
    _description = "Petty Cash Out"
    _order = "id desc"

    def _get_default_date(self):
        return datetime.now()

    def _get_period(self):
        period_id = self.env['tw.account.period']._get_current_periods()
        return period_id.id

    name = fields.Char(string="Name", readonly=True, default='New', copy=False, compute=False, inverse=False)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    state = fields.Selection(selection_add = STATE_SELECTION, string='State', readonly=True, default='draft',
        ondelete={
            'draft': 'set default',
            'posted': 'set default',
            'reimbursed': 'set default',
            'cancel': 'set default',
        }
    )
    amount_real = fields.Float(string='Amount Real', digits='Price Unit', store=True, readonly=True, compute='_compute_amount')
    
    # Audit trail
    confirm_uid = fields.Many2one('res.users', string="Posted by")
    confirm_date = fields.Datetime('Posted on')
    cancel_uid = fields.Many2one('res.users', string="Cancelled by")
    cancel_date = fields.Datetime('Cancelled on')
    
    # Relational Field
    company_id = fields.Many2one('res.company', string='Branch', required=True, domain=[('parent_id', '!=', False)],)
    employee_id = fields.Many2one('hr.employee', string='Responsible',required=True,domain=[('company_id', 'in', 'company_id')], default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1).id)
    receiver_id = fields.Many2one('res.partner',string='Penerima Uang', domain="['|', ('company_id', '=', company_id), ('company_id', '=', False)]")
    branch_destination_id = fields.Many2one('res.company', string='Branch Destination', required=True, domain=[('parent_id', '!=', False)])
    petty_cash_out_line_ids = fields.One2many('tw.petty.cash.out.line', 'petty_cash_out_id', string="Petty Cash Out Line", copy=True)
    move_line_ids = fields.One2many('account.move.line', related='move_id.line_ids', string='Journal Items', readonly=True)
    period_id = fields.Many2one('tw.account.period', string="Period", related='move_id.period_id', store=True, readonly=True)
    account_id = fields.Many2one('account.account', string="Account")
    reimbursed_id = fields.Many2one('tw.reimbursement.petty.cash', copy=False)
    invoice_ids = fields.Many2many(
        string="Invoices",
        comodel_name='account.move',
        relation='account_move__tw_petty_cash_out',
        column1='payment_id',
        column2='petty_cash_out_id',
        copy=False,
    )
    available_account_ids = fields.Many2many(comodel_name='account.account',compute='_compute_available_account_ids')
    journal_petty_id = fields.Many2one('account.journal',default=False, string="Journal" )
    saldo_petty_cash = fields.Monetary(string='Saldo Petty Cash', currency_field='currency_id', compute='_compute_saldo_petty_cash')

    @api.depends('company_id', 'journal_petty_id', 'division')
    def _compute_saldo_petty_cash(self):
        for rec in self:
            saldo = 0
            if rec.company_id and rec.journal_petty_id:
                account_id = rec.journal_petty_id.default_credit_account_id or rec.journal_petty_id.default_debit_account_id
                if account_id:
                    moves = self.env['account.move.line'].sudo().search([
                        ('account_id', 'in', account_id.ids), 
                        ('parent_state', '=', 'posted'), 
                        ('balance', '!=', 0), 
                        ('company_id', 'child_of', rec.company_id.id)
                        ])
                    saldo = sum(moves.mapped('balance'))
            rec.saldo_petty_cash = saldo

    @api.depends('company_id')
    def _compute_available_account_ids(self):
        for record in self:
            domain = ['|', ('company_ids', 'in', record.company_id.id), ('company_ids', 'parent_of', record.company_id.id)]
            filter_type = 'petty_cash_out'
            account_filter_domain = self.env['tw.account.filter'].get_account_domain(filter_type)
            if account_filter_domain:
                domain += account_filter_domain
            record.available_account_ids = self.env['account.account'].search(domain)
            
    @api.depends('move_id.name')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec.name or _('Draft Petty Cash Out')

    @api.depends('petty_cash_out_line_ids.amount_real')
    def _compute_amount(self):
        for rec in self:
            amount_real = sum(line.amount_real for line in rec.petty_cash_out_line_ids)
            rec.amount_real = amount_real

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
            
    @api.onchange('company_id')
    def _onchange_company_journal_petty_id(self):
        self.ensure_one()
        if self.company_id:
            self.branch_destination_id = self.company_id
        else:
            self.branch_destination_id = False
        
        self.journal_petty_id = False
    
    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.receiver_id = (
                self.employee_id.work_contact_id
                or self.employee_id.address_home_id
            )
        else:
            self.receiver_id = False
            
    def action_post_petty_cash_out(self):
        for rec in self._get_to_post():
            rec.write({
                'period_id': self._get_period(),
                'date': fields.Date.today(),
                'state': 'posted',
                'confirm_uid': self.env.uid,
                'confirm_date': datetime.now()
            })
            rec.sudo()._action_move_line_out_create()
            if rec._is_inter_company():
                rec._action_aml_inter_company_create()
            rec.move_id.sudo().action_post()
            rec._set_amount_real()

            pco_line_names = '<br>'.join(rec.petty_cash_out_line_ids.mapped('name'))
            rec.sudo().message_post(
                body=Markup(f"Petty Cash Out <b>{rec.name or '(tanpa nama)'}</b> Posted.<br> Petty Cash Line: <br>{pco_line_names}"),
                subtype_xmlid="mail.mt_note"
            )

    def action_recalculate_amount_real(self):
        for rec in self.filtered(lambda r: r.state == 'posted'):
            rg_data = self.env['tw.petty.cash.in.line']._read_group(
                domain=[
                    ('petty_cash_in_id.petty_cash_out_id', '=', rec.id),
                    ('petty_cash_in_id.state', '=', 'posted'),
                ],
                groupby=['account_id'],
                aggregates=['amount:sum']
            )
            pci_amounts = {account.id: amount_sum for account, amount_sum in rg_data if account}
            
            # Reset amount_real to amount for all lines first
            for line in rec.petty_cash_out_line_ids:
                line.amount_real = line.amount
            
            # Deduct the petty cash in amounts sequentially from matching PCO lines
            for account_id, pci_amount in pci_amounts.items():
                remaining = pci_amount
                for line in rec.petty_cash_out_line_ids.filtered(lambda l: l.account_id.id == account_id):
                    if remaining <= 0:
                        break
                    deduct = min(line.amount_real, remaining)
                    line.amount_real -= deduct
                    remaining -= deduct
            
    def recalculate_amount_real(self):
        self.action_recalculate_amount_real()

    def action_cancel(self):
        self.write({
            'state': 'cancel',
            'cancel_uid': self.env.uid,
            'cancel_date': datetime.now()
        })
        draft_moves = self.move_id.filtered(lambda m: m.state == 'draft')
        draft_moves.unlink()
        (self.move_id - draft_moves).button_cancel()

    def get_total_value(self):
        total = 0
        for line in self.petty_cash_out_line_ids:
            total = total + line.amount
        return total

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('company_id'):
                branch_src = self.env['res.company'].suspend_security().search([
                    ('id', '=', values['company_id'])
                ], limit=1)
                values['name'] = self.env['ir.sequence'].get_sequence_code('PCO', str(branch_src.code))
        res = super().create(vals_list)
        return res

    def copy(self,default=None):
        default = dict(default or {})
        default['amount_real'] = 0.0

        new_lines = []
        for line in self.petty_cash_out_line_ids:
            vals = line.copy_data()[0]
            vals['amount_real']=0.0
            new_lines.append((0,0,vals))
        default['petty_cash_out_line_ids'] = new_lines
        return super(TwPettyCashOut, self).copy(default)
    
    def validate_order(self):
        for rec in self:
            if rec.saldo_petty_cash < rec.amount:
                raise ValidationError(
                    _(f'Saldo petty cash tidak cukup. Saldo saat ini: {"{:,.2f}".format(rec.saldo_petty_cash)}')
                )
            if not rec.amount:
                raise ValidationError(_('Silahkan masukkan amount.'))
            if not rec.petty_cash_out_line_ids:
                raise ValidationError(_('Silahkan masukkan line details.'))
            for line in rec.petty_cash_out_line_ids:
                if line.amount <= 0:
                    raise ValidationError(_('amount di line details tidak boleh lebih kecil dari 0.'))
            line_amount = sum(rec.petty_cash_out_line_ids.mapped('amount'))
            if rec.amount != line_amount:
                raise ValidationError(_('Amount total harus sama.'))

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError("Tidak dapat menghapus data yang tidak dalam status draft.")

    def _set_amount_real(self):
        for rec in self:
            for line in rec.petty_cash_out_line_ids :
                line.amount_real = line.amount

    def _is_inter_company(self):
        self.ensure_one()
        if self.company_id.id != self.branch_destination_id.id:
            return True
        return False

    def _action_move_line_out_create(self):
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        for rec in self:
            name = rec.name
            date = rec.date
            journal_petty_id = rec.journal_petty_id.id
            account_id = rec.journal_petty_id.default_credit_account_id.id or rec.journal_petty_id.default_debit_account_id.id
            period_id = rec.period_id.id
            if not account_id:
                raise ValidationError(_(f'Silakan masukkan akun debit dan kredit default untuk journal {rec.journal_petty_id.display_name}'))

            move_vals = {
                'name': name,
                'journal_id': journal_petty_id,
                'company_id': rec.company_id.id,
                'ref': name,
                'date': date,
                'period_id': period_id,
                'partner_id': rec.company_id.partner_id.id,
                'division': rec.division,
            }
            move_id = move_obj.sudo().create(move_vals)
            move_line1 = {
                'name': _('Petty Cash Out'),
                'ref': name,
                'account_id': account_id,
                'move_id': move_id.id,
                'journal_id': journal_petty_id,
                'period_id': period_id,
                'date': date,
                'debit': 0.0,
                'credit': rec.amount,
                'company_id': rec.company_id.id,
                'division': rec.division,
                'partner_id': rec.company_id.partner_id.id,
            }
            move_line_obj.sudo().with_context(check_move_validity=False).create(move_line1)
            for line in rec.petty_cash_out_line_ids:
                default_name = line.name
                default_account_id = line.account_id.id

                move_line_2 = {
                    'name': default_name,
                    'ref': name,
                    'account_id': default_account_id,
                    'move_id': move_id.id,
                    'journal_id': journal_petty_id,
                    'period_id': period_id,
                    'date': date,
                    'debit': line.amount,
                    'credit': 0.0,
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
                'name': _(f'Interco Petty Cash Out {self.branch_destination_id.name}'),
                'ref': _(f'Interco Petty Cash Out {self.branch_destination_id.name}'),
                'account_id': inter_branch_header_account_id.id,
                'move_id': self.move_id.id,
                'journal_petty_id': self.journal_petty_id.id,
                'period_id': self.period_id.id,
                'date': self.date,
                'debit': debit,
                'credit': credit,
                'company_id': self.branch_destination_id.id,
                'division': self.division
            }
            move_line_obj.sudo().with_context(check_move_validity=False).create(move_line1)
            move_line_2 = {
                'name': _(f'Interco Petty Cash Out {self.company_id.name}'),
                'ref': _(f'Interco Petty Cash Out {self.company_id.name}'),
                'account_id': inter_branch_detail_account_id.id,
                'move_id': self.move_id.id,
                'journal_petty_id': self.journal_petty_id.id,
                'period_id': self.period_id.id,
                'date': self.date,
                'debit': credit,
                'credit': debit,
                'company_id': self.company_id.id,
                'division': self.division
            }
            move_line_obj.sudo().with_context(check_move_validity=False).create(move_line_2)
        
    def _get_to_post(self):
        return self.filtered(lambda r: r.state == 'draft')

