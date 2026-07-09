# -*- coding: utf-8 -*-

from odoo import models, fields, Command
from odoo.exceptions import UserError


class DGIReceiptBpkbWizard(models.TransientModel):
    """Wizard for syncing Penerimaan BPKB data from DGI API.

    Menggunakan Output Template untuk mapping configuration.
    Engine handles: API call, parsing, dan relation lookup.
    Wizard handles: lot state validation dan grouping by birojasa.

    Output Template:
        {"id_spk": "idSPK", "vehicle_ownership_receipt_line_ids": {"lot_id": "unit.nomorRangka"}}
    """
    _name = "tw.dgi.receipt.bpkb.wizard"
    _inherit = "tw.dgi.wizard.mixin"
    _description = "DGI Receipt BPKB Wizard"

    def action_get_dgi_data(self):
        """Main action: GET data dari DGI dan process"""
        return self.action_sync_dgi_data(endpoint_code='doch_receipt_bpkb')

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
            return f"Penerimaan BPKB SPK {id_spk}"
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
        """Create Penerimaan BPKB dari engine-parsed values.

        Engine sudah handles:
        - Filtering by statusFakturSTNK = 5
        - Mapping unit.nomorRangka to lot_id (via relation mapping with idSPK)
        """
        model = self.env['tw.vehicle.ownership.receipt'].sudo()
        line_items = vals.get('vehicle_ownership_receipt_line_ids', [])

        if not line_items:
            raise UserError("Tidak ada line items valid untuk diproses")

        # Group by birojasa
        receipt_vals = {}
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
            if not self._validate_lot_receipt_bpkb(lot):
                error_lots.append(lot.name or str(lot_id))
                continue

            # Build line vals
            line_vals = {
                'lot_id': lot.id,
                'vehicle_ownership_number': line_data.get('vehicle_ownership_number'),
                'vehicle_ownership_date': line_data.get('vehicle_ownership_date'),
            }

            # Group by birojasa (dari lot)
            bj_id = lot.biro_jasa_id.id if lot.biro_jasa_id else False

            if bj_id not in receipt_vals:
                receipt_vals[bj_id] = {
                    'company_id': lot.company_id.id or self.company_id.id,
                    'biro_jasa_id': bj_id,
                    'division': 'Unit',
                    'is_dgi': True,
                    'dgi_get_date': fields.Datetime.now(),
                    'dgi_get_uid': self.env.user.id,
                    'vehicle_ownership_receipt_line_ids': [Command.create(line_vals)],
                }
            else:
                receipt_vals[bj_id]['vehicle_ownership_receipt_line_ids'].append(
                    Command.create(line_vals))

        if not receipt_vals:
            raise UserError(
                f"Semua unit gagal validasi: {', '.join(error_lots)}"
            )

        # Create grouped records
        created_records = self._create_grouped_records(model, receipt_vals, 'Penerimaan BPKB')

        extra_logs = []
        if error_lots:
            extra_logs.append(f"Skipped: {', '.join(error_lots)}")

        if created_records:
            extra_logs.append(f"Created {len(created_records)} transaksi Penerimaan BPKB")
            return created_records.with_context(dgi_success_log_lines=extra_logs)

        raise UserError("Gagal membuat transaksi Penerimaan BPKB")

    def _validate_lot_receipt_bpkb(self, lot):
        """Validasi lot state untuk Penerimaan BPKB."""
        # Check branch
        if lot.company_id.id != self.company_id.id:
            self._add_process_log(
                f"NoRangka {lot.name}: Branch mismatch", 'ERROR')
            return False

        # Check document state
        if lot.document_state != 'registration_process':
            self._add_process_log(
                f"NoRangka {lot.name}: Status {lot.document_state}", 'ERROR')
            return False

        # Check sudah proses STNK
        if not lot.registration_process_date:
            self._add_process_log(
                f"NoRangka {lot.name}: Belum proses STNK", 'ERROR')
            return False

        # Check existing receipt
        existing = self.env['tw.vehicle.ownership.receipt.line'].sudo().search([
            ('lot_id', '=', lot.id),
            ('vehicle_ownership_receipt_id.state', 'not in', ['cancel', 'done']),
            ('state', '!=', 'cancel')
        ], limit=1)
        if existing:
            self._add_process_log(
                f"NoRangka {lot.name}: Sudah ada di {existing.vehicle_ownership_receipt_id.name}", 'ERROR')
            return False

        # Check sudah terima STNK
        if not lot.vehicle_registration_receipt_date and not lot.notice_receipt_date:
            self._add_process_log(
                f"NoRangka {lot.name}: Belum diproses di Penerimaan STNK", 'ERROR')
            return False

        return True

    def _create_grouped_records(self, model, grouped_vals, process_name):
        """Create records dari grouped values dict."""
        created = self.env['tw.vehicle.ownership.receipt']

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
