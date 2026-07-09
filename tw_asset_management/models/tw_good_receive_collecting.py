# -*- coding: utf-8 -*-

# 1: imports of python lib
from collections import defaultdict

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command
from odoo.osv import expression

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, OrderedSet, groupby, formatLang

# 5: local imports

# 6: Import of unknown third party lib

class TwGoodReceiveCollecting(models.Model):
    _name = "tw.good.receive.collecting"
    _inherit = ["tw.attachment.mixin"]
    _description = "Good Receive Collecting"
    _order = "id desc"

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now()
    
    # 8: fields
    name = fields.Char(string="Name", readonly=True, default='New', copy=False, index=True, compute='_compute_name', store=True)
    date = fields.Date(string='Date', default=_get_default_date)
    document_no = fields.Char(string='Vendor Document No')
    no_faktur_pajak = fields.Char(string='No Faktur Pajak')
    document_date = fields.Date(string='Document Date')
    tgl_faktur_pajak = fields.Date(string='Tgl Faktur Pajak')
    description = fields.Char(string='Description')
    reason_cancel = fields.Char(string='Reason Cancel')
    is_collect_all = fields.Boolean(string='Collect All?')
    notes = fields.Html('Terms and Conditions')

    amount_total = fields.Float(string='Total', digits='Account', compute='_compute_amount_all')
    amount_untaxed = fields.Float(string='Amount Untaxed', digits='Account', compute='_compute_amount_all')
    amount_tax = fields.Float(string='Amount Tax', digits='Account', compute='_compute_amount_all')
    tax_totals = fields.Binary(compute='_compute_tax_totals', exportable=False)
    
    state = fields.Selection([
        ('draft', 'Draft Quotation'),
        ('waiting_for_approval','Waiting For Approval'),
        ('approved','Approved'),
        ('open', 'Open'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
        ('reject','Rejected'),
    ], string='Status', default='draft')
    division = fields.Selection([
        ('Umum', 'Umum'),
    ], required=True, string='Division', default='Umum')

    # Audit Trail
    rfa_uid = fields.Many2one('res.users','RFA by')
    rfa_date = fields.Datetime('RFA on')
    confirm_date = fields.Datetime('Confirmed on')
    confirm_uid = fields.Many2one('res.users', string='Confirmed by')
    approve_date = fields.Datetime('Approved on')
    approve_uid = fields.Many2one('res.users', string='Approved by')
    done_date = fields.Datetime('Done on')
    done_uid = fields.Many2one('res.users', string='Done by')
    cancel_date = fields.Datetime('Cancelled on')
    cancel_uid = fields.Many2one('res.users', string='Cancelled by')


    # 9: relation fields
    branch_type_id = fields.Many2one('tw.selection', string='Branch Type', related='company_id.branch_type_id')
    payment_term_id = fields.Many2one('account.payment.term',string='Payment Term')
    invoice_id = fields.Many2one(comodel_name='account.move', string='Invoice')
    company_id = fields.Many2one(comodel_name='res.company', string='Branch')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Supplier')
    tax_ids = fields.Many2many('account.tax', 'invoice_tw_good_receive_collecting_tax', 'collecting_id', 'tax_id', 'Taxes')
    move_id = fields.Many2one('account.move', 'Account Entry', copy=False)
    move_ids = fields.One2many(related='move_id.line_ids', string='Journal Items', readonly=True)
    line_ids = fields.One2many(comodel_name='tw.good.receive.collecting.line', inverse_name='collecting_id', string='Collecting Lines')
    currency_id = fields.Many2one("res.currency", readonly=True)
    good_receive_ids = fields.Many2many('tw.good.receive', 'tw_good_receive_collecting_rel', 'collecting_good_receive_id', 'good_receive_id', 'Good Receive', copy=False)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    @api.depends('move_id','move_ids')
    def _compute_move_ids(self):
        for rec in self:
            if rec.move_id:
                if rec.move_id.payment_state == 'paid':
                    rec.action_done()

    @api.depends_context('lang')
    @api.depends('line_ids', 'line_ids.price', 'line_ids.discount', 'line_ids.qty', 'line_ids.tax_ids')
    def _compute_tax_totals(self):
        AccountTax = self.env['account.tax']
        for order in self:
            if not order.company_id:
                order.tax_totals = order._empty_tax_totals(order.company_id.currency_id)
                continue

            order_lines = order.line_ids
            base_lines = [line._prepare_base_line_for_taxes_computation() for line in order_lines]
            AccountTax._add_tax_details_in_base_lines(base_lines, order.company_id)
            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
            tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.company_id.currency_id,
                company=order.company_id,
            )
            order.tax_totals = tax_totals
    
    def _compute_amount_all(self):
        for order in self:
            amount_untaxed = 0.0
            amount_tax = 0.0
            amount_total = 0.0

            for add in order.line_ids:
                amount_untaxed += add.price_subtotal
                amount_tax += add.price_tax
                amount_total += (add.price_subtotal + add.price_tax)

            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax
            order.amount_total = amount_total

    
    @api.depends('company_id')
    def _compute_currency(self):
        for bill in self:
            branch_config_obj = bill.company_id.branch_setting_id
            currency_id = False
            if branch_config_obj:
                currency_id = branch_config_obj.account_setting_id.journal_purchase_unit_id.currency_id
            bill.currency_id = currency_id.id if currency_id else bill.company_id.currency_id
    
    @api.depends('partner_id')
    def _compute_company(self):
        for bill in self:
            bill.company_id =  bill.company_id.id or bill.partner_id.company_id.id

    @api.depends('company_id')
    def _compute_name(self):
        for rec in self:
            if not rec.name or rec.name == 'New':
                if rec.company_id:
                    rec.name = self.env['ir.sequence'].get_sequence_code('GRC', rec.company_id.code)

    @api.onchange('company_id', 'partner_id')
    def _onchange_company_id(self):
        self.currency_id = False
        self.description = False
        self.document_date = False
        self.document_no = False
        self.line_ids = False 
        self.is_collect_all = False
        self.good_receive_ids = False
        
        if self.company_id or self.partner_id:
            self.currency_id = self.company_id.currency_id if self.company_id else False
    
    @api.onchange('tax_ids')
    def _onchange_tax_ids(self):
        for line in self.line_ids:
            line.tax_ids = [[6, 0, self.tax_ids.ids]]
        
    
    @api.onchange('good_receive_ids')
    def _onchange_good_receive_ids(self):
        if not self.good_receive_ids:
            self.line_ids = False
        else:
            self.line_ids = False
            data_line_ids = []
            for data in self.good_receive_ids:
                for line in data.move_asset_ids:
                        data_line_ids.append([0, 0, {
                            'collecting_good_receive_id': line._origin.id,
                            'purchase_order_id': line.purchase_order_id.id,
                            'purchase_order_line_id': line.purchase_order_line_id.id,
                            'product_id': line.product_id.id,
                            'origin': line.picking_id.name,
                            'description': line.description,
                            'document_date': line.do_date,
                            'price': line.price,
                            'qty': line.qty,
                            'discount': line.discount,
                            'company_id': line.company_id.id,
                            'partner_id': data.partner_id.id,
                            'account_id': line.asset_category_id.account_asset_id.id,
                            'tax_ids':[(6,0,line.tax_ids.ids)],
                            }])
            self._compute_currency()
            self._compute_company()
            self.line_ids = data_line_ids
        
    
    @api.onchange('is_collect_all')
    def _onchange_is_collect_all(self):
        self.line_ids = False
        if self.is_collect_all:
            data_line_ids = []
            for data in self.good_receive_ids:
                for line in data.move_asset_ids:
                    data_line_ids.append([0, 0, {
                        'collecting_good_receive_id': line._origin.id,
                        'purchase_order_id': line.purchase_order_id.id,
                        'purchase_order_line_id': line.purchase_order_line_id.id,
                        'product_id': line.product_id.id,
                        'origin': line.picking_id.name,
                        'description': line.description,
                        'document_date': line.do_date,
                        'price': line.price,
                        'qty': line.qty,
                        'discount': line.discount,
                        'company_id': line.company_id.id,
                        'partner_id': data.partner_id.id,
                        'account_id': line.asset_category_id.account_asset_id.id,
                        'tax_ids':[(6,0,line.tax_ids.ids)],
                    }])
            self._compute_currency()
            self._compute_company()
            self.line_ids = data_line_ids
            if not data_line_ids:
                self.line_ids = False
        else:
            self.line_ids = False

    @api.model_create_multi 
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('line_ids'):
                raise Warning('Tidak ada data Collecting Lines!')
            duplicate_data = []
            if not self.is_collect_all:
                for line in vals.get('line_ids'):
                    if line[2].get('collecting_good_receive_id') and line[2].get('collecting_good_receive_id') not in duplicate_data:
                        duplicate_data.append(line[2].get('collecting_good_receive_id'))
                    else:
                        collecting_good_receive_line_obj = self.env['tw.good.receive.asset.line'].suspend_security().browse(line[2].get('collecting_good_receive_id'))
                        if collecting_good_receive_line_obj:
                            raise Warning('Terdapat data yang duplikat %s[%s]\n\n hapus dahulu data yang duplikat!' % (collecting_good_receive_line_obj.name, collecting_good_receive_line_obj.description))
            
            company_id = vals.get('company_id', self.default_get(['company_id']).get('company_id'))
            branch_obj = self.env['res.company'].browse(company_id)
            
            if vals.get('name', 'New') == 'New':
                seq_name = self.with_company(company_id).env['ir.sequence'].get_sequence_code('GRC', branch_obj.code)
                vals['name'] = seq_name 


        return super(TwGoodReceiveCollecting, self).create(vals_list)
    
    
    def write(self, vals):        
        duplicate_data = []
        write = super(TwGoodReceiveCollecting, self).write(vals)
        for line in self.line_ids:
            if line and line.collecting_good_receive_id and line.collecting_good_receive_id.id not in duplicate_data:
                duplicate_data.append(line.collecting_good_receive_id.id)
            else:
                raise Warning('Terdapat data yang duplikat %s[%s]\n\n hapus dahulu data yang duplikat!' % (line.collecting_good_receive_id.name, line.collecting_good_receive_id.description))
        return write

    
    def unlink(self):
        for me in self:
            if me.state != 'draft':
                raise Warning('Tidak bisa dihapus selain Draft !')
        return super(TwGoodReceiveCollecting, self).unlink()
    
    def button_dummy(self):
        return True
    
    
    def action_confirm(self):
        if self.state != 'approved':
            raise Warning(f'Silakan refresh halaman Good Receive Collecting ini, karena state sudah {self._get_state_value()}')
        
        # Recompute amount
        self._compute_amount_all()

        # * Create journals and invoice
        self.suspend_security().action_create_journal_invoice()

        # for data in self.good_receive_ids:
        #     data.suspend_security().action_check_status()

        move = self.env['account.move'].suspend_security().search([('ref','=',self.name)], limit=1)

        # Collect unique GR asset lines to avoid duplicate write on same record
        unique_gr_lines = self.line_ids.mapped('collecting_good_receive_id')
        unique_gr_lines.write({'state': 'done'})

        vals = {
            'move_id': self.invoice_id.id if self.invoice_id else move.id,
            'confirm_uid': self._uid,
            'confirm_date': datetime.now()
        }
        if self.state != 'done':
            vals['state'] = 'open'
            
        self.write(vals)
    
    
    def action_cancel_wizard(self):
        if self.state in ('cancel','done'):
            raise Warning('Collecting sudah dilakukan %s, tidak dapat di cancel !' %(self.state))
        
        form_id = self.env.ref('tw_good_receive.good_receive_collecting_cancel_wizard_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': ('Cancel Good Receive Collecting'),
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'view_id': False,
            'res_model': 'tw.good.receive.collecting',
            'res_id': self.id,
            'views': [(form_id, 'form')]
        }

    
    def action_cancel(self):
        if self.invoice_id:
            # * Check Invoice and auto cancel
            self._auto_invoice_cancel()
        
        if self.move_id:
            # * Cancel Journal
            self.move_id.cancel_journal()
        

        self.write({
            'state': 'cancel',
            'cancel_uid': self._uid,
            'cancel_date': datetime.now()
        })

        # * update all lines to draft in Collecting lines
        self.action_update_collecting_status()

    
    def action_update_collecting_status(self):
        if not self.line_ids:
            raise Warning('Tidak ada data Collecting Lines!')
        
        if self.state not in ('draft','waiting_for_approval','open','cancel'):
            raise Warning('Status transaksi sudah bukan Draft / RFA / Open!')

        for line in self.line_ids:
            if line.collecting_good_receive_id and line.collecting_good_receive_id.state != 'draft':
                line.collecting_good_receive_id.suspend_security().write({'state': 'draft'})
                line.collecting_good_receive_id.picking_id.suspend_security().action_check_status()

    
    def action_view_invoice(self):  
        return {
            'name': 'Supplier Invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': self.invoice_id.id
        }

    
    def action_create_journal_invoice(self):
        if self.good_receive_ids and self.line_ids:
            obj_model_id = self.env['ir.model'].search([ ('model','=',self.__class__.__name__) ])
            name = self.name
            config = self.company_id.branch_setting_id.account_setting_id
            
            if not config:
                raise Warning('Please define Journal in Setup Division for this branch: "%s".' %(self.company_id.name))
            
            journal_good_receive_asset_collecting_id = config.journal_good_receive_asset_collecting_id
            if not journal_good_receive_asset_collecting_id:
                raise Warning('Journal Good Receive Colleting pada Branch %s kosong.' %(self.company_id.name))
            
            invoice_account = journal_good_receive_asset_collecting_id.default_credit_account_id
            if not invoice_account:
                raise Warning('Default Credit Account pada journal %s kosong !' %(journal_good_receive_asset_collecting_id.name))
            
            if self.env['account.move'].search([('ref','=',self.name)], limit=1):
                raise Warning('Invoice dengan %s sudah ada' %(self.name))
            
            invoice_line = []
            account_line_id = journal_good_receive_asset_collecting_id.default_debit_account_id
            if not account_line_id:
                raise Warning('Default Debit Account pada journal %s kosong !' %(journal_good_receive_asset_collecting_id.name))

            for data in self.line_ids:
                good_receive_account_move = self.env['account.move.line'].search([
                    ('ref', '=', data.collecting_good_receive_id.picking_id.name),
                    '|',
                    ('credit', '>', 0),
                    ('name','!=', data.collecting_good_receive_id.picking_id.name)
                ], limit=1)
                product_name = data.product_id.name or data.product_id.description or ''
                invoice_line.append({
                    'company_id' :self.company_id.id,
                    'division' : self.division,
                    'name': data.collecting_good_receive_id.picking_id.name + ' ' + product_name,
                    'product_id':data.product_id.id if data.product_id else False,
                    'quantity':data.qty,
                    'ref':self.name,
                    'price_unit':data.price,
                    'account_id': good_receive_account_move.account_id.id,
                    'tax_ids': [(6, 0, data.tax_ids.ids)],
                })

            # Collect unique records to avoid duplicate writes when multiple lines reference the same GR
            unique_gr_lines = self.line_ids.mapped('collecting_good_receive_id')
            unique_gr_lines.suspend_security().write({'state': 'open'})

            unique_pickings = unique_gr_lines.mapped('picking_id')
            for picking in unique_pickings:
                picking.suspend_security().action_done()
            
            invoice_vals = {
                'ref': self.name,
                'company_id':self.company_id.id,
                'division': self.division,
                'partner_id':self.partner_id.id,
                'move_type': 'in_invoice',
                'date': self.date,
                'invoice_date': self.document_date or self.date,
                'journal_id': journal_good_receive_asset_collecting_id.id,
                'invoice_payment_term_id': self.payment_term_id.id,
                'invoice_line_ids': [Command.create(line) for line in invoice_line],
            }
            invoice = self.env['account.move'].with_company(self.company_id).create(invoice_vals)
            prefix = self.company_id.code
            invoice.name = self.env['ir.sequence'].get_sequence_code('JCA', prefix)
            invoice.sudo().action_post()
            
            self.write({'invoice_id': invoice.id})
 
            try:
                payment_journal = journal_good_receive_asset_collecting_id
                if not payment_journal:
                    raise Warning("Journal untuk pembayaran keluar (outbound payment) belum di-setting di Branch Config!")
                
                payable_line = self.env['account.move.line'].search([
                    ('move_id', '=', invoice.id),
                    ('partner_id', '=', self.partner_id.id),
                    '|',
                    ('credit', '>', 0),
                    ('name','!=', data.collecting_good_receive_id.picking_id.name)
                ], limit=1)

                if not payable_line:
                    raise Warning("Gagal menemukan baris utang (payable line) pada invoice %s." % invoice.name)

                vals_line_dr_ids = [[0, 0, {
                    'name': invoice.name,
                    'move_line_id': payable_line.id,
                    'amount_original': payable_line.credit,
                    'amount_unreconciled': abs(payable_line.amount_residual),
                    'amount': self.amount_total, # Jumlah yang dibayar adalah total GRC
                    'date_original': invoice.date,
                    'date_due': invoice.invoice_date_due,
                    'account_id': payable_line.account_id.id,
                    'currency_id': self.currency_id.id,
                    'partner_id': self.partner_id.id,
                }]]

                vals_payment = {
                    'company_id': self.company_id.id,
                    'beneficiary_company_id': self.company_id.id, 
                    'partner_id': self.partner_id.id,
                    'partner_type': 'supplier',
                    'date': self.date,
                    'amount': self.amount_total,
                    'type': 'supplier_payment',
                    'payment_type': 'outbound',
                    'journal_id': payment_journal.id,
                    'currency_id': self.currency_id.id,
                    'account_id': payment_journal.default_account_id.id, 
                    'division': self.division,
                    'narration': 'Pembayaran Asset Collecting dengan nomor %s' % self.name,
                    'line_dr_ids': vals_line_dr_ids,
                }
                
                supplier_payment = self.env['tw.account.payment'].create(vals_payment)

            except Exception as e:
                raise Warning("Invoice berhasil dibuat, tetapi gagal membuat Supplier Payment. \n\nError: %s" % str(e))

        else:
            raise Warning('Good Receive dan Line Detail tidak ada !')
    
    
    def action_done(self):
        self.write({
            'state': 'done',
            'done_uid': self._uid,
            'done_date': datetime.now()
        })
        
        # Trigger PO status update after collecting is done
        po_ids = self.line_ids.mapped('purchase_order_id')
        for po in po_ids:
            po.suspend_security().action_check_received()
            
        return True
    
    def _auto_invoice_cancel(self):
        data = {
            'company_id': self.company_id.id,
            'invoice_id': self.invoice_id.id,
            'date': datetime.now(),
            'division': 'Umum',
            'type': 'in_invoice',
            'reason': self.reason_cancel
        }
        invoice_cancel = self.env['tw.account.invoice.cancel'].suspend_security().create(data)
        if invoice_cancel:
            invoice_cancel.request_approval()
            invoice_cancel.approva_all_approval()
            invoice_cancel.confirm()
    
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

