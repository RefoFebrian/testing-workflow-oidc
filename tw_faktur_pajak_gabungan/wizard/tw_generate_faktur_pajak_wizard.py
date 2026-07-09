# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import api, fields, models, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)


class TwGenerateFakturPajakWizard(models.TransientModel):
    """
    Wizard untuk Generate Faktur Pajak Out secara manual.
    User bisa mencari transaksi yang belum memiliki nomor faktur pajak
    dan generate secara batch.
    """
    _name = "tw.generate.faktur.pajak.wizard"
    _description = "Generate Faktur Pajak Wizard"

    # 7: default methods

    # 8: fields
    master_model_id = fields.Many2one(
        'tw.master.model.pajak',
        string="Model Transaksi",
        required=True,
        help="Pilih model transaksi yang ingin dicari"
    )
    transaction = fields.Char(
        string="Transaction Search",
        help="Masukkan sebagian nama/nomor transaksi (minimal 10 karakter)"
    )
    company_id = fields.Many2one(
        'res.company',
        string="Branch",
        help="Filter transaksi berdasarkan branch"
    )
    start_date = fields.Date(
        string="Start Date",
        help="Filter transaksi mulai dari tanggal ini"
    )
    end_date = fields.Date(
        string="End Date",
        help="Filter transaksi sampai tanggal ini"
    )
    is_found = fields.Boolean(string="Is Found", default=False)
    message = fields.Text(string="Message", readonly=True)
    
    # 9: relation fields
    transaction_ids = fields.One2many(
        'tw.generate.faktur.pajak.wizard.line',
        'wizard_id',
        string="Transactions"
    )

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_search(self):
        """
        Search transaksi berdasarkan input transaction.
        Minimal 10 karakter untuk mencegah query yang terlalu besar.
        """
        self.ensure_one()
        
        # Clear existing lines
        self.transaction_ids.unlink()
        self.is_found = False
        self.message = False

        if not self.master_model_id:
            raise Warning(_("Harap pilih Model Transaksi terlebih dahulu."))

        model_name = self.master_model_id.model_name
        
        # Validasi model exists
        if model_name not in self.env:
            raise Warning(_("Model '%s' tidak ditemukan di sistem.") % model_name)

        # Validasi model memiliki field yang diperlukan
        model_fields = self.env[model_name].fields_get()
        if 'faktur_pajak_out_id' not in model_fields:
            raise Warning(_(
                "Model '%s' tidak memiliki field 'faktur_pajak_out_id'. "
                "Pastikan model sudah inherit dari tw.faktur.pajak.mixin."
            ) % model_name)

        # Tentukan field name dan date
        name_field = 'name'
        if 'number' in model_fields:
            name_field = 'number'
        
        date_field = 'date'
        if 'date_order' in model_fields:
            date_field = 'date_order'

        # Build domain
        domain = [
            ('faktur_pajak_out_id', '=', False),  # Belum punya faktur pajak
        ]

        # Filter by transaction name
        if self.transaction and len(self.transaction) >= 10:
            domain.append((name_field, 'ilike', self.transaction.upper()))
        elif self.transaction:
            raise Warning(_("Harap masukkan minimal 10 karakter untuk pencarian nama transaksi."))

        # Filter by company/branch
        if self.company_id:
            domain.append(('company_id', '=', self.company_id.id))

        # Filter by periode
        if self.start_date:
            domain.append((date_field, '>=', self.start_date))
        if self.end_date:
            domain.append((date_field, '<=', self.end_date))

        # Validasi: minimal salah satu filter harus diisi
        if not self.transaction and not self.company_id and not self.start_date and not self.end_date:
            raise Warning(_("Harap isi minimal salah satu filter: Transaction, Branch, atau Periode."))
        
        # Tambahkan filter is_combined_tax jika ada
        if 'is_combined_tax' in model_fields:
            domain.append(('is_combined_tax', '=', False))

        # Search transaksi
        results = self.env[model_name].sudo().search(domain, limit=100)

        if not results:
            raise Warning(_("Tidak ditemukan transaksi dengan kriteria tersebut."))

        # Prepare ir.model reference
        model_id = self.env['ir.model'].sudo().search(
            [('model', '=', model_name)], limit=1
        )

        # Create lines - SAVE TO DATABASE using create()
        line_obj = self.env['tw.generate.faktur.pajak.wizard.line']
        for rec in results:
            trx_name = getattr(rec, name_field, False) or rec.name or str(rec.id)
            release_date = getattr(rec, date_field, False)
            
            # Convert datetime to date if needed
            if release_date and hasattr(release_date, 'date'):
                release_date = release_date.date()
            
            thn_penggunaan = int(release_date.strftime('%Y'))
            
            line_obj.create({
                'wizard_id': self.id,
                'model_id': model_id.id if model_id else False,
                'model_name': model_name,
                'transaction_id': rec.id,
                'transaction_name': trx_name,
                'release_date': release_date,
                'thn_penggunaan': thn_penggunaan,
            })

        self.is_found = True
        self.message = _("Ditemukan %s transaksi.") % len(results)
        
        # Reload wizard to show results
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.generate.faktur.pajak.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_generate_all(self):
        """
        Generate faktur pajak untuk semua transaksi yang ada di list.
        """
        self.ensure_one()
        
        # Reload lines from database
        lines = self.transaction_ids
        
        if not lines:
            raise Warning(_("Tidak ada transaksi yang ditemukan untuk di-generate. Silakan klik 'Search' terlebih dahulu."))

        messages = []
        success_count = 0
        fail_count = 0

        for line in lines:
            try:
                result = line.action_generate_faktur_pajak()
                trx_display = line.transaction_name or str(line.transaction_id)
                if result:
                    messages.append(
                        _("✓ Faktur pajak berhasil terbentuk untuk transaksi %s") % trx_display
                    )
                    success_count += 1
                else:
                    messages.append(
                        _("✗ Faktur pajak gagal terbentuk untuk transaksi %s") % trx_display
                    )
                    fail_count += 1
            except Exception as e:
                trx_display = line.transaction_name or str(line.transaction_id)
                messages.append(
                    _("✗ Error pada transaksi %s: %s") % (trx_display, str(e))
                )
                fail_count += 1
                _logger.error("Error generating faktur pajak for %s: %s", trx_display, str(e))

        # Show result in new wizard
        summary = _("Berhasil: %s | Gagal: %s\n\n") % (success_count, fail_count)
        
        return {
            'name': _('Hasil Generate Faktur Pajak'),
            'type': 'ir.actions.act_window',
            'res_model': 'tw.generate.faktur.pajak.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('tw_faktur_pajak_gabungan.tw_generate_faktur_pajak_wizard_message_form').id,
            'target': 'new',
            'context': {
                'default_message': summary + '\n'.join(messages)
            }
        }

    # 14: private methods


