# -*- coding: utf-8 -*-

from odoo import models, fields, Command
from odoo.exceptions import UserError


class TWDGIHandoverBpkbWizard(models.TransientModel):
    """Wizard for syncing Penyerahan BPKB data from DGI API.

    Menggunakan Output Template untuk mapping configuration.
    Engine handles: API call, parsing, dan relation lookup.
    Wizard handles: lot state validation dan grouping by customer.

    Output Template:
        {"id_spk": "idSPK", "receiver": "namaPenerima", "ownership_handover_line_ids": {"lot_id": "unit.nomorRangka"}}
    """
    _name = "tw.dgi.handover.bpkb.wizard"
    _inherit = "tw.dgi.wizard.mixin"
    _description = "DGI Handover BPKB Wizard"

    def action_get_dgi_data(self):
        """Main action: GET data dari DGI dan process"""
        return self.action_sync_dgi_data(endpoint_code='doch_handover_bpkb')

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
            return f"Penyerahan BPKB SPK {id_spk}"
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

    def _find_lot_by_spk(self, id_spk):
        """Fallback: Cari lot hanya berdasarkan dgi_spk_number (Wahana)."""
        return self.env['stock.lot'].sudo().search([
            ('dgi_spk_number', '=', id_spk),
            ('company_id', '=', self.company_id.id),
        ], limit=1)

    def _create_record_from_response(self, endpoint, vals):
        """Create Penyerahan BPKB dari engine-parsed values.

        Engine sudah handles:
        - Filtering by statusFakturSTNK = 6
        - Mapping unit.nomorRangka to lot_id (via relation mapping with idSPK)
        - Extracting namaPenerima -> receiver
        """
        model = self.env['tw.vehicle.ownership.handover'].sudo()
        line_items = vals.get('ownership_handover_line_ids', [])
        receiver = vals.get('receiver', '')
        id_spk = vals.get('_idSPK') or vals.get('id_spk', '')

        if not line_items:
            raise UserError("Tidak ada line items valid untuk diproses")

        # Group by customer
        handover_vals = {}
        error_lots = []

        for line_item in line_items:
            if not isinstance(line_item, (list, tuple)) or len(line_item) < 3:
                continue
            line_data = line_item[2]
            lot_id = line_data.get('lot_id')
            lot = None

            if lot_id:
                lot = self.env['stock.lot'].sudo().browse(lot_id)
            elif id_spk:
                lot = self._find_lot_by_spk(id_spk)
                if lot:
                    self._add_process_log(
                        f"SPK {id_spk}: nomorRangka tidak ada, fallback lookup → Lot {lot.name}", 'INFO')
                else:
                    self._add_process_log(
                        f"SPK {id_spk}: Lot tidak ditemukan", 'ERROR')
                    error_lots.append(id_spk)
                    continue

            if not lot or not lot.exists():
                continue

            # receiver dari line_data (Wahana namaPenerima dalam unit) atau dari root
            line_receiver = line_data.get('receiver') or receiver

            # Validasi lot state
            if not self._validate_lot_handover_bpkb(lot):
                error_lots.append(lot.name or str(lot_id))
                continue

            # Build line vals
            line_vals = {
                'lot_id': lot.id,
                'bpkb_handover_date': line_data.get('bpkb_handover_date'),
            }

            # Group by customer
            cust_id = lot.customer_stnk_id.id if lot.customer_stnk_id else False

            if cust_id not in handover_vals:
                handover_vals[cust_id] = {
                    'company_id': lot.company_id.id or self.company_id.id,
                    'partner_id': cust_id,
                    'receiver': line_receiver or (lot.customer_stnk_id.name if lot.customer_stnk_id else ''),
                    'division': 'Unit',
                    'is_dgi': True,
                    'dgi_get_date': fields.Datetime.now(),
                    'dgi_get_uid': self.env.user.id,
                    'ownership_handover_line_ids': [Command.create(line_vals)],
                }
            else:
                handover_vals[cust_id]['ownership_handover_line_ids'].append(
                    Command.create(line_vals))

        if not handover_vals:
            raise UserError(
                f"Semua unit gagal validasi: {', '.join(error_lots)}"
            )

        # Create grouped records
        created_records = self._create_grouped_records(model, handover_vals, 'Penyerahan BPKB')

        extra_logs = []
        if error_lots:
            extra_logs.append(f"Skipped: {', '.join(error_lots)}")

        if created_records:
            extra_logs.append(f"Created {len(created_records)} transaksi Penyerahan BPKB")
            return created_records.with_context(dgi_success_log_lines=extra_logs)

        raise UserError("Gagal membuat transaksi Penyerahan BPKB")

    def _validate_lot_handover_bpkb(self, lot):
        """Validasi lot state untuk Penyerahan BPKB (khusus customer cash)."""
        # Check branch
        if lot.company_id.id != self.company_id.id:
            self._add_process_log(
                f"NoRangka {lot.name}: Branch mismatch", 'ERROR')
            return False

        # Khusus customer cash (bukan Finco)
        if lot.finco_id:
            self._add_process_log(
                f"NoRangka {lot.name}: Bukan customer cash (Finco)", 'ERROR')
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

        # Check sudah proses Tagihan Birojasa
        if not lot.registration_billing_id:
            self._add_process_log(
                f"NoRangka {lot.name}: Belum diproses di Tagihan Birojasa", 'ERROR')
            return False

        # Check sudah terima BPKB
        if not lot.vehicle_ownership_receipt_date:
            self._add_process_log(
                f"NoRangka {lot.name}: Belum diproses di Penerimaan BPKB", 'ERROR')
            return False

        # Check existing handover
        existing = self.env['tw.vehicle.ownership.handover.line'].sudo().search([
            ('lot_id', '=', lot.id),
            ('vehicle_ownership_handover_id.state', 'not in', ['cancel', 'done']),
            ('state', '!=', 'cancel')
        ], limit=1)
        if existing:
            self._add_process_log(
                f"NoRangka {lot.name}: Sudah ada di {existing.vehicle_ownership_handover_id.name}", 'ERROR')
            return False

        # Check sudah selesai
        if lot.vehicle_ownership_handover_date:
            self._add_process_log(
                f"NoRangka {lot.name}: Sudah selesai", 'ERROR')
            return False

        return True

    def _create_grouped_records(self, model, grouped_vals, process_name):
        """Create records dari grouped values dict."""
        created = self.env['tw.vehicle.ownership.handover']

        if not grouped_vals:
            raise UserError(
                f'Processing {process_name}: Tidak ada data valid!')

        for cust_id, g_vals in grouped_vals.items():
            record = model.suspend_security().create(g_vals)
            record.invalidate_recordset()
            record.read(['name', 'partner_id'])
            created += record
            cust_name = record.partner_id.name if record.partner_id else 'Tanpa Customer'
            record_name = record.name or f'ID:{record.id}'
            self._add_process_log(
                f'Created {process_name}: {record_name} (Customer: {cust_name})', 'SUCCESS')

        return created
