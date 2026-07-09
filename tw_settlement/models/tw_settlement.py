# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib
from datetime import date, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import ValidationError, UserError as Warning

# 5: local imports
import logging

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)


class TwSettlement(models.Model):
    _name = "tw.settlement"
    _description = "Settlement"
    _inherit = ["tw.attachment.mixin"]
    _order = "id desc"
    
    # 7: defaults methods

    @api.depends_context('lang')
    @api.depends('settlement_line_ids.amount', 'settlement_line_ids.tax_id')
    def _compute_tax_totals(self):
        AccountTax = self.env['account.tax']
        for order in self:
            if not order.company_id:
                order.tax_totals = order._empty_tax_totals(order.company_id.currency_id)
                continue

            order_lines = order.settlement_line_ids
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
            order.tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.company_id.currency_id,
                company=order.company_id,
            )
    
    @api.depends('amount_avp','settlement_line_ids.amount')
    def _compute_amount(self):
        for record in self:
            amount = 0
            for line in record.settlement_line_ids:
                amount += line.amount

            record.amount_total = amount

            if record.type:
                if record.type=='kembali':
                    record.amount_gap = record.amount_avp - record.amount_total
                else:
                    record.amount_gap = record.amount_total - record.amount_avp
            else:
                record.amount_gap = 0 
        
    def _get_default_date(self):
        return date.today()

            
    # 8: fields
    name = fields.Char(string='Settlement',compute='_compute_name',store=True)
    amount_avp = fields.Float(string='Total AVP')
    date = fields.Date(string='Date',default=_get_default_date)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options_list(['Unit','Sparepart','Umum']))
    state = fields.Selection([
            ('draft','Draft'),
            ('done','Done'),
            ('cancel','Cancelled')
        ], string='Status', index=True, readonly=True, default='draft')
    description = fields.Text(string='Description')
    type = fields.Selection([
                             ('tambah','Tambah'),
                             ('kembali','Kembali')                             
                             ],string='Type Kas')
    amount_total = fields.Float(string='Total Untaxed',digits='Account', store=True, readonly=True, compute='_compute_amount',)
    amount_tax = fields.Float(string='Total Tax',digits='Account', store=True, readonly=True, compute='_compute_amount',)
    amount_gap = fields.Float(string='Total Kembalian/Tambahan',digits='Account', store=True, readonly=True, compute='_compute_amount',)
    tax_totals = fields.Binary(compute='_compute_tax_totals', exportable=False)
    email = fields.Char(string='Email')
    reference_pengembalian = fields.Char(string='Ref Pengembalian')
    count_moves = fields.Integer('Count Moves', compute="_compute_count_moves")
    

    # Audit Trail
    confirm_uid = fields.Many2one('res.users',string="Confirmed by")
    confirm_date = fields.Datetime('Confirmed on')
    cancel_uid = fields.Many2one('res.users',string="Cancelled by")
    cancel_date = fields.Datetime('Cancelled on')
    
    # 9: relation fields
    employee_id = fields.Many2one('hr.employee',string='Employee',required=True)
    company_id = fields.Many2one('res.company', string='Branch',required=True)
    advance_payment_id = fields.Many2one('tw.advance.payment',string='Advance Payment',required=True)
    journal_id = fields.Many2one('account.journal',string='Journal', domain="[('company_id', 'parent_of', company_id)]", copy=False)
    return_journal_id = fields.Many2one('account.journal',string='Journal Kembali', domain="[('company_id', 'parent_of', company_id), ('type','in',('bank','cash'))]")
    account_avp_id = fields.Many2one('account.account',string='Account Advance Payment')
    move_id = fields.Many2one('account.move')
    move_ids = fields.One2many(related='move_id.line_ids', string='Journal Items', readonly=True)
    settlement_line_ids = fields.One2many('tw.settlement.line','settlement_id',required=True)
    available_account_ids = fields.Many2many(comodel_name='account.account',compute='_compute_available_account_ids')

    # 10: Constraints & SQL Constraints
    @api.constrains('advance_payment_id', 'state')
    def _check_description(self):
        avp_id = self.search([('advance_payment_id','=',self.advance_payment_id.id)])
        if len(avp_id)>1:
            for avp in avp_id:
                if avp.state!='cancel' and avp.id!=self.id:
                    raise Warning("Nomor Advance Payment sudah pernah di buat di transaksi lain")
        
    # 11: Compute/Depends & On Change Methods
    @api.depends('move_id','state')
    def _compute_count_moves(self):
        for record in self:
            record.count_moves = len(record.move_id)

    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            if record.id and not record.name and record.state:
                prefix = record.company_id.code
                seq_name = self.env['ir.sequence'].get_sequence_code('STL', prefix)
                record.name = seq_name
    
    @api.onchange('advance_payment_id')
    def onchange_avp_id(self):
        if self.advance_payment_id:
            self._check_avp()
            self.employee_id = self.advance_payment_id.employee_id.id
            self.company_id = self.advance_payment_id.company_id.id
            self.division = self.advance_payment_id.division
            self.amount_avp = self.advance_payment_id.amount
            self.account_avp_id = self.advance_payment_id.account_avp_id.id
    
    @api.depends('company_id')
    def _compute_available_account_ids(self):
        for record in self:
            domain = ['|', ('company_ids', 'in', record.company_id.id), ('company_ids', 'parent_of', record.company_id.id)]
            filter_type = 'advance_payment'
            account_filter_domain = self.env['tw.account.filter'].get_account_domain(filter_type)
            if account_filter_domain:
                domain += account_filter_domain
            record.available_account_ids = self.env['account.account'].search(domain)
            
    @api.onchange('type')
    def onchange_type(self):
        self.return_journal_id = False

    # 12: Override Methods
    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            branch_obj = self.env['res.company'].browse(vals['company_id'])
            self._check_branch_config(branch_obj)
            vals['date'] = self._get_default_date()
            vals['journal_id'] = branch_obj.branch_setting_id.account_setting_id.journal_settlement_id.id
        return super(TwSettlement,self).create(vals_list)
    
    def unlink(self):
        for item in self:
            if item.state != 'draft':
                raise Warning("Settlement sudah diproses, data tidak bisa dihapus !")
        return super(TwSettlement, self).unlink()

    def copy(self, default=None):
        """Override copy untuk tidak membawa journal dan data audit trail."""
        default = dict(default or {})
        default.update({
            'move_id': False,
            'journal_id': False,
            'state': 'draft',
            'confirm_uid': False,
            'confirm_date': False,
            'cancel_uid': False,
            'cancel_date': False,
        })
        return super(TwSettlement, self).copy(default)
    
    
    # 13: Action Methods
    def action_confirm(self):
        # Check branch config
        self._check_branch_config()
        self.check_amount_total()
        self._create_account_move()
        
        move_line_avp = self.env['account.move.line'].sudo().search([('id','in',self.advance_payment_id.move_ids.ids),('account_id','=',self.account_avp_id.id)])
        if not move_line_avp:
            raise Warning('Confirm gagal. Tidak ada jurnal advance payment yang bisa dilakukan reconciliation.')
        move_line_stl = self.env['account.move.line'].sudo().search([('move_id','=',self.move_id.id),('account_id','=',self.account_avp_id.id),('name','ilike','Payment Amount -%%')])
        if not move_line_stl:
            raise Warning('Confirm gagal. Tidak ada jurnal settlement yang bisa dilakukan reconciliation.')
        
        (move_line_avp + move_line_stl).reconcile()

        self.move_id.write({'narration':'refresh'}) #untuk mentrigger status move.line, karena jika ada intercompany statusnya unbalance. kalau di write maka berubah jadi balance. kalau unbalance jadi masalah saat mau cancel
        self.advance_payment_id.suspend_security().action_done()
        self.write({'date':self._get_default_date(),'state':'done','confirm_uid':self._uid,'confirm_date':datetime.now()})        
        return True

    
    def action_cancel_settlement(self,context=None):
        self.write({'state':'cancel','cancel_uid':self._uid,'cancel_date':datetime.now()})
        # cancel advance payment
        self.advance_payment_id.action_cancel()

    def action_view_entries(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_journal_line")
        context = eval(action.get('context')) if action.get('context') else {}
        context.update({
            'create':False,
        })
        action['context'] = context
        action['domain'] = [('id','in',self.move_id.ids)]
        return action
    
    def action_print_settlement(self):
        self.ensure_one()
        return self.env.ref('tw_settlement.action_settlement_advance_payment_report').report_action(self.id)

    # 14: Private Methods
    def _create_account_move(self):
        if self.move_id:
            raise Warning(_("Advance Payment already posted or Journal Entry already created."))
        self._check_branch_config()
        currency_id = self.company_id.currency_id.id
        move_vals = {
            'move_type': 'entry',
            'ref': self.name,
            'date': self.date,
            'journal_id': self.journal_id.id,
            'company_id': self.company_id.id,
            'division': self.division,
            'partner_id': self.employee_id.user_id.partner_id.id,
            'currency_id': currency_id,
            'partner_bank_id': False,
            'line_ids': [
                Command.create(line_vals)
                for line_vals in self._prepare_move_line_default_vals()
            ],
        }
        if self.name:
            move_vals['name'] = self.name
        move_created = self.env['account.move'].create([move_vals])
        
        move_created.sudo().action_post()
        
        self.move_id = move_created.id
    
    def _prepare_move_line_default_vals(self):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        period_ids = self.env['tw.account.period']._get_current_periods()
        currency_id = self.company_id.currency_id.id

        line_vals_list = []       
        taxes = {}
        if not self.account_avp_id:
            account_avp_id = self.advance_payment_id.account_avp_id.id or self.company_id.branch_setting_id.account_setting_id.journal_avp_id.default_debit_account_id.id
            self.account_avp_id = account_avp_id
            if not account_avp_id:
                raise Warning("Account Advance Payment not found")

        partner = self.employee_id.work_contact_id or self.employee_id.user_id.partner_id
        if not partner:
            raise Warning(_("Data partner untuk employee %s tidak ditemukan") % self.employee_id.name)
            
        line_vals_list.append({
                    'name': 'Payment Amount - ' + (self.description or self.name),
                    'partner_id': partner.id,
                    'account_id': self.account_avp_id.id,
                    'period_id': period_ids.id,
                    'date': self._get_default_date(),
                    'debit': 0.0,
                    'credit': self.amount_avp,
                    'amount_currency': -self.amount_avp,
                    'company_id': self.company_id.id,
                    'division': self.division,
                    'currency_id': currency_id,
                    'date_maturity': self._get_default_date(),
                })

        for record in self.settlement_line_ids:
            line_vals_list.append({
                'name': 'Advance Payment - ' + (self.description or self.name),
                'date_maturity': self._get_default_date(),
                'amount_currency': record.price_subtotal,
                'currency_id': currency_id,
                'period_id': period_ids.id,
                'debit': record.price_subtotal,
                'credit': 0.0,
                'partner_id': partner.id,
                'account_id': record.account_id.id,
                'company_id': self.company_id.id,
                'division': self.division,
                'currency_id': currency_id,
                'date_maturity': self._get_default_date(),
                'tax_ids': [(6, 0, record.tax_id.ids)],
            })
            if record.tax_id:
                taxes[record.tax_id] = taxes.get(record.tax_id,0) + record.price_tax
        
        if self.type == 'tambah':
            line_vals_list.append({
                    'name': 'Kekurangan Advance Payment - ' + (self.description or self.name),
                    'partner_id': partner.id,
                    'account_id': self.advance_payment_id.journal_id.default_credit_account_id.id,
                    'period_id': period_ids.id,
                    'date': self._get_default_date(),
                    'debit': 0.0,
                    'credit': self.amount_gap,
                    'amount_currency': -self.amount_gap,
                    'company_id': self.company_id.id,
                    'division': self.division,
                    'currency_id': currency_id,
                    'date_maturity': self._get_default_date(),  
                    # 'tax_ids': [(6, 0, record.tax_id.ids)],
            })
        elif self.type == 'kembali':
            line_vals_list.append({
                    'name': 'Kembalian Advance Payment - ' + (self.description or self.name),
                    'partner_id': partner.id,
                    'account_id': self.return_journal_id.default_debit_account_id.id or self.return_journal_id.default_credit_account_id.id,
                    'period_id': period_ids.id,
                    'date': self._get_default_date(),
                    'debit': self.amount_gap,
                    'credit': 0.0,
                    'amount_currency': self.amount_gap,
                    'company_id': self.company_id.id,
                    'division': self.division,
                    'currency_id': currency_id,
                    'date_maturity': self._get_default_date(),
                    # 'tax_ids': [(6, 0, record.tax_id.ids)],
            })                 
      
        return line_vals_list

    def check_amount_total(self):
         
        if self.type == 'kembali':
            if self.amount_total >= self.amount_avp:
                raise Warning('Amount harus lebih kecil dari total AVP untuk tipe kembali')
        elif self.type == 'tambah':
            if self.amount_total <= self.amount_avp:
                raise Warning('Amount harus lebih besar dari total AVP untuk tipe tambah')
        else:
            if self.amount_total != self.amount_avp:
                raise Warning('Amount harus sama dengan total AVP')
               
    def _check_branch_config(self,branch=False):
        branch_conf = self.company_id.branch_setting_id.account_setting_id or branch.branch_setting_id.account_setting_id
        if not branch_conf:
            raise Warning("Konfigurasi Branch Config Settlement belum dibuat !")
        else:
            if not branch_conf.journal_settlement_id:
                raise Warning("Konfigurasi Journal Settlement belum dibuat !")
            
            if self.type == 'kembali' and not(self.return_journal_id.default_credit_account_id):
                raise Warning("Konfigurasi Default Credit pada Payment Method %s belum dibuat, silahkan setting dulu"%(self.return_journal_id.name))

    def _check_avp(self):
        avp_booked = self.search([('advance_payment_id','=',self.advance_payment_id.id),('state','!=','cancel')],limit=1)
        if avp_booked:
            raise Warning("Settelement untuk Advance Payment ini sudah pernah di buat di transaksi lain (%s)" %(avp_booked.name))

    

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