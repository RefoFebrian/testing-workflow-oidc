# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

class TwFakturPajakGabungan(models.Model):
    _name = "tw.faktur.pajak.gabungan"
    _description = "Faktur Pajak Gabungan"
    _inherit = ['tw.faktur.pajak.mixin']

    # 8: relation fields
    name = fields.Char( string="Name",  readonly=True,  default='/',compute="_compute_name",store=True, copy=False)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    date = fields.Date(string="Date", required=True, default=fields.Date.context_today)
    date_pajak = fields.Date(string='Date of Faktur Pajak', help="Tanggal yang akan digunakan saat faktur pajak di-generate.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancel','Cancelled')
    ], string='State', readonly=True, default='draft', copy=False)
    amount = fields.Float('amount',compute='_compute_amount')
    untaxed_amount = fields.Float('Untaxed Amount',compute='_compute_amount')
    tax_amount = fields.Float('Tax Amount',compute='_compute_amount')

    # Field Audit Trail
    confirm_uid = fields.Many2one('res.users', string="Confirmed by", readonly=True, copy=False)
    confirm_date = fields.Datetime('Confirmed on', readonly=True, copy=False)
    
    # 9: relation fields
    master_model_id = fields.Many2one('tw.master.model.pajak', string="Model Transaksi", required=True, readonly=True)
    pajak_gabungan_line = fields.One2many('tw.faktur.pajak.gabungan.line','pajak_gabungan_id', string="Detail Transaksi",readonly=True)
    faktur_pajak_out_id = fields.Many2one('tw.faktur.pajak.out', string="Faktur Pajak Out", readonly=True, copy=False)
    company_id = fields.Many2one('res.company', string='Branch', required=True, readonly=True, default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for data in self:
            if data.id and not data.name and data.state or data.name == '/':
                data.name = self.env['ir.sequence'].get_sequence_code('FPG',data.company_id.code)
    
    @api.onchange('end_date')
    def _onchange_end_date(self):
        if self.end_date and self.start_date and self.start_date > self.end_date:
            self.end_date = False
            return {
                'warning': {
                    'title': _('Perhatian!'),
                    'message': _("End Date tidak boleh kurang dari Start Date."),
                }
            }

    @api.onchange('master_model_id')
    def _onchange_master_model_id(self):
        """
        Validasi "Jegatan": Memeriksa apakah modul jembatan Coretax
        untuk model yang dipilih sudah ter-install.
        """
        # Kosongkan baris detail setiap kali model diubah
        self.pajak_gabungan_line = [(5, 0, 0)]

        if self.master_model_id:
            module_name = self.master_model_id.module_name
            
            module_jembatan = self.env['ir.module.module'].search([
                ('name', '=', module_name),
                ('state', '=', 'installed')
            ], limit=1)

            if not module_jembatan:
                self.master_model_id = False
                raise Warning(
                    _('Modul jembatan "%s" untuk memproses model ini tidak ditemukan atau belum ter-install. Harap hubungi Administrator.') % (module_name)
                )

    @api.depends('pajak_gabungan_line.total_amount')
    def _compute_amount(self):
        for data in self:
            data.amount = sum(data.pajak_gabungan_line.mapped('total_amount'))
            data.untaxed_amount = sum(data.pajak_gabungan_line.mapped('untaxed_amount'))
            data.tax_amount = sum(data.pajak_gabungan_line.mapped('tax_amount'))

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        return super(TwFakturPajakGabungan, self).create(vals_list)

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise Warning(_("Anda tidak dapat menghapus dokumen yang tidak berstatus Draft."))
        return super(TwFakturPajakGabungan, self).unlink()

    # 13: action methods
    def action_search_transactions(self):
        """
        Mengisi baris detail berdasarkan filter di header.
        """
        self.ensure_one()
        if not self.master_model_id:
            raise Warning(_("Harap pilih Model Transaksi terlebih dahulu."))

        self.pajak_gabungan_line = [(5, 0, 0)]

        # Siapkan domain pencarian
        # Asumsi field tanggal di model sumber adalah 'date'
        date_field = 'create_date' 
        model_name = self.master_model_id.model_name
        
        # Validasi sederhana
        if model_name not in self.env or 'is_combined_tax' not in self.env[model_name].fields_get():
            raise Warning(
                _("Model %s tidak valid atau tidak memiliki field 'is_combined_tax' untuk digabungkan.") % (model_name)
            )
            
        domain = [
            ('company_id', '=', self.company_id.id),
            ('partner_id', '=', self.partner_id.id),
            ('division', '=', self.division),
            ('faktur_pajak_out_id', '=', False), # Dari mixin
            ('is_combined_tax', '=', True), # Dari mixin
            ('state', 'not in', ['draft', 'cancel']) 
        ]
        
        if self.start_date:
            domain.append((date_field, '>=', self.start_date))
        if self.end_date:
            domain.append((date_field, '<=', self.end_date))

        source_docs = self.env[model_name].search(domain)

        new_lines = []
        for doc in source_docs:
            new_lines.append((0, 0, {
                'name': doc.name,
                'date': getattr(doc, date_field),
                'total_amount': doc.amount_total,
                'untaxed_amount': doc.amount_untaxed,
                'tax_amount': doc.amount_tax,
                'model': model_name,
                'source_doc_id': f"{model_name},{doc.id}"
            }))
        
        if not new_lines:
            raise Warning(_("Tidak ada transaksi yang ditemukan untuk digabungkan."))
            
        self.pajak_gabungan_line = new_lines
        return True

    def action_confirm(self):
        """
        Mengkonfirmasi FPG dan memanggil arsitektur Coretax 
        untuk membuat satu FPO.
        """
        if not self.pajak_gabungan_line:
            raise Warning(_("Silakan klik tombol 'Search Transactions' terlebih dahulu."))
        
        # Panggil method 'get_number_faktur_pajak' dari Coretax Mixin
        # Ini akan memicu 'create_faktur_pajak' -> '_prepare_faktur_pajak_vals'
        faktur_pajak_out = self.get_number_faktur_pajak()
        if not faktur_pajak_out:
            raise Warning(_("Tidak ada nomor faktur pajak yang bisa di gunakan untuk branch %s dan release date dibawah %s, silahkan cek kembali") % (self.company_id.name, self.date))

        self.write({
            'state': 'confirmed',
            'confirm_uid': self.env.user.id,
            'confirm_date': fields.Datetime.now(),
            'faktur_pajak_out_id': faktur_pajak_out.id,
        })
        
        # Link semua dokumen sumber ke FPO yang baru
        for line in self.pajak_gabungan_line:
            source_doc = line.source_doc_id
            if source_doc:
                source_doc.write({'faktur_pajak_out_id': faktur_pajak_out.id})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_set_to_draft(self):
        self.write({'state': 'draft'})

    def action_print_report_pdf(self):
        self.ensure_one()
        return self.env.ref('tw_faktur_pajak_gabungan.action_report_faktur_pajak_gabungan').report_action(self)

    # 14: private methods
