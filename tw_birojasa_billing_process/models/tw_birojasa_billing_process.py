from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError as Warning

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('confirmed', 'Confirmed'),
    ('done', 'Done'),
    ('cancel', 'Cancelled'),
]

class TwBirojasaBillingProcess(models.Model):
    _name = "tw.birojasa.billing.process"
    _description = "Tagihan Birojasa"
    _order = "name desc"

    @api.model
    def _default_tax_totals(self):
        currency = self.env.company.currency_id
        return self._empty_tax_totals(currency)

    name = fields.Char(string="Name", default='New', copy=False)
    confirm_date = fields.Datetime('Posted on')
    cancel_date = fields.Datetime('Cancelled on')
    document_date = fields.Date(string='Document Date', default=fields.Date.today())
    document_number = fields.Char('Document Number')
    description = fields.Char('Description')
    invoiced = fields.Boolean(string='Invoiced', copy=False)
    document_copy = fields.Boolean(string='Document Copy')
    approval_correction_amount = fields.Float(string='Approval Correction', digits='Product Price', compute='_get_amount', compute_sudo=True, store=True)
    estimation_amount = fields.Float(string='Estimation Total', digits='Product Price', compute='_get_amount', compute_sudo=True, store=True)
    correction_amount = fields.Float(string='Correction Total', digits='Product Price', compute='_get_amount', compute_sudo=True, store=True)
    service_tax_amount = fields.Float(string='Service Tax', digits='Product Price', compute='_compute_amounts', compute_sudo=True, store=True)
    progressive_tax_amount = fields.Float(string='Progressive Total', digits='Product Price', compute='_get_amount', compute_sudo=True, store=True)
    amount_untaxed = fields.Float(string='Amount Untaxed', digits='Product Price', compute='_compute_amounts', compute_sudo=True, store=True)
    amount_tax = fields.Float(string='Amount Tax', digits='Product Price', compute='_compute_amounts', compute_sudo=True, store=True)
    amount_total = fields.Float(string='Total Bills', digits='Product Price', compute='_compute_amounts', compute_sudo=True, store=True)
    document_file = fields.Binary(string="Document File")
    document_filename = fields.Char(string='Document Filename', required=False)
    notes = fields.Text(string="Notes", required=False)
    document_file = fields.Binary(string="Document File")
    document_filename = fields.Char(string='Document Filename', required=False)
    notes = fields.Text(string="Notes", required=False)
    
    state = fields.Selection(STATE_SELECTION, string='State', readonly=True, default='draft')
    type = fields.Selection(selection=[
            ('reg', 'REG'),
            ('adv', 'ADV')
        ], default='reg', string='Type')
    invoice_method = fields.Selection(selection=[
            ('order', 'Based on generated draft invoice')
        ], string='Invoicing Control', default='order')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options(), default='Unit')
    date = fields.Date(string='Date', default=fields.Date.today())
    tax_totals = fields.Binary(
        compute='_compute_tax_totals',
        exportable=False,
        default=lambda self: self._default_tax_totals()
    )

    company_id = fields.Many2one('res.company', string='Branch', domain=[('parent_id', '!=', False)], default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id.id)
    available_biro_jasa_ids = fields.Many2many('res.partner', compute='_compute_available_biro_jasa_ids')
    biro_jasa_id = fields.Many2one(comodel_name='res.partner', string='Biro Jasa', domain="[('id', 'in', available_biro_jasa_ids)]")
    billing_line_ids = fields.One2many('tw.birojasa.billing.process.line', 'birojasa_billing_id', string="Tagihan Birojasa Line")
    confirm_uid = fields.Many2one('res.users', string="Posted by")
    cancel_uid = fields.Many2one('res.users', string="Cancelled by")
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    currency_id = fields.Many2one(comodel_name='res.currency', compute='_get_currency', string='Currency',)
    invoice_id = fields.Many2one(comodel_name='account.move', string='Vendor Bill')
    done_uid = fields.Many2one('res.users', string='Done by')
    done_date = fields.Datetime(string='Done on')

    @api.depends('company_id')
    def _compute_available_biro_jasa_ids(self):
        for rec in self:
            if rec.company_id and rec.company_id.branch_setting_id:
                birojasa_settings = rec.company_id.branch_setting_id.birojasa_setting_ids
                rec.available_biro_jasa_ids = birojasa_settings.mapped('biro_jasa_id').ids
            else:
                rec.available_biro_jasa_ids = False

    @api.depends(
        'tax_ids',
        'billing_line_ids.service_amount',
        'billing_line_ids.amount_total',
        'billing_line_ids.estimation_amount',
        'billing_line_ids.correction_amount',
        'billing_line_ids.progressive_tax_amount',
    )
    def _get_amount(self):
        for rec in self:
            # Initialize all amounts
            approval_correction_amount = 0.0
            estimation_amount = 0.0
            correction_amount = 0.0
            progressive_tax_amount = 0.0

            # Sum all line values
            for line in rec.billing_line_ids:
                approval_correction_amount += line.correction_amount or 0.0
                estimation_amount += line.estimation_amount or 0.0
                correction_amount += line.correction_amount or 0.0
                progressive_tax_amount += line.progressive_tax_amount or 0.0

            # Update record values
            rec.update({
                'approval_correction_amount': approval_correction_amount,
                'estimation_amount': estimation_amount,
                'correction_amount': correction_amount,
                'progressive_tax_amount': progressive_tax_amount,
            })

    def _empty_tax_totals(self, currency):
        return {
            "currency_id": currency.id,
            "currency_pd": 0.0,
            "company_currency_id": currency.id,
            "company_currency_pd": 0.0,
            "has_tax_groups": False,
            "subtotals": [
                {
                    "tax_groups": [],
                    "tax_amount_currency": 0.0,
                    "tax_amount": 0.0,
                    "base_amount_currency": 0.0,
                    "base_amount": 0.0,
                    "name": "Untaxed Amount"
                }
            ],
            "base_amount_currency": 0.0,
            "base_amount": 0.0,
            "tax_amount_currency": 0.0,
            "tax_amount": 0.0,
            "same_tax_base": False,
            "total_amount_currency": 0.0,
            "total_amount": 0.0
        }

    def _baseline(self, rec, line, amount, taxes):
        return {
            'price_unit': float(amount or 0.0),
            'quantity': 1.0,
            'discount': 0.0,
            'tax_ids': taxes or rec.env['account.tax'].browse([]),  # harus field 'tax_ids'
            'product_id': False,
            'product_uom_id': False,
            'account_id': False,
            'display_type': False,
            'analytic_distribution': {},
            'is_refund': False,
            'special_mode': False,
            'manual_tax_amounts': False,
            'manual_total_excluded_currency': None,
            'manual_total_excluded': None,
            'filter_tax_function': False,
            'special_type': False,
            'rate': 1.0,
            'company_id': rec.company_id,
            'currency_id': rec.currency_id or rec.company_id.currency_id,
            'partner_id': rec.biro_jasa_id or False,
            'date': rec.document_date,
        }

    def _compute_totals_core(self, rec):
        """Bangun base_lines, jalankan tax pipeline Odoo, kembalikan (totals, currency)."""
        Tax = self.env['account.tax']
        currency = rec.currency_id or rec.company_id.currency_id or self.env.company.currency_id

        # Guard awal
        if not rec.company_id or not currency or not rec.biro_jasa_id:
            return (rec._empty_tax_totals(currency), currency)

        base_lines = []
        for line in rec.billing_line_ids:
            taxable_amt = float(line.service_amount or 0.0)
            non_taxable_amt = float(line.amount_total or 0.0) - taxable_amt

            if taxable_amt > 0.0:
                taxes = rec.tax_ids or self.env['account.tax'].browse([])
                base_lines.append(self._baseline(rec, line, taxable_amt, taxes))
            if non_taxable_amt > 0.0:
                base_lines.append(self._baseline(rec, line, non_taxable_amt, self.env['account.tax'].browse([])))

        if not base_lines:
            return (rec._empty_tax_totals(currency), currency)

        # Jalankan pipeline pajak standar
        Tax._add_tax_details_in_base_lines(base_lines, rec.company_id)
        Tax._round_base_lines_tax_details(base_lines, rec.company_id)
        totals = Tax._get_tax_totals_summary(
            base_lines=base_lines,
            currency=currency,
            company=rec.company_id,
        ) or {}

        # Pastikan key selalu ada
        totals.setdefault('base_amount', 0.0)
        totals.setdefault('tax_amount', 0.0)
        totals.setdefault('total_amount', 0.0)

        return (totals, currency)

    @api.depends_context('lang')
    @api.depends(
        'billing_line_ids.service_amount',
        'billing_line_ids.amount_total',
        'currency_id', 'company_id', 'biro_jasa_id', 'tax_ids'
    )
    def _compute_tax_totals(self):
        for rec in self:
            currency = rec.currency_id or rec.company_id.currency_id or self.env.company.currency_id
            totals, _currency = rec._compute_totals_core(rec)
            rec.tax_totals = totals or rec._empty_tax_totals(currency)

    @api.depends(
        'billing_line_ids.service_amount',
        'billing_line_ids.amount_total',
        'currency_id', 'company_id', 'biro_jasa_id', 'tax_ids'
    )
    def _compute_amounts(self):
        """HANYA menulis field stored (angka-angka). Terpisah dari tax_totals."""
        for rec in self:
            totals, _currency = rec._compute_totals_core(rec)
            rec.amount_untaxed = float(totals.get('base_amount', 0.0) or 0.0)
            rec.amount_tax = float(totals.get('tax_amount', 0.0) or 0.0)
            rec.service_tax_amount = float(totals.get('tax_amount', 0.0) or 0.0)
            rec.amount_total = float(totals.get('total_amount', 0.0) or 0.0)

    @api.depends('biro_jasa_id', 'company_id')
    def _get_currency(self):
        for rec in self:
            rec.currency_id = rec.biro_jasa_id.currency_id.id or rec.company_id.currency_id.id
    
    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('company_id') and values.get('name', 'New') == _('New'):
                branch_src = self.env['res.company'].suspend_security().search([
                    ('id', '=', values['company_id'])
                ], limit=1)
                values['name'] = self.env['ir.sequence'].get_sequence_code('PRBJ', str(branch_src.code))
        res = super().create(vals_list)
        res._validate_order()
        return res

    def write(self, vals):
        res = super(TwBirojasaBillingProcess, self).write(vals)
        self._validate_order()
        return res

    @api.ondelete(at_uninstall=False)
    def _unlink_except_draft(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_("You cannot delete data that is not in draft status."))

    def action_confirm(self):
        for rec in self.filtered(lambda r: r.state == self.get_state()):
            invoice_id = rec.action_create_invoice()
            rec.write({
                'state': 'confirmed',
                'confirm_uid': self.env.user.id,
                'confirm_date': datetime.now()
            })
            for line in rec.billing_line_ids:
                line.lot_id.write({
                    'birojasa_billing_id': rec.id,
                    'birojasa_billing_date': rec.date,
                })

    def action_cancel(self):
        for rec in self:
            if rec.state == 'done':
                raise ValidationError(_('Cannot cancel a billing process that is already done.'))
            rec.write({
                'state': 'cancel',
                'cancel_uid': self.env.user.id,
                'cancel_date': datetime.now(),
            })
            rec.billing_line_ids.action_cancel()
    
    def action_done(self):
        """Mark billing process as done when invoice is paid."""
        for rec in self:
            if rec.state != 'confirmed':
                raise ValidationError(_('Only confirmed billing process can be marked as done.'))
            if not rec.invoice_id:
                raise ValidationError(_('No invoice found for this billing process.'))
            if rec.invoice_id.payment_state != 'paid':
                raise ValidationError(_('Invoice must be fully paid before marking as done.'))
            
            rec.write({
                'state': 'done',
                'done_uid': self.env.user.id,
                'done_date': datetime.now(),
            })
        return True

    def action_print_out_birojasa(self):
        self.ensure_one()

        return self.env.ref('tw_birojasa_billing_process.action_print_out_birojasa').report_action(self)

    def _validate_order(self):
        for rec in self:
            if not rec.billing_line_ids:
                raise ValidationError(_('Please input engine line.'))
            for line in rec.billing_line_ids:
                other_line_id = self.env['tw.birojasa.billing.process.line'].search([
                    ('lot_id', '=', line.lot_id.id),
                    ('id', '!=', line.id),
                    ('birojasa_billing_id.state', '!=', 'cancel'),
                ], limit=1)
                if other_line_id:
                    raise ValidationError(_(f'Engine number {line.lot_id.name} has been processed in'
                                            f' {other_line_id.birojasa_billing_id.name}.'))

    def action_view_invoice(self):
        action = self.env.ref('account.action_move_in_invoice').sudo().read()[0]
        action['views'] = [(False, 'form')]
        action['res_id'] = self.invoice_id.id
        return action

    def action_create_invoice(self):
        """
        Create vendor bill with:
        - Estimation & Difference per lot (non-taxed)
        - Aggregated service (taxed only on this line)
        (Without accrual reconciliation)
        """
        self.ensure_one()

        # Get configuration
        account_setting = self._get_branch_config()
        journal_birojasa, journal_progressive, bbn_debit_acc, bbn_credit_acc = self._get_journals_and_accounts(account_setting)
        self._validate_business_rules()

        # Initialize values
        invoice_line_vals = []
        to_reconcile_accrual_lines = self.env['account.move.line']
        total_service = 0.0
        move_line_obj = self.env['account.move.line']
        partner_id = self.biro_jasa_id.id

        # Process each billing line
        for line in self.billing_line_ids:
            lot = line.lot_id
            if not lot:
                continue

            # Get estimation account from lot's accrual or use default BBN account
            est_account = bbn_credit_acc
            if hasattr(lot, 'accrue_bbn_move_line_ids') and lot.accrue_bbn_move_line_ids:
                accrual_lines = move_line_obj.search([
                    ('id', 'in', lot.accrue_bbn_move_line_ids.ids),
                    ('partner_id', '=', partner_id),
                ])
                
                if not accrual_lines:
                    raise Warning('Accrual BBN beli untuk nomor mesin %s tidak ditemukan'%lot.name)
                else:
                    est_account = accrual_lines[0].account_id
                    to_reconcile_accrual_lines += accrual_lines

            # Accumulate service amount
            total_service = line.service_amount or 0.0
            # Calculate difference (progressive tax + correction)
            difference = (line.progressive_tax_amount or 0.0) + (line.correction_amount or 0.0)
            
            # Add estimation line
            invoice_line_vals.append((0, 0, {
                'name': f'Total Estimasi {lot.name}',
                'account_id': est_account.id,
                'quantity': 1,
                'sequence': 1,
                'price_unit': line.estimation_amount - total_service,
            }))

            # Add difference line if exists
            if difference:
                invoice_line_vals.append((0, 0, {
                    'name': f'Total Selisih {lot.name}',
                    'account_id': bbn_debit_acc.id,
                    'quantity': 1,
                    'sequence': 3,
                    'price_unit': difference,
                }))

            # Add service line with taxes
            # Gunakan est_account (accrual - liability_current) bukan bbn_credit_acc
            # agar tidak melanggar Odoo 18 constraint (liability_payable tidak boleh di product line).
            # Akun payable `21210306 Hutang Dagang Birojasa` akan otomatis di-generate
            # oleh Odoo sebagai payment_term line via property_account_payable_id partner.
            if total_service:
                invoice_line_vals.append((0, 0, {
                    'name': f'Total Estimasi Jasa {lot.name}',
                    'account_id': est_account.id,
                    'quantity': 1,
                    'sequence': 2,
                    'price_unit': total_service,
                    'tax_ids': [(6, 0, self.tax_ids.ids)],
                }))

        # Prepare and create move
        move_vals = {
            'move_type': 'in_invoice',
            'partner_id': self.biro_jasa_id.id,
            'invoice_date': self.date,
            'date': self.date,
            'ref': self.name,
            'division': self.division,
            'journal_id': journal_birojasa.id,
            'currency_id': self.currency_id.id or self.company_id.currency_id.id,
            'invoice_line_ids': invoice_line_vals,
            'company_id': self.company_id.id,
        }

        # Create and post the move
        move = self.env['account.move'].suspend_security().with_company(self.company_id).create(move_vals)
        move.suspend_security().with_company(self.company_id).action_post()
        to_reconcile_prbj_lines = move.line_ids.filtered(lambda l: l.account_id.id == est_account.id)
        (to_reconcile_accrual_lines | to_reconcile_prbj_lines).reconcile()

        # Update references
        self.invoice_id = move.id
        self.invoiced = True

        return move

    def _get_branch_config(self):
        """Get branch configuration with proper error handling"""
        setting = self.env['tw.branch.setting'].search(
            [('company_id', '=', self.company_id.id)], 
            limit=1
        )
        if not setting or not setting.account_setting_id:
            raise Warning(_(
                'Please define Journal in Setup Division for this branch: "%s"'
            ) % self.company_id.name)
        return setting.account_setting_id

    def _get_journals_and_accounts(self, account_setting):
        """Get journals and accounts with validation"""
        journal_birojasa = account_setting.journal_birojasa_bbn_id

        bbn_debit_acc = journal_birojasa.default_debit_account_id or journal_birojasa.default_account_id
        bbn_credit_acc = journal_birojasa.default_credit_account_id or journal_birojasa.default_account_id
        
        if not bbn_debit_acc or not bbn_credit_acc:
            raise Warning(_(
                'Account BBN debit/credit belum diisi di Journal %s'
            ) % journal_birojasa.display_name)
            
        return journal_birojasa, False, bbn_debit_acc, bbn_credit_acc

    def _validate_business_rules(self):
        """Validate all business rules before creating invoice"""
        if self.amount_total <= 0:
            raise Warning(_('Total amount must be greater than 0.'))
        if not self.biro_jasa_id:
            raise Warning(_('Vendor (Biro Jasa) is required.'))
        if not self.billing_line_ids:
            raise Warning(_('No billing lines found.'))
        if self.invoice_id:
            raise Warning(_('An invoice already exists for this record.'))
        
        for line in self.billing_line_ids:
            if not line.lot_id.registration_process_date:
                raise Warning(_(f'Engine number {line.lot_id.name} has not been processed (Proses STNK).'))
    
    def get_state(self):
        return 'draft'
    
    def _check_invoice_paid_and_update(self):
        """Check if invoice is paid and auto-update to done."""
        for rec in self:
            if rec.state == 'confirmed' and rec.invoice_id and rec.invoice_id.payment_state == 'paid':
                rec.action_done()