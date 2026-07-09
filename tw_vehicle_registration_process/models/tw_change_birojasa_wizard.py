# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib


class TWChangeBirojasaWizard(models.TransientModel):
    """
    Wizard untuk mengganti Biro Jasa pada proses STNK yang sudah berstatus Posted.

    Alur konfirmasi:
    1. Validasi input (biro jasa baru ≠ lama, record ada & statusnya Posted)
    2. Update biro_jasa_id pada tw.vehicle.registration.process dan semua stock.lot terkait
    3. Per lot: reverse journal Accrue BBN lama (buat jurnal baru balikan)
    4. Per lot: buat journal Accrue BBN baru dengan Biro Jasa yang baru
    5. Update referensi accure_bbn_move_id di lot ke journal baru
    """

    _name = "tw.change.birojasa.wizard"
    _description = "Change Biro Jasa Wizard"

    # 8: fields
    old_biro_jasa_id = fields.Many2one('res.partner', string='Biro Jasa Lama', readonly=True)

    available_biro_jasa_ids = fields.Many2many('res.partner', compute='_compute_available_biro_jasa_ids')
    new_biro_jasa_id = fields.Many2one(
        'res.partner', string='Biro Jasa Baru', required=True,
        domain="[('id', 'in', available_biro_jasa_ids), ('id', '!=', old_biro_jasa_id)]"
    )

    @api.depends('old_biro_jasa_id')
    def _compute_available_biro_jasa_ids(self):
        for rec in self:
            active_id = self.env.context.get('active_id')
            if active_id:
                record = self.env['tw.vehicle.registration.process'].browse(active_id)
                company = record.company_id
                if company and company.branch_setting_id:
                    birojasa_settings = company.branch_setting_id.birojasa_setting_ids
                    rec.available_biro_jasa_ids = birojasa_settings.mapped('biro_jasa_id').ids
                    continue
            rec.available_biro_jasa_ids = False

    # 12: action methods
    def action_confirm(self):
        """Main entry point: validasi dan update biro jasa."""
        self.ensure_one()
        self._check_validity()

        record = self._get_registration_process()
        self._update_biro_jasa(record)

    # 14: private methods
    def _get_registration_process(self):
        """Ambil record tw.vehicle.registration.process dari context active_id."""
        active_id = self.env.context.get('active_id')
        record = self.env['tw.vehicle.registration.process'].suspend_security().browse(active_id)
        if not record.exists():
            raise ValidationError(_("Record proses STNK tidak ditemukan."))
        return record

    def _check_validity(self):
        """Validasi input sebelum proses dijalankan."""
        self.ensure_one()
        if self.old_biro_jasa_id == self.new_biro_jasa_id:
            raise ValidationError(_("Biro Jasa baru tidak boleh sama dengan Biro Jasa lama."))

        record = self._get_registration_process()
        if not record.registration_process_line_ids:
            raise ValidationError(_("Tidak ada engine yang terdaftar pada proses STNK ini."))

    def _update_biro_jasa(self, record):
        """
        Update biro_jasa_id pada registration process.
        Update lot akan dilakukan saat konfirmasi proses STNK (action_confirm).

        Args:
            record: tw.vehicle.registration.process record
        """
        record.suspend_security().write({
            'biro_jasa_id': self.new_biro_jasa_id.id,
            'old_biro_jasa_id': self.old_biro_jasa_id.id,
        })
