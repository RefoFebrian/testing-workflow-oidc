# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.tools import SQL
from odoo.exceptions import UserError as Warning

# 5: local imports
from odoo.addons.tw_base.models.amount_to_text import convert

# 6: Import of unknown third party lib

#? Inherit odoo default account.payment to change its description
class InheritAccountPayment(models.Model):
    _inherit = "account.payment"
    _description = "Account Payment (Odoo Default)"

    origin = fields.Char(string='Origin')
    payment_transaction_id = fields.Many2one('payment.transaction', 'Payment Transaction', copy=False)
    payment_transaction_status = fields.Selection(related='payment_transaction_id.state', string='Payment Status')

class TWInheritAccountPayment(models.Model):
    _name = "tw.account.payment"
    _description = "Account Payment"
    _inherit = ["account.payment", "tw.attachment.mixin"]

    # 7: Default Method
    
    # 8: fields
    type = fields.Selection([
        ('receive_payment', 'Receive Payment'),
        ('customer_payment', 'Customer Payment'),
        ('supplier_payment', 'Supplier Payment')
    ], string='Type')

    state = fields.Selection(
        compute=False,
        selection_add=[
            ('paid','Posted')
        ], 
        ondelete={
            'paid': 'set default',
        }
    )
    
    is_round = fields.Boolean('Pembulatan')
    schedule_date = fields.Date('Schedule Date')
    due_date = fields.Date('Due Date')
    is_receipt_printed = fields.Boolean('Cetak Kwitansi', default=False, help="Formerly known as 'kwitansi'")
    receipt_print_count = fields.Integer('Cetak Kwitansi ke',default=0)
    
    narration = fields.Text('Notes')
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    payment_receipt_title = fields.Char(compute='_compute_payment_receipt_title')
    document_number = fields.Char('Document Number')
    document_date = fields.Date('Document Date')

    writeoff_amount = fields.Float(string='Difference Amount', compute ='_compute_writeoff_amount', store=True)
    amount_text = fields.Char(string='Terbilang', compute='_get_amount_text')
    amount_untaxed = fields.Monetary(string='Amount Untaxed',currency_field='currency_id', compute='_compute_amount_total')
    amount_tax = fields.Monetary(string='Amount Tax',currency_field='currency_id', compute='_compute_amount_total')
    amount_total = fields.Monetary(string='Amount Total',currency_field='currency_id', compute='_compute_amount_total')

    account_number = fields.Char('Account Number')
    account_holder = fields.Char('Account Holder')
    transfer_note = fields.Char('Transfer Note',compute='_compute_transfer_note',precompute=True,store=True)

    # == Display purpose fields ==
    payment_method = fields.Char(related='payment_method_id.code', string='Payment Method Code')
    payment_provider = fields.Char(related='payment_method_line_id.payment_provider_id.name', string='Payment Provider')

    # used to know whether the field `partner_bank_id` needs to be displayed/required or not in the payments form views
    show_partner_bank_account = fields.Boolean(compute='_compute_show_require_partner_bank')
    show_account_number = fields.Boolean(compute='_compute_show_require_partner_bank')
    require_partner_bank_account = fields.Boolean(compute='_compute_show_require_partner_bank')
    require_account_number = fields.Boolean(compute='_compute_show_require_partner_bank')
    
    # Audit Trail
    confirm_uid = fields.Many2one('res.users',string="Confirmed by")
    confirm_date = fields.Datetime('Confirmed on')
    validate_uid = fields.Many2one('res.users',string="Validated by")
    validate_date = fields.Datetime('Validated on')

    # 9: relation fields
    available_account_ids = fields.Many2many(comodel_name='account.account',compute='_compute_available_account_ids')
    available_journal_ids = fields.Many2many(comodel_name='account.journal',compute='_compute_available_journal_ids')
    available_acc_payment_method_ids = fields.Many2many(comodel_name='account.payment.method', compute='_compute_available_acc_payment_method_ids')
    company_id = fields.Many2one('res.company', 'Branch', compute=False, precompute=False, index=False, required=True, domain="[('parent_id', '!=', False)]", default=lambda self: self.env.company if self.env.company.parent_id else False)
    beneficiary_company_id = fields.Many2one('res.company', 'Beneficiary Branch', index=True, domain="[('parent_id', '!=', False)]", default=lambda self: self.env.company if self.env.company.parent_id else False)
    bank_id = fields.Many2one('res.bank', string='Bank')
    move_id = fields.Many2one('account.move', 'Account Entry', copy=False)
    account_id = fields.Many2one('account.account', string='Account')
    journal_id = fields.Many2one('account.journal', string='Journal', domain="[('id', 'in', available_journal_ids)]", help="Formerly known as 'payment method', this field is used for selecting an Account Journal. Extra Note: Now the 'payment method' field is used to select a real payment method")
    payment_method_id = fields.Many2one('account.payment.method', string="Method", domain="[('id', 'in', available_acc_payment_method_ids)]", related='', help="Real 'payment method', this field is used for selecting a payment method not like the previous odoo version when it was used to select a Journal")
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    partner_bank_id = fields.Many2one('res.partner.bank', string="Rekening Penerima",readonly=False, store=True, tracking=True, compute='_compute_partner_bank_id', domain="[('id', 'in', available_partner_bank_ids)]", check_company=True, ondelete='restrict',)
    partner_id = fields.Many2one('res.partner',string="Customer/Vendor",store=True, readonly=False, ondelete='restrict',compute='_compute_partner_id',precompute=True,domain="[]",tracking=True,check_company=False)
    move_ids = fields.One2many(related='move_id.line_ids', string='Journal Items', readonly=True)
    line_ids = fields.One2many('tw.account.payment.line','payment_id','Line', context={'default_type':'cr'})
    line_cr_ids = fields.One2many('tw.account.payment.line','payment_id','Credits',domain=[('type','=','cr')], context={'default_type':'cr'})
    line_dr_ids = fields.One2many('tw.account.payment.line','payment_id','Debits',domain=[('type','=','dr')], context={'default_type':'dr'})
    line_wo_ids = fields.One2many('tw.account.payment.line','payment_id','Writeoff',domain=[('type','=','wo')], context={'default_type':'wo'})    
    invoice_ids = fields.Many2many('account.move', string="Invoices", relation='account_move_tw_account_payment', column1='payment_id', column2='invoice_id',) # contains the invoice even if they don't have a journal entry and are not reconciled
    duplicate_payment_ids = fields.Many2many('tw.account.payment', compute='_compute_duplicate_payment_ids')
    source_payment_id = fields.Many2one(comodel_name='tw.account.payment',related=False)
    attachment_ids = fields.One2many('tw.attachment', 'res_id', string='Attachments',domain="[('res_model', '=', 'tw.account.payment')]")
    
    # 10: constraints & sql constraints
    @api.constrains('state', 'move_id')
    def _check_move_id(self):
        for payment in self:
            if (
                payment.state not in payment._get_unconfirmed_states()
                and not payment.move_id
                and payment.outstanding_account_id
            ):
                raise ValidationError(_("A payment with an outstanding account cannot be confirmed without having a journal entry."))

    # 11: compute/depends & on change methods
    @api.depends('company_id','type')
    def _compute_available_account_ids(self):
        for record in self:
            domain = [('company_ids', 'parent_of', record.company_id.id)]
            payment_type = record.type or record.payment_type
            account_filter_domain = self.env['tw.account.filter'].get_account_domain(payment_type)
            if account_filter_domain:
                domain += account_filter_domain
            accounts = self.env['account.account'].sudo().search(domain)
            record.available_account_ids = accounts
    
    @api.depends('payment_type','company_id')
    def _compute_available_journal_ids(self):
        """
        Get all journals having at least one payment method for inbound/outbound depending on the payment_type.
        """
        for pay in self:
            journals = self.env['account.journal'].search([
                ('company_id', 'in', self.env.companies.ids),
                ('type', 'in', self._get_available_journal_type()),
            ])
            if pay.payment_type == 'inbound':
                pay.available_journal_ids = journals.filtered('inbound_payment_method_line_ids')
            else:
                pay.available_journal_ids = journals.filtered('outbound_payment_method_line_ids')
    
    @api.depends('payment_type')
    def _compute_available_acc_payment_method_ids(self):
        """
        Get all journals having at least one payment method for inbound/outbound depending on the payment_type.
        """
        for pay in self:
            domain_account_payment_method = pay._get_domain_account_payment_method()
            account_payment_method_ids = self.env['account.payment.method'].sudo().search(domain_account_payment_method)
            pay.available_acc_payment_method_ids = account_payment_method_ids
            
    @api.depends('move_id.name', 'state', 'company_id', 'journal_id', 'payment_type')
    def _compute_name(self):
        for payment in self:
            if payment.id and not payment.name and payment.state:
                seq_name = payment._get_sequence_name()
                payment.name = seq_name
    
    @api.depends('line_ids','line_ids.amount','line_ids.tax_ids')
    def _compute_amount_total(self):
        for record in self:
            total_untaxed = 0
            total_tax = 0
            total_amount = 0
            for line in record.line_ids:
                amount = line.amount
                amount_untaxed = line.amount
                amount_tax = 0
                if line.tax_ids:
                    computed_tax = line.tax_ids.compute_all(amount,line.currency_id)
                    amount_untaxed = computed_tax.get('total_void',0)
                    amount_tax = computed_tax.get('total_included',0) - computed_tax.get('total_excluded',0)
                    amount = amount_untaxed + amount_tax
                
                total_untaxed += amount_untaxed
                total_tax += amount_tax
                total_amount += amount

            record.amount_untaxed = total_untaxed
            record.amount_tax = total_tax
            record.amount_total = total_amount
    
    @api.depends('journal_id','account_number','account_holder')
    def _compute_transfer_note(self):
        for record in self:
            transfer_note = ''
            if record.journal_id:
                transfer_note += record.journal_id.bank_account_id.code if record.journal_id.bank_account_id.code else ''
                transfer_note += ' '
            if record.account_number:
                transfer_note += record.account_number
                transfer_note += ' '
            if record.account_holder:
                transfer_note += record.account_holder
                transfer_note += ' '
            
            record.transfer_note = transfer_note

    @api.depends('amount','line_dr_ids','line_cr_ids','line_wo_ids','writeoff_amount')
    def _compute_writeoff_amount(self):
        for record in self:
            currency_obj = record.env['res.currency']
            res = {}
            debit = credit = writeoff = 0.0
            sign = record.payment_type == 'outbound' and -1 or 1
            for l in record.line_dr_ids:
                debit += l.amount
            for l in record.line_cr_ids:
                credit += l.amount
            for l in record.line_wo_ids :
                writeoff += l.amount
            record.writeoff_amount = record.amount - (sign * (credit - debit)) - writeoff

    @api.depends('payment_method_id')
    def _compute_show_require_partner_bank(self):
        """ Computes if the destination bank account must be displayed in the payment form view. By default, it
        won't be displayed but some modules might change that, depending on the payment type."""
        for payment in self:
            if payment.payment_method_id.is_require_bank_account:
                payment.show_partner_bank_account = True
            else:
                payment.show_partner_bank_account = False
            
            if payment.payment_method_id.is_require_account_number:
                payment.show_account_number = True
            else:
                payment.show_account_number = False
            
            payment.require_partner_bank_account = payment.state == 'draft' and payment.show_partner_bank_account
            payment.require_account_number = payment.state == 'draft' and payment.show_account_number

    @api.depends('available_partner_bank_ids', 'journal_id','show_partner_bank_account')
    def _compute_partner_bank_id(self):
        ''' The default partner_bank_id will be the first available on the partner. '''
        for pay in self:
            if not pay.show_partner_bank_account:
                pay.partner_bank_id = False
            else:   
                if pay.partner_bank_id not in pay.available_partner_bank_ids:
                    pay.partner_bank_id = pay.available_partner_bank_ids[:1]._origin

    @api.depends('move_id.line_ids.matched_debit_ids', 'move_id.line_ids.matched_credit_ids')
    def _compute_stat_buttons_from_reconciliation(self):
        ''' Retrieve the invoices reconciled to the payments through the reconciliation (account.partial.reconcile). '''
        #? Turn off stat buttons, because we don't need it
        self.reconciled_invoice_ids = False
        self.reconciled_invoices_count = 0
        self.reconciled_invoices_type = False
        self.reconciled_bill_ids = False
        self.reconciled_bills_count = 0
        self.reconciled_statement_line_ids = False
        self.reconciled_statement_lines_count = 0
        return

    @api.depends('partner_id', 'amount', 'date', 'payment_type')
    def _compute_duplicate_payment_ids(self):
        """ Retrieve move ids with same partner_id, amount and date as the current payment """
        payment_to_duplicate_move = self._fetch_duplicate_reference()
        for payment in self:
            # Uses payment._origin.id to handle records in edition/existing records and 0 for new records
            payment.duplicate_payment_ids = payment_to_duplicate_move.get(payment._origin.id, self.env[self._name])
    
    @api.depends('journal_id')
    def _compute_company_id(self):
        #? We dont use this compute method. Override it to avoid unnecessary changes on company
        pass
    
    @api.depends('company_id', 'partner_id')
    def _compute_journal_id(self):
        #? We dont use this compute method. Its automaticly change the journal used in the payment.
        #? We override it to make default journal based on menu AND to enable journal selection
        pass
            
    def _compute_payment_receipt_title(self):
        """ To override in order to change the title displayed on the payment receipt report """
        self.payment_receipt_title = _('Bukti Pembayaran')
    
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

    @api.depends('amount')
    def _get_amount_text(self):
        for payment in self:
            terbilang = convert(payment.amount)
            payment.amount_text = terbilang

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.beneficiary_company_id = False
        if self.company_id:
            self.beneficiary_company_id = self.company_id.id
    
    @api.onchange('company_id')
    def _onchange_company_journal_id(self):
        if self.company_id:
            self.journal_id = self._get_default_journal_id()
        else:
            self.journal_id = False
    
    @api.onchange('partner_bank_id')
    def _onchange_partner_bank_id(self):
        if self.partner_bank_id:
            self.account_number = self.partner_bank_id.acc_number
            self.account_holder = self.partner_bank_id.acc_holder_name
        else:
            self.account_number = False
            self.account_holder = False
    
    @api.onchange('partner_id')
    def _onchange_partner_id_payment_term(self):
        if self.partner_id and self.partner_id.property_supplier_payment_term_id:
            payment_term = self.partner_id.property_supplier_payment_term_id
            date_ref = fields.Date.today()
            currency = self.currency_id or self.company_id.currency_id
            
            # Compute terms using Odoo 18's _compute_terms method
            terms = payment_term._compute_terms(
                date_ref=date_ref,
                currency=currency,
                company=self.company_id,
                tax_amount=0,
                tax_amount_currency=0,
                sign=1,
                untaxed_amount=self.amount_total or 0,
                untaxed_amount_currency=self.amount_total or 0
            )
            
            # Get the latest payment date from the computed terms
            if terms:
                payment_dates = [term['date'] for term in terms.get('line_ids') if term and 'date' in term]
                if payment_dates:
                    self.schedule_date = max(payment_dates)
                    return
            # Fallback to today's date if no valid terms found
            self.schedule_date = date_ref
        else:
            self.schedule_date = False

    @api.onchange('payment_method_id')
    def _onchange_payment_method_id(self):
        self.available_payment_method_line_ids = self.journal_id._get_available_payment_method_lines(self.payment_type)
        self.partner_bank_id = False
        self.bank_id = False
        self.account_number = False
        self.account_holder = False
        self.payment_method_line_id = False
        if self.payment_method_id and self.journal_id:
            if self.available_payment_method_line_ids:
                new_available_payment_method_line_ids = []
                for payment_method_line_obj in self.available_payment_method_line_ids:
                    if 'manual' in payment_method_line_obj.name.lower():
                        new_available_payment_method_line_ids.append(payment_method_line_obj.id)
                    else:
                        if payment_method_line_obj.payment_provider_id:
                            payment_method_ids = payment_method_line_obj.payment_provider_id.payment_method_ids.filtered(lambda pm: pm.code == self.payment_method_id.code)
                            if payment_method_ids:
                                new_available_payment_method_line_ids.append(payment_method_line_obj.id)

                self.available_payment_method_line_ids = new_available_payment_method_line_ids
                if self.available_payment_method_line_ids:
                    if len(self.available_payment_method_line_ids) <= 1:
                        self.payment_method_line_id = self.available_payment_method_line_ids.id
                    else:
                        self.payment_method_line_id = self.available_payment_method_line_ids.filtered(lambda x: x.code == self.payment_method_id.code).id

    @api.onchange('payment_method_line_id')
    def _onchange_payment_method_line_id(self):
        if not self.payment_method_id and self.type == 'customer_payment':
            self.payment_method_line_id = False
    
    @api.onchange('beneficiary_company_id')
    def _onchange_beneficiary_company_id(self):
        self._reset_line()
    
    @api.onchange('partner_id')
    def _onchange_reset_on_partner_id(self):
        self._reset_line()

    @api.onchange('division')
    def _onchange_reset_on_division(self):
        self._reset_line()
    
    @api.onchange('company_id')
    def _onchange_reset_on_company_id(self):
        self._reset_line()
    
    
    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        payments = super().create(vals_list)
        return payments
    
    def write(self, vals):
        payment = super().write(vals)
        if self.state != 'draft' and not self.line_cr_ids and not self.line_dr_ids and not self.line_wo_ids:
            raise Warning(_("You must add at least one payment detail."))
        
        return payment
    
    def unlink(self):
        for payment in self:
            if payment.state != 'draft':
                raise Warning('Hanya payment draft yang bisa di hapus.')
        return super().unlink()
    
    def copy_data(self, default=None):
        default = dict(default or {})
        vals_list = super().copy_data(default)
        for payment, vals in zip(self, vals_list):
            vals.update({
                'date': fields.Date.today(),
                'confirm_uid': False,
                'confirm_date': False,
                'validate_uid': False,
                'validate_date': False,
                'state': 'draft',
            })
        return vals_list

    # 13: action methods
    def action_post(self):
        payment_obj = self.with_company(self.company_id)
        payment_obj._validate_amount()
        payment_obj.write({
            'confirm_uid':self._uid,
            'confirm_date':datetime.now()
        })
        post = super(TWInheritAccountPayment, payment_obj).action_post()
        if not self.payment_method_id.code in self._get_payment_method_need_process():
            payment_obj.action_validate()
        return post
    
    def action_validate(self):
        if self.validate_date:
            raise Warning(_("Transaksi telah dilakukan Validasi pada (%s)."%(self.validate_date)))
        
        payment_obj = self.with_company(self.company_id)
        payment_obj._validate_amount()
        if payment_obj.state == 'paid':
            raise Warning('Payment already validated.')
        payment_obj._create_account_move()
        super(TWInheritAccountPayment, payment_obj).action_validate()
        payment_obj._post_reconcilled_bills()
        payment_obj.write({
            'state': 'paid',
            'validate_uid': self._uid,
            'validate_date': datetime.now()
        })
    
    def action_open_business_doc(self):
        return {
            'name': _("Payment"),
            'type': 'ir.actions.act_window',
            'views': [(False, 'form')],
            'res_model': 'tw.account.payment',
            'res_id': self.id,
        }
    
    def action_print_pdf(self):
        self.ensure_one()
        return self.env.ref('tw_payment.action_report_tw_payment').sudo().report_action(self.id)
    
    def action_print_customer_payment(self):
        self.ensure_one()
        return self.env.ref('tw_payment.action_report_tw_customer_payment').sudo().report_action(self.id)
    
    def action_print_supplier_payment(self):
        self.ensure_one()
        return self.env.ref('tw_payment.action_report_tw_supplier_payment').sudo().report_action(self.id)
    
    def action_print_kwitansi(self):
        self.ensure_one()

        report_action = self.env.ref('tw_payment.action_report_tw_payment_kwitansi').sudo().report_action(self.id)
        report_action['close_on_report_download'] = True

        return report_action
    
    def action_update_amount(self):
        return True
    
    # 14: private methods
    def _reset_line(self):
        self.line_ids = False
        self.line_cr_ids = False
        self.line_dr_ids = False
        self.line_wo_ids = False
    
    def _get_sequence_name(self):
        if self.type == 'receive_payment':
            seq_name = self.env['ir.sequence'].with_company(self.company_id).get_sequence_code('HL', self.company_id.code)
        elif self.payment_type == 'inbound' and self.company_id:
            seq_name = self.env['ir.sequence'].with_company(self.company_id).get_sequence_code('AR',self.company_id.code)
        elif self.payment_type == 'outbound' and self.company_id:
            seq_name = self.env['ir.sequence'].with_company(self.company_id).get_sequence_code('PV',self.company_id.code)
        else:
            seq_name = (
            self.move_id.name
            or self.env['ir.sequence'].with_company(self.company_id).next_by_code(
                self._name,
                sequence_date=self.date,
            )
        )
        return seq_name
    
    def _get_default_journal_id(self):
        return self.env['account.journal'].search([
            *self.env['account.journal']._check_company_domain(self.company_id),
            ('type', 'in', ['bank', 'cash', 'credit']),
        ], limit=1).id
    
    def _get_domain_account_payment_method(self):
        return [('payment_type','=',self.payment_type)]
    
    def _get_payment_method_need_process(self):
        return []

    def _validate_amount(self):
        if not self.line_ids:
            raise Warning(_("You must have at least 1 line of payment."))

        total_cr = sum(line.amount_included for line in self.line_cr_ids)
        total_dr = sum(line.amount_included for line in self.line_dr_ids)
        total_wo = sum(line.amount_included for line in self.line_wo_ids)
        total_amount = total_cr - total_dr - total_wo
        branch_type = self.company_id.branch_type_id
        jtype = self.journal_id.type
        # ?INFO: commended because cant paid when amount is 0 on DSO. Also, when paid using HL, the amount is 0
        # if self.amount == 0:
        #     raise Warning(_("Validation Failed : The value of the payment cannot be 0."))
        if total_cr == 0 and total_dr == 0 and total_wo == 0:
            raise Warning(_("Validation Failed : The value of the payment cannot be 0."))
        if total_cr <0:
            raise Warning(_("Validation Failed : Total credit amount cannot be less than 0."))
        if total_dr <0:
            raise Warning(_("Validation Failed : Total debit amount cannot be less than 0."))
        
        # Check on draft only
        if self.state == 'draft':
            if self.schedule_date and self.schedule_date < datetime.today().date():
                raise Warning(_("Validation Failed : Schedule date cannot be less than today"))
            if self.due_date and self.due_date < datetime.today().date():
                raise Warning(_("Validation Failed : Due date cannot be less than today"))

        #? Check duplikat
        aml_ids = []
        for line in self.line_ids:
            if line.move_line_id:
                if line.move_line_id.id in aml_ids:
                    raise Warning(_("Validation Failed : Ditemukan ID duplikat (%s) silahkan hapus salah 1 nya."%(line.move_line_id.name)))
                if line.move_line_id.move_id.state != 'posted':
                    raise Warning(_("Validation Failed : Invoice %s belum posted"%line.move_line_id.move_id.name))
                if line.move_line_id.reconciled:
                    raise Warning(_("Validation Failed : Invoice %s sudah ter reconcile, silahkan cek kembali."%line.move_line_id.move_id.name))
                aml_ids.append(line.move_line_id.id)

                if line.amount > line.amount_unreconciled:
                    raise Warning(_("Validation Failed : Nilai amount tidak boleh melebihi nilai invoice."))
        
        rounding = self.is_round

        acc, max_rounding = self._get_rounding_configuration() if rounding else (None, 0)

        max_rounding = int(float(max_rounding))
        sign = self.payment_type == 'outbound' and -1 or 1
        diff = self.amount - (sign * (total_cr - total_dr)) - total_wo

        if abs(diff) > max_rounding:
            raise Warning(_(f"Validation Failed : Terdapat perbedaan amount {self.currency_format(diff)}. Amount bayar {self.currency_format(self.amount)} amount detail {self.currency_format(total_amount*sign)} Silahkan cek kembali."))
        
        if self.payment_type in ('payment'):

            if jtype == 'bank' and self.amount > 0.0 and total_cr + total_dr == 0.0 and total_wo != 0.0 and diff == 0.0:
                # input bank fee
                return True
            if self.amount > 0.0 and total_dr > 0 and total_cr == 0.0 and (diff != 0.0 and rounding or diff == 0.0):
                # input debt payment
                return True

            if branch_type.name == 'HO' and self.amount > 0.0 and total_dr > 0.0 and total_cr > 0.0 and (diff != 0.0 and rounding or diff == 0.0):
                # input debt payment with DP
                return True
            if branch_type.name == 'HO' and self.amount > 0.0 and total_cr + total_dr == 0.0 and total_wo == 0.0 and diff > 0.0 and not rounding:
                # input DP payment
                return True

            if jtype != 'bank' and self.amount > 0.0 and total_cr + total_dr == 0.0 and total_wo != 0.0 and diff == 0.0:
                raise Warning(_("Validation Failed : This input is only for bank Payment Method."))
            if diff != 0.0 and not rounding:
                raise Warning(_("Validation Failed : Difference Amount: Rp {diff:,.2f}. Except for rounding, it must be Rp 0."))
            if branch_type.value != 'HO' and total_cr > 0.0:
                raise Warning(_("Validation Failed : Transactions with Credits can only be done by Head Office."))
            raise Warning(_("Validation Failed : Please check your input again."))
        
        validated_type = self._get_validate_type()
        if self.type in validated_type:
            # in previous teds the total amount verification is done for hutang lain (receive_payment?)
            if self.type == 'receive_payment' and total_amount != self.amount:
                raise Warning(_("Validation Failed : The total amount of the payment lines must be equal to the payment amount."))
        else:
            raise Warning(_("Validation Failed : Undefined payment type. Please contact IT Administrator."))

        return True
    
    def _get_available_journal_type(self):
        return ['bank', 'cash', 'credit']

    def _get_validate_type(self):
        return ['receive_payment', 'customer_payment', 'supplier_payment']
    
    def _get_unconfirmed_states(self):
        return ('draft', 'in_process')
    
    def _get_to_check_duplicate_states(self):
        return ('draft', 'in_process')
    
    def _update_amount_based_on_total_amount(self):
        # Give the original method for clear inheritance, used in other receivable
        pass

    def _create_account_move(self):
        if self.move_id:
            raise Warning(_("Payment already posted or Journal Entry already created."))
        
        move_vals = {
            'move_type': 'entry',
            'ref': self.name,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'division': self.division,
            'partner_id': self.partner_id.id,
            'currency_id': self.currency_id.id or self.company_id.currency_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            'line_ids': [
                Command.create(line_vals)
                for line_vals in self._prepare_move_line_default_vals()
            ],
        }
        if self.name:
            move_vals['name'] = self.name
        move_created = self.env['account.move'].suspend_security().with_context({'company_id': self.company_id.id}).create([move_vals])
        move_created.sudo().action_post()
        
        self.write({'move_id': move_created.id})

    def _prepare_move_line_default_vals(self):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        
        # Compute amounts.
        if self.type == 'receive_payment':
            # Receive money.
            liquidity_amount_currency = self.amount
        elif self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.amount
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.amount
        else:
            liquidity_amount_currency = 0.0

        liquidity_balance = self.currency_id._convert(
            liquidity_amount_currency,
            self.company_id.currency_id,
            self.company_id,
            self.date,
        )
        
        currency_id = self.currency_id.id or self.company_id.currency_id.id

        # Compute a default label to set on the journal items.
        liquidity_line_name = ''.join(x[1] for x in self._get_aml_default_display_name_list())
        counterpart_line_name = ''.join(x[1] for x in self._get_aml_default_display_name_list())
        
        line_vals_list = []
        for line in self.line_ids:
            line_credit = 0
            line_debit = 0

            if not line.account_id:
                raise Warning("Account untuk line %s tidak ditemukan!" % line.name)
            
            # ? Account move line should not be negative
            # ? If the amount is negative, we need to change the sign
            # ? and the type of the line
            amount = line.amount

            if line.amount < 0:
                amount = -line.amount
                if line.type == 'dr':
                    line.type = 'cr'
                elif line.type == 'cr':
                    line.type = 'dr'
            
            # Handle Tax
            if line.tax_ids:
                computed_tax = line.tax_ids.compute_all(amount,line.currency_id)
                amount = computed_tax.get('total_void',0)

            # Handle ammount currency and debit/credit
            if (line.type=='dr'):
                line_debit = amount
                amount_currency = amount
            elif (line.type=='cr'):
                line_credit = amount
                amount_currency = -amount
            elif (line.type=='wo'):
                sign = self.payment_type == 'outbound' and -1 or 1
                amount = sign * line.amount
                # amount_currency = amount
                line_credit = amount if amount > 0 else 0.0
                line_debit = -amount if amount < 0 else 0.0
                # The amount expressed in writeoff must be positive when account is debited and negative when account is credited
                amount_currency = line_debit - line_credit
            line_vals_list.append(
                # Liquidity line.
                {
                    'name': line.move_line_id.ref or line.name or self.name,
                    'date_maturity': self.date,
                    'amount_currency': amount_currency,
                    'currency_id': currency_id,
                    'payment_line_id': line.id if line._name == 'tw.account.payment.line' else False,
                    'debit': line_debit,
                    'credit': line_credit,
                    'partner_id': self.partner_id.id,
                    'account_id': line.account_id.id,
                    'company_id': line.beneficiary_company_id.id or self.company_id.id,
                    'tax_ids': [Command.set(line.tax_ids.ids)],
                    'division': self.division,
                }
            )
        
        amount_wo = 0.0
                
        account_id, max_rounding = self._get_rounding_configuration()
        total_cr = sum([l.amount_included for l in self.line_ids if l.type == 'cr'])
        total_dr = sum([l.amount_included for l in self.line_ids if l.type == 'dr'])
        total_wo = sum([l.amount_included for l in self.line_ids if l.type == 'wo'])
        
        total_amount = total_cr - total_dr - total_wo
        max_rounding = int(float(max_rounding))
        sign = self.payment_type == 'outbound' and -1 or 1
        diff = self.amount - (sign * (total_cr - total_dr)) - total_wo
        if diff:
            diff_name = False
            if self.is_round:
                diff_name = f'{self.name} (Pembulatan)'
                if abs(diff) > max_rounding:
                    raise Warning("Nilai different amount tidak boleh melebihi batas pembulatan")
                if not account_id:
                    raise Warning("Account pembulatan tidak ditemukan")
                    
                line_vals_list.append({
                    'company_id': self.company_id.id,
                    'division': self.division,
                    'name': diff_name or self.name,
                    'account_id': account_id,
                    'partner_id': self.partner_id.id,
                    'date': self.date,
                    'credit': diff if diff > 0 else 0.0,
                    'debit': -diff if diff < 0 else 0.0,
                    'amount_currency': -diff,
                    'currency_id': currency_id,
                })
            else:
                raise Warning(_(f"Gagal membuat journal Entries, terdapat perbedaan amount. Amount bayar {self.currency_format(self.amount)} amount detail {self.currency_format(total_amount*-1)} Silahkan cek kembali."))
            
        # Receivable / Payable.
        #? Jika account di isi di header, maka menggunakan account dari header
        #? Jika tidak, maka menggunakan account dari journalnya
        if self.account_id:
            account_id = self.account_id.id
        else:
            account = self.journal_id.default_debit_account_id if liquidity_balance > 0.0 else self.journal_id.default_credit_account_id
            account_id = account.id if account else self.journal_id.default_account_id.id
            
        if not account_id:
            raise Warning("Default Account is not set for journal %s.\n"
                        "- Go to the Journal.\n"
                        "- Set the 'Default Account'.\n"
                        "This configuration is required to create Payment." 
                        % self.journal_id.name)
            
        line_vals_list.append({
                    'division': self.division,
                    'company_id': self.company_id.id,
                    'name': self.memo or self.name,
                    'date_maturity': self.date,
                    'amount_currency': liquidity_amount_currency,
                    'currency_id': currency_id,
                    'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                    'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': account_id,
                })
        return line_vals_list

    def _generate_journal_entry(self, write_off_line_vals=None, force_balance=None, line_ids=None):
        """
        Inheriting default generate entry, because we dont use outstanding_account_id field and have different method
        of generating journal entry which can have more than 1 move line.
        """
        pass

    def _get_rounding_configuration(self) :
        branch_setting = self.company_id.branch_setting_id
        account_setting = branch_setting.account_setting_id
        account_id = account_setting.account_rounding_id.id
        if not account_id:
            raise Warning('Account Rounding belum disetting pada Branch account config')     
        rounding_amount = account_setting.rounding_amount or 0
        return (account_id, rounding_amount)

    def _post_reconcilled_bills(self):
        if self.state != 'paid':
            raise Warning(_("Payment state should be paid to reconcile related invoice!"))

        # Track invoices before reconciliation
        invoices_to_check = self.env['account.move']
        
        for line in self.line_ids:
            payment_entry = self.move_id.line_ids.filtered(lambda aml: aml.payment_line_id.id == line.id and not aml.reconciled)
            invoice_entry = line.move_line_id
            if invoice_entry and payment_entry:
                # Track invoice before reconciliation
                invoice = invoice_entry.move_id
                if invoice.is_invoice(include_receipts=True) and invoice.payment_state not in ('paid', 'in_payment'):
                    invoices_to_check |= invoice
                    
                (payment_entry + invoice_entry).sudo().reconcile()
        # Trigger _invoice_paid_hook for invoices that became paid after reconciliation
        if invoices_to_check:
            invoices_to_check.filtered(
                lambda inv: inv.payment_state == 'paid'
            )._invoice_paid_hook()
    
    def _fetch_duplicate_reference(self, matching_states=False):
        """ Retrieve move ids for possible duplicates of payments. Duplicates moves:
        - Have the same partner_id, amount and date as the payment
        - Are not reconciled
        - Represent a credit in the same account receivable or a debit in the same account payable as the payment, or
        - Represent a credit in outstanding receipts or debit in outstanding payments, so bank statement lines with an
         outstanding counterpart can be matched, or
        - Are in the suspense account
        """
        # Does not perform unnecessary check if partner_id or amount are not set, nor if payment is posted
        payments = self.filtered(lambda p: p.partner_id and p.amount and p.state != 'in_process')
        if not payments:
            return {}

        if not matching_states:
            matching_states = self._get_to_check_duplicate_states()
        # Update tables involved in the query
        used_fields = ("company_id", "partner_id", "date", "state", "amount", 'payment_type')
        self.flush_model(used_fields)

        model_name = self._name
        tabel_name = self._name.replace('.', '_')
        payment_table_and_alias = SQL("%s AS payment" % tabel_name)
        if not self[0].id:  # if record is under creation/edition in UI, safely inject values in the query
            # Necessary since new record aren't searchable in the DB and record in edition aren't up to date yet
            values = {
                field_name: self._fields[field_name].convert_to_write(self[field_name], self) or None
                for field_name in used_fields
            }
            values["id"] = self._origin.id or 0
            # The amount total depends on the field line_ids and is calculated upon saving, we needed a way to get it even when the
            # invoices has not been saved yet.
            casted_values = SQL(', ').join(
                SQL("%s::%s", value, SQL.identifier(self._fields[field_name].column_type[0]))
                for field_name, value in values.items()
            )
            column_names = SQL(', ').join(SQL.identifier(field_name) for field_name in values)
            payment_table_and_alias = SQL("(VALUES (%s)) AS payment(%s)", casted_values, column_names)

        query = SQL(
            """
                SELECT payment.id AS payment_id,
                       ARRAY_AGG(DISTINCT duplicate_payment.id) AS duplicate_payment_ids
                  FROM %(payment_table_and_alias)s
                  JOIN %(tabel_name)s AS duplicate_payment ON payment.id != duplicate_payment.id
                                                           AND payment.partner_id = duplicate_payment.partner_id
                                                           AND payment.company_id = duplicate_payment.company_id
                                                           AND payment.date = duplicate_payment.date
                                                           AND payment.payment_type = duplicate_payment.payment_type
                                                           AND payment.amount = duplicate_payment.amount
                                                           AND duplicate_payment.state IN %(matching_states)s
                 WHERE payment.id = ANY(%(payments)s)
              GROUP BY payment.id
            """,
            payment_table_and_alias=payment_table_and_alias,
            tabel_name=SQL(tabel_name),
            matching_states=tuple(matching_states),
            payments=payments.ids or [0],
        )

        return {
            payment_id: self.env[model_name].browse(duplicate_ids)
            for payment_id, duplicate_ids in self.env.execute_query(query)
        }
    