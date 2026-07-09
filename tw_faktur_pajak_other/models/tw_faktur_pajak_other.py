# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning, ValidationError

# 4: imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class TwFakturPajakOther(models.Model):
    """
    Model untuk mencatat faktur pajak untuk transaksi lain-lain (Other).
    Digunakan untuk transaksi yang tidak tercakup dalam model standar
    seperti Sales Order, Invoice, atau Payment.
    """

    _name = "tw.faktur.pajak.other"
    _description = "Faktur Pajak Other"
    _order = "id desc"

    # 8: Fields
    name = fields.Char(string='No. Dokumen', readonly=True, default='/', copy=False)
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today, readonly=True)
    tgl_terbit = fields.Date(string='Tanggal Terbit',required=True)
    thn_penggunaan = fields.Integer(string='Tahun Penggunaan',required=True)
    pajak_gabungan = fields.Boolean(string='Pajak Gabungan')
    untaxed_amount = fields.Float(string='Untaxed Amount (DPP)', required=True)
    tax_amount = fields.Float(string='Tax Amount (PPN)', required=True)
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
    ], string='State', default='draft', readonly=True, copy=False)
    kwitansi_no = fields.Char(string='No. Kwitansi')
    memo = fields.Char(string='Memo')

    # Core Tax Fields
    is_coretax = fields.Boolean(string='Coretax')
    kode_barang = fields.Char(string='Kode Barang', default='B')
    uom = fields.Char(string='UoM', default='UM.0033')

    # 9: Relation Fields
    faktur_pajak_out_id = fields.Many2one('tw.faktur.pajak.out', string='No. Faktur Pajak', domain="[('state', '=', 'open')]")
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    company_id = fields.Many2one('res.company', string='Branch', required=True, readonly=True, default=lambda self: self.env.company)

    # Audit Trail Fields
    confirm_uid = fields.Many2one('res.users', string="Posted by", readonly=True, copy=False)
    confirm_date = fields.Datetime(string='Posted on', readonly=True, copy=False)

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('untaxed_amount', 'tax_amount')
    def _compute_total_amount(self):
        """Compute total amount from untaxed + tax amount."""
        for record in self:
            record.total_amount = record.untaxed_amount + record.tax_amount

    @api.onchange('thn_penggunaan')
    def _onchange_thn_penggunaan(self):
        """Validasi tahun penggunaan harus 4 digit."""
        if self.thn_penggunaan:
            tahun_str = str(self.thn_penggunaan).replace(".", "")
            if len(tahun_str) != 4:
                self.thn_penggunaan = False
                return {
                    'warning': {
                        'title': _('Perhatian!'),
                        'message': _('Tahun penggunaan harus 4 digit!')
                    }
                }

    @api.onchange('faktur_pajak_out_id')
    def _onchange_faktur_pajak_out_id(self):
        """Set tahun penggunaan dari faktur pajak yang dipilih."""
        self.thn_penggunaan = False
        if self.faktur_pajak_out_id:
            # Get year from release_date of faktur pajak
            if self.faktur_pajak_out_id.release_date:
                self.thn_penggunaan = self.faktur_pajak_out_id.release_date.year

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence and validate data."""
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].get_sequence_code(
                    'FPO',
                    self.env.company.code
                )
            # Validate on create
            self._validate_faktur_pajak_other(vals)
        return super(TwFakturPajakOther, self).create(vals_list)

    def unlink(self):
        """Prevent deletion if not in draft state."""
        for record in self:
            if record.state != 'draft':
                raise Warning(_("Faktur Pajak Other yang sudah diposting tidak dapat dihapus!"))
        return super(TwFakturPajakOther, self).unlink()

    # 13: action methods
    def action_post(self):
        """
        Konfirmasi Faktur Pajak Other dan link ke Faktur Pajak Out.
        Jika menggunakan Core Tax, juga buat line di tw.faktur.pajak.out.line.
        """
        self.ensure_one()

        # Validate before posting
        self._validate_before_post()

        # Check faktur pajak state
        if self.faktur_pajak_out_id.state != 'open':
            raise Warning(_("Nomor faktur pajak telah digunakan oleh transaksi lain!"))

        # Get model reference
        model_id = self.env['ir.model'].search([
            ('model', '=', 'tw.faktur.pajak.other')
        ], limit=1)

        # Check if using Core Tax implementation
        is_old_settings = self.env['tw.faktur.pajak.out'].sudo()._check_implementation()

        # Prepare line values for Core Tax
        line_vals = []
        if not is_old_settings:
            # Lookup default PPN tax for Core Tax implementation
            ppn_tax = self.env['account.tax'].sudo().search([
                ('type_tax_use', '=', 'sale'),
                ('amount', '=', 11),  # 11% PPN
                ('company_id', '=', self.company_id.id),
            ], limit=1)
            
            # Core Tax implementation: Create line for Faktur Pajak Out
            line_vals = [(0, 0, {
                'kode_barang': self.kode_barang if self.is_coretax else 'B',
                'uom': self.uom if self.is_coretax else 'UM.0033',
                'amount': self.total_amount,
                'untaxed_amount': self.untaxed_amount,
                'ppn': self.tax_amount,
                'qty': 1,
                'product_name': self.memo or self.name,
                'tax_ids': [(6, 0, ppn_tax.ids)] if ppn_tax else False,
            })]

        # Update Faktur Pajak Out
        update_vals = {
            'model_id': model_id.id,
            'is_combined_tax': self.pajak_gabungan,
            'partner_id': self.partner_id.id,
            'untaxed_amount': self.untaxed_amount,
            'tax_amount': self.tax_amount,
            'amount_total': self.total_amount,
            'date': self.tgl_terbit,
            'transaction_id': self.id,
            'ref': self.name,
            'company_id': self.company_id.id,
            'state': 'close',
        }

        # Add line_ids if using Core Tax
        if line_vals:
            update_vals['line_ids'] = line_vals

        self.faktur_pajak_out_id.write(update_vals)

        # Update this record
        self.write({
            'state': 'posted',
            'confirm_uid': self.env.user.id,
            'confirm_date': fields.Datetime.now(),
        })

        return True

    # 14: private methods
    def _validate_faktur_pajak_other(self, vals):
        """
        Validasi data faktur pajak other pada saat create.
        
        Args:
            vals: Dictionary of values to validate
        """
        thn_penggunaan = vals.get('thn_penggunaan')
        if thn_penggunaan:
            tahun_str = str(thn_penggunaan).replace(".", "")
            if len(tahun_str) != 4:
                raise ValidationError(_("Tahun penggunaan harus 4 digit!"))

    def _validate_before_post(self):
        """
        Validasi data sebelum melakukan posting.
        Memeriksa tanggal terbit dan tahun penggunaan.
        """
        self.ensure_one()

        if not self.tgl_terbit:
            raise Warning(_("Tanggal terbit harus diisi!"))

        if not self.thn_penggunaan:
            raise Warning(_("Tahun penggunaan harus diisi!"))

        tgl_terbit = self.tgl_terbit
        date_now = date.today()
        last_month = date_now.replace(day=1) - relativedelta(months=1)

        # Validate tahun penggunaan
        thn_penggunaan_str = str(self.thn_penggunaan).replace(".", "")
        thn_penggunaan_int = int(thn_penggunaan_str)

        if len(thn_penggunaan_str) != 4:
            raise Warning(_("Tahun penggunaan harus 4 digit!"))

        if thn_penggunaan_int != tgl_terbit.year:
            raise Warning(_(
                "Tahun penggunaan dan tahun tanggal terbit tidak sesuai, "
                "silahkan dicek kembali!"
            ))

        # Validate tgl_terbit against faktur pajak out
        if self.faktur_pajak_out_id and self.faktur_pajak_out_id.release_date:
            fp_release_date = self.faktur_pajak_out_id.release_date
            if tgl_terbit < fp_release_date:
                raise Warning(_(
                    "Tanggal terbit faktur pajak other kurang dari tanggal terbit "
                    "faktur pajak, silahkan dicek kembali!"
                ))

        # Validate tgl_terbit not too old
        if tgl_terbit < last_month:
            raise Warning(_("Masa tanggal terbit terlalu lama dari bulan sekarang!"))

        # Validate tgl_terbit not in future
        if tgl_terbit > date_now:
            raise Warning(_("Tanggal terbit tidak boleh melebihi hari ini!"))