class TwGenerateFakturPajakWizardLine(models.TransientModel):
    """
    Line untuk wizard Generate Faktur Pajak.
    Menyimpan transaksi yang ditemukan dan akan di-generate.
    """
    _name = "tw.generate.faktur.pajak.wizard.line"
    _description = "Generate Faktur Pajak Wizard Line"

    # 8: fields
    wizard_id = fields.Many2one(
        'tw.generate.faktur.pajak.wizard',
        string="Wizard",
        ondelete='cascade'
    )
    model_id = fields.Many2one('ir.model', string="Model", readonly=True)
    model_name = fields.Char(string="Model Name", readonly=True)
    transaction_name = fields.Char(string="Transaction Name", readonly=True)
    transaction_id = fields.Integer(string="Transaction ID", readonly=True)
    release_date = fields.Date(string="Release Date", readonly=True)
    thn_penggunaan = fields.Char(string="Tahun Penggunaan", readonly=True)

    # 13: action methods
    def action_generate_faktur_pajak(self):
        """
        Generate faktur pajak untuk satu transaksi.
        Memanggil method get_number_of_faktur_pajak dari tw.faktur.pajak.out
        """
        self.ensure_one()
        
        # Gunakan model_name yang disimpan langsung
        model_name = self.model_name
        
        if not model_name or not self.transaction_id:
            _logger.warning("Missing model_name or transaction_id: %s, %s", model_name, self.transaction_id)
            return False

        try:
            transaction = self.env[model_name].browse(self.transaction_id)
            transaction.get_number_faktur_pajak()
            return True
        except Exception as e:
            _logger.error("Error generating faktur pajak: %s", str(e))
            raise
