# -*- coding: utf-8 -*-

from odoo import models, fields, Command
from odoo.exceptions import UserError


class DGIReceiptStnkWizard(models.TransientModel):
    """Wizard for syncing Penerimaan STNK data from DGI API.

    Menggunakan Output Template untuk mapping configuration.
    Engine handles: API call, parsing, dan relation lookup.
    Wizard handles: lot state validation dan grouping by birojasa.

    Output Template:
        {"id_spk": "idSPK", "vehicle_registration_receipt_line_ids": {"lot_id": "unit.nomorRangka"}}
    """
    _name = "tw.dgi.receipt.stnk.wizard"
    _inherit = "tw.dgi.wizard.mixin"
    _description = "DGI Receipt STNK Wizard"

    def action_get_dgi_data(self):
        """Main action: GET data dari DGI dan process"""
        return self.action_sync_dgi_data(endpoint_code='doch_receipt_stnk')

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
            return f"Penerimaan STNK SPK {id_spk}"
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
        """Create Penerimaan STNK dari engine-parsed values.

        Engine sudah handles:
        - Mapping unit.nomorRangka to lot_id (via relation mapping dengan idSPK)
        - Jika nomorRangka tidak tersedia, fallback lookup via idSPK → DSO → lot_id
        """
        model = self.env['tw.vehicle.registration.receipt'].sudo()
        line_items = vals.get('vehicle_registration_receipt_line_ids', [])
        id_spk = vals.get('id_spk')

        if not line_items:
            raise UserError("Tidak ada line items valid untuk diproses")

        # Group by birojasa
        receipt_vals = {}
        error_lots = []

        for line_item in line_items:
            # Engine mengembalikan (0, 0, dict) atau (Command, id, dict)
            # Gunakan index untuk menghindari error jika format tidak persis 3 elemen
            if not isinstance(line_item, (list, tuple)) or len(line_item) < 3:
                continue
            line_data = line_item[2]
            lot_id = line_data.get('lot_id')
            if not lot_id:
                continue

            lot = self.env['stock.lot'].sudo().browse(lot_id)

            # Validasi lot state
            if not self._validate_lot_receipt_stnk(lot):
                error_lots.append(lot.name or str(lot_id))
                continue

            # Build line vals seperti onchange_lot:
            # Ambil data dari lot (dari proses STNK sebelumnya),
            # jika tidak ada, ambil dari response API DGI.
            # Notice
            notice_number = lot.notice_number or line_data.get('notice_number') or False
            notice_date = lot.notice_date or line_data.get('notice_date') or False

            # STNK
            vehicle_registration_number = (
                lot.vehicle_registration_number
                or line_data.get('vehicle_registration_number')
                or False
            )
            stnk_date = lot.stnk_date or line_data.get('stnk_date') or False

            # Plat
            plate_number = (
                lot.plate_number
                or line_data.get('plate_number')
                or False
            )

            # is_receive_plate: ditentukan dari adanya plate_number hasil mapping
            is_receive_plate = bool(plate_number and not lot.plate_receipt_id)

            line_vals = {
                'lot_id': lot.id,
                'customer_stnk_id': lot.customer_stnk_id.id if lot.customer_stnk_id else False,
                # Notice
                'notice_number': notice_number,
                'notice_date': notice_date,
                'notice_received': bool(lot.notice_receipt_id),
                # STNK
                'vehicle_registration_number': vehicle_registration_number,
                'stnk_date': stnk_date,
                'vehicle_registration_received': bool(lot.vehicle_registration_receipt_id),
                # Plat
                'plate_number': plate_number,
                'plate_received': bool(lot.plate_receipt_id),
                'is_receive_plate': is_receive_plate,
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
                    'vehicle_registration_receipt_line_ids': [Command.create(line_vals)],
                }
            else:
                receipt_vals[bj_id]['vehicle_registration_receipt_line_ids'].append(
                    Command.create(line_vals))

        if not receipt_vals:
            raise UserError(
                f"Semua unit gagal validasi: {', '.join(error_lots)}"
            )

        # Create grouped records
        created_records = self._create_grouped_records(model, receipt_vals, 'Penerimaan STNK')

        extra_logs = []
        if error_lots:
            extra_logs.append(f"Skipped: {', '.join(error_lots)}")

        if created_records:
            extra_logs.append(f"Created {len(created_records)} transaksi Penerimaan STNK")
            return created_records.with_context(dgi_success_log_lines=extra_logs)

        raise UserError("Gagal membuat transaksi Penerimaan STNK")

    def _validate_lot_receipt_stnk(self, lot):
        """Validasi lot state untuk Penerimaan STNK."""
        # Check branch
        if lot.company_id.id != self.company_id.id:
            self._add_process_log(
                f"NoRangka {lot.name}: Branch mismatch", 'ERROR')
            return False

        # Check document state
        if lot.document_state != 'registration_process':
            self._add_process_log(
                f"NoRangka {lot.name}: Status {lot.document_state} "
                f"(harus registration_process)", 'ERROR')
            return False

        # Check sudah proses STNK
        if not lot.registration_process_date:
            self._add_process_log(
                f"NoRangka {lot.name}: Belum proses STNK", 'ERROR')
            return False

        # Check existing receipt
        existing = self.env['tw.vehicle.registration.receipt.line'].sudo().search([
            ('lot_id', '=', lot.id),
            ('vehicle_registration_receipt_id.state', 'not in', ['cancel', 'done']),
            ('state', '!=', 'cancel')
        ], limit=1)
        if existing:
            self._add_process_log(
                f"NoRangka {lot.name}: Sudah ada di {existing.vehicle_registration_receipt_id.name}", 'ERROR')
            return False

        # Check sudah selesai
        if lot.notice_receipt_id and lot.vehicle_registration_receipt_id and lot.plate_receipt_id:
            self._add_process_log(
                f"NoRangka {lot.name}: Sudah selesai diproses sepenuhnya", 'ERROR')
            return False

        return True

    def _create_grouped_records(self, model, grouped_vals, process_name):
        """Create records dari grouped values dict."""
        created = self.env['tw.vehicle.registration.receipt']

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
