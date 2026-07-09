# 1: imports of python lib
from datetime import datetime, timedelta
import base64
import xlrd

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwListingCetakKwitansi(models.Model):
    _name = "tw.listing.cetak.kwitansi"
    _description = "Listing Cetak Kwitansi"

    # 7: defaults methods
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()
    
    def _get_default_datetime(self):
        return datetime.now()
    
    def _set_domain_journal_id(self):
        domain = [('id','=',0)]
        if self.company_id:
            journal_objs = self.env['account.journal'].search([
                '|',
                ('code','=','BK01HHO'),
                ('company_id','=',self.company_id.id),
                ('type','=','bank')
            ])
            if journal_objs:
                domain = [('id','in',journal_objs.ids)]

        return domain

    # 8: fields
    name = fields.Char(string='Name')
    reference_no = fields.Char(string='No Refrence')
    payer_name = fields.Char(string='Nama Pembayar')
    account_name = fields.Char(string='Nama Rekening', default='PT. Tunas Dwipa Matra')
    branch_head_name = fields.Char(string='Pimpinan Cabang')
    editorial = fields.Char(string='Redaksi')
    number_faktur_pajak = fields.Char(string='No Faktur Pajak')
    proof_of_payment_no = fields.Char(string='No Bukti Pembayaran')
    cancel_reason = fields.Text(string='Alasan Cancel')
    date = fields.Date(string='Tanggal Kwitansi', default=_get_default_date)
    payment_date = fields.Date(string='Tanggal Bukti Pembayaran')
    is_ppn = fields.Boolean(string='PPN ?')
    print_to = fields.Integer(string='Cetakan Ke')
    total = fields.Float(string='Jumlah Pembayaran')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft')
    transaction_type = fields.Selection(selection=lambda self: self.env['tw.selection'].get_option_list('ListCetakKwtCategory'))

    # Audit Trail
    confirm_date = fields.Datetime(string='Posted on')
    confirm_uid = fields.Many2one(comodel_name='res.users', string='Posted By')
    cancel_date = fields.Datetime(string='Cancelled on')
    cancel_uid = fields.Many2one(comodel_name='res.users', string= 'Cancelled By')

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', required=True, domain=[('parent_id','!=',False)], default=lambda self: self.env.company)
    journal_id = fields.Many2one(comodel_name='account.journal', string='No Rekening')

    # 10: constraints & sql constraints
    @api.constrains('total')
    def _validate_total(self):
        for record in self:
            if record.total <= 0:
                raise Warning('Jumlah Pembayaran harus lebih besar dari 0.')

    # 11: compute/depends & on change methods
    @api.onchange('is_ppn')
    def _onchange_no_faktur_pajak(self):
        self.number_faktur_pajak = False
    
    @api.onchange('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            self.branch_head_name = self.company_id.branch_setting_id.sudo().branch_head_id.name
            self.payer_name = self.company_id.default_supplier_id.name
        
    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            branch_code = ''
            if vals.get('company_id'):
                branch = self.env['res.company'].browse(vals['company_id'])
                branch_code = branch.code or ''

            vals['name'] = self.env['ir.sequence'].get_sequence_code('K',branch_code)

        create = super(TwListingCetakKwitansi, self).create(vals_list)
        
        return create
    
    def unlink(self):
        for data in self:
            if data.state != 'draft':
                raise Warning('Transaksi yang berstatus selain Draft tidak bisa dihapus !')
        
        return super(TwListingCetakKwitansi, self).unlink()

    # 13: action methods
    def action_listing_cetak_kwitansi_tree(self):
        domain = []
        list_view_id = self.env.ref('tw_listing_cetak_kwitansi.tw_listing_cetak_kwitansi_list_view').id
        form_view_id = self.env.ref('tw_listing_cetak_kwitansi.tw_listing_cetak_kwitansi_form_view').id
        search_view_id = self.env.ref('tw_listing_cetak_kwitansi.tw_listing_cetak_kwitansi_search_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Listing Cetak Kwitansi',
            'path': 'listing-cetak-kwitansi',
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': 'tw.listing.cetak.kwitansi',
            'domain': domain,
            'views': [(list_view_id, 'list'), (form_view_id, 'form')],
            'search_view_id': search_view_id,
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def action_update_faktur_pajak_kwitansi(self):
        return self.action_listing_cetak_kwitansi_wizard(wizard_form_type='faktur_pajak')
    
    def action_pembayaran_kwitansi(self):
        return self.action_listing_cetak_kwitansi_wizard(wizard_form_type='payment_kwt')

    def action_cancel_kwitansi(self):
        return self.action_listing_cetak_kwitansi_wizard(wizard_form_type='cancel_kwt')
    
    def action_listing_cetak_kwitansi_wizard(self, wizard_form_type='faktur_pajak'):
        self.ensure_one()
        name = 'Faktur Pajak'
        path = 'list-cetak-kwt-faktur-pajak'
        context = {
            'wizard_type': wizard_form_type,
            'search_default_fieldname': 1,
            'readonly_by_pass': 1
        }
        if wizard_form_type == 'faktur_pajak':
            context.update({'default_is_ppn': True})
        elif wizard_form_type == 'payment_kwt':
            name = 'Pembayaran'
            path = 'list-cetak-kwt-pembayaran'
        elif wizard_form_type == 'cancel_kwt':
            name = 'Cancel'
            path = 'list-cetak-kwt-cancel'

        form_view_id = self.env.ref('tw_listing_cetak_kwitansi.tw_listing_cetak_kwitansi_wizard_view').id

        return {
            'type': 'ir.actions.act_window',
            'name': (name),
            'path': path,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.listing.cetak.kwitansi',
            'view_id': False,
            'views': [(form_view_id, 'form')],
            'target': 'new',
            'res_id': self.id,
            'context': context
        }
    
    def action_post(self):
        if self.state != 'draft':
            raise Warning('State sudah tidak bisa diposting !')
        self.suspend_security().write({
            'state': 'posted',
            'confirm_uid': self._uid,
            'confirm_date': self._get_default_datetime()
        })

    def action_to_revisi(self):
        if self.state != 'posted':
            raise Warning('Tidak bisa di Revisi !')
        self.suspend_security().write({
            'state': 'draft',
            'print_to': False
        })

    def action_submit_faktur(self):
        self.is_ppn = True

    def action_submit_pembayaran(self):
        self.suspend_security().write({'state': 'paid'})

    def action_cancel(self):
        if self.state != 'posted':
            raise Warning('Tidak bisa di Cancel status bukan Posted !')
        self.suspend_security().write({
            'cancel_reason': self.cancel_reason,
            'state': 'cancelled',
            'cancel_uid': self._uid,
            'cancel_date': self._get_default_datetime()
        })

    def action_print_listing_cetak_kwitansi_pdf(self):
        self.ensure_one()
        if not self:
            raise Warning('Tidak ada data kwitansi yang bisa diproses !')
        
        if not self.env.user.has_group('tw_listing_cetak_kwitansi.group_tw_listing_cetak_kwitansi_button_print_pdf'):
            if self.print_to > 1:
                raise Warning('Print Kwitansi PDF sudah tidak bisa dicetak !')
            self.sudo().print_to += 1
            
        datas = {
            'id': self.id,
            'model': self._name,
            'data': self.read()[0],
            'user': self._uid
        }

        return self.env.ref('tw_listing_cetak_kwitansi.tw_listing_cetak_kwitansi_print_pdf_action_report').report_action(self, data=datas)

    # 14: private methods