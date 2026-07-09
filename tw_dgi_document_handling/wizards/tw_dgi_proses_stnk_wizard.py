# -*- coding: utf-8 -*-

from odoo import models, fields, Command
from odoo.exceptions import UserError


class DGIProsesStnkWizard(models.TransientModel):
    """Wizard for syncing Proses STNK data from DGI API.

    Menggunakan Response Mappings untuk filtering dan lookup configuration.
    Engine handles: API call, parsing, dan relation lookup (termasuk Wahana).
    Wizard handles: lot state validation dan grouping by birojasa.

    Wahana-specific mapping:
    - statusFakturSTNK = text → expected_value mencakup teks enum Wahana
    - lot_id lookup: json_path=idSPK, relation_lookup_field=dgi_spk_number
      (karena Wahana tidak mengirim nomorRangka)
    """
    _name = "tw.dgi.proses.stnk.wizard"
    _inherit = "tw.dgi.wizard.mixin"
    _description = "DGI Proses STNK Wizard"

    def action_get_dgi_data(self):
        """Main action: GET data dari DGI dan process"""
        return self.action_sync_dgi_data(endpoint_code='doch_proses_stnk')

    def _prepare_api_request_body(self):
        """Override to add idCustomer dan idSPK ke request body"""
        body = super()._prepare_api_request_body()
        body['idCustomer'] = ""
        if self.id_spk:
            body['idSpk'] = self.id_spk
        return body

    def _get_item_identifier(self, endpoint, item):
        """Override to extract DOCH-specific identifier for logging."""
        id_spk = item.get('idSPK')
        if id_spk:
            return f"Proses STNK SPK {id_spk}"
        return super()._get_item_identifier(endpoint, item)

    def _prepare_parse_response(self, endpoint, response_item):
        """Validasi awal sebelum engine parsing."""
        id_spk = response_item.get('idSPK')
        units = response_item.get('unit', [])

        if not units:
            self._add_process_log(
                f"ID SPK {id_spk}: Detail DOCH tidak ditemukan!", 'ERROR')
            return False

        return True

    def _create_record_from_response(self, endpoint, vals):
        """Create Proses STNK dari engine-parsed values.

        Engine sudah handles:
        - Filtering by statusFakturSTNK (termasuk Wahana text enum via mapping)
        - lot_id lookup: by chassis_number+idSPK (dealer lain)
          atau by idSPK→dgi_spk_number (Wahana via mapping)
        - Extracting faktur_stnk_number
        """
        model = self.env['tw.vehicle.registration.process'].sudo()
        line_items = vals.get('registration_process_line_ids', [])

        if not line_items:
            raise UserError("Tidak ada line items valid untuk diproses")

        # Group by birojasa (dari lot)
        proses_stnk_vals = {}
        error_lots = []

        for line_item in line_items:
            if not isinstance(line_item, (list, tuple)) or len(line_item) < 3:
                continue
            line_data = line_item[2]
            lot_id = line_data.get('lot_id')
            if not lot_id:
                continue

            lot = self.env['stock.lot'].sudo().browse(lot_id)

            # Validasi lot state
            if not self._validate_lot_proses_stnk(lot):
                error_lots.append(lot.name or str(lot_id))
                continue

            # Build line vals
            line_vals = {
                'lot_id': lot.id,
                'faktur_stnk_number': line_data.get('faktur_stnk_number'),
            }

            # Group by birojasa
            bj_id = lot.biro_jasa_id.id if lot.biro_jasa_id else False

            if bj_id not in proses_stnk_vals:
                proses_stnk_vals[bj_id] = {
                    'company_id': self.company_id.id,
                    'biro_jasa_id': bj_id,
                    'division': 'Unit',
                    'is_dgi': True,
                    'dgi_get_date': fields.Datetime.now(),
                    'dgi_get_uid': self.env.user.id,
                    'registration_process_line_ids': [Command.create(line_vals)],
                }
            else:
                proses_stnk_vals[bj_id]['registration_process_line_ids'].append(
                    Command.create(line_vals))

        if not proses_stnk_vals:
            raise UserError(
                f"Semua unit gagal validasi: {', '.join(error_lots)}"
            )

        # Create grouped records
        created_records = self._create_grouped_records(model, proses_stnk_vals, 'Proses STNK')

        extra_logs = []
        if error_lots:
            extra_logs.append(f"Skipped: {', '.join(error_lots)}")

        if created_records:
            extra_logs.append(f"Created {len(created_records)} transaksi Proses STNK")
            return created_records.with_context(dgi_success_log_lines=extra_logs)

        raise UserError("Gagal membuat transaksi Proses STNK")

    def _validate_lot_proses_stnk(self, lot):
        """Validasi lot state untuk Proses STNK."""
        if lot.company_id.id != self.company_id.id:
            self._add_process_log(
                f"NoRangka {lot.name}: Branch mismatch "
                f"({lot.company_id.code})", 'ERROR')
            return False

        if lot.document_state != 'document_receive':
            self._add_process_log(
                f"NoRangka {lot.name}: Status {lot.document_state} "
                f"(harus Terima Faktur)", 'ERROR')
            return False

        if not lot.vehicle_document_receive_date:
            self._add_process_log(
                f"NoRangka {lot.name}: Tanggal terima kosong", 'ERROR')
            return False

        existing_process = self.env['tw.vehicle.registration.process.line'].search([
            ('lot_id', '=', lot.id),
            ('registration_process_id.state', 'not in', ['cancel']),
            ('state', '!=', 'cancel'),
        ], limit=1)
        if existing_process:
            self._add_process_log(
                f"NoRangka {lot.name}: Sudah diproses di "
                f"{existing_process.registration_process_id.name}", 'ERROR')
            return False

        if lot.registration_process_date:
            self._add_process_log(
                f"NoRangka {lot.name}: Sudah selesai diproses", 'ERROR')
            return False

        return True

    def _create_grouped_records(self, model, grouped_vals, process_name):
        """Create records dari grouped values dict."""
        created = self.env['tw.vehicle.registration.process']

        if not grouped_vals:
            raise UserError(
                f'Processing {process_name}: Tidak ada data valid!')

        for bj_id, g_vals in grouped_vals.items():
            record = model.suspend_security().create(g_vals)
            record.invalidate_recordset()
            record.read(['name', 'biro_jasa_id'])
            created += record
            bj_name = record.biro_jasa_id.name if record.biro_jasa_id else 'Tanpa Birojasa'
            record_name = record.name or f'ID:{record.id}'
            self._add_process_log(
                f'Created {process_name}: {record_name} (Birojasa: {bj_name})', 'SUCCESS')

        return created
