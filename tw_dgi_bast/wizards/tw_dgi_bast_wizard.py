# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
from datetime import datetime

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields

# 4: imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)


class TwDgiBastWizard(models.TransientModel):
    """
    Wizard untuk sync BAST (Berita Acara Serah Terima) dari DGI API.
    Menggunakan mixin dari tw_dgi.

    BAST digunakan untuk proses batch transfer out (packing/surat jalan)
    dari transaksi Dealer Sale Order divisi Unit.

    Response structure (actual):
    {
        "data": [{
            "deliveryDocumentId": "07327-SLO-2602134",
            "tanggalPengiriman": "24/04/2026",
            "idDriver": "246084",
            "statusDeliveryDocument": "4",
            "dealerId": "07327",
            "createdTime": "24/04/2026 13:23:09",
            "modifiedTime": "24/04/2026 13:42:08",
            "detail": [{
                "noSO": "07327-SPK-26002987",
                "idSPK": "07327-SPK-26002987",
                "noMesin": "JMK1E1131253",
                "noRangka": "JMK111TK131193",
                "idCustomer": "8042265516",
                "waktuPengiriman": "14:00",
                "checklistKelengkapan": "Battery,Mirror,...",
                "lokasiPengiriman": "DUSUN IV",
                "namaPenerima": "ADRIAN",
                "noKontakPenerima": "082174270751",
                ...
            }]
        }]
    }
    """
    _name = "tw.dgi.bast.wizard"
    _description = "DGI BAST Sync Wizard"
    _inherit = ["tw.dgi.wizard.mixin"]

    # -------------------------------------------------------------------------
    # FIELDS
    # -------------------------------------------------------------------------
    delivery_document_id = fields.Char(
        string="Delivery Document ID",
        help="Filter berdasarkan ID Surat Jalan DGI (optional)",
    )

    # -------------------------------------------------------------------------
    # ACTIONS
    # -------------------------------------------------------------------------
    def action_get_dgi_data(self):
        """Main action: GET BAST data dari DGI."""
        return self.action_sync_dgi_data(endpoint_code='dgi_bast')

    # -------------------------------------------------------------------------
    # HOOKS - Override mixin methods
    # -------------------------------------------------------------------------
    def _prepare_api_request_body(self):
        """Override to add deliveryDocumentId to request body."""
        body = super()._prepare_api_request_body()

        if self.delivery_document_id:
            body['deliveryDocumentId'] = self.delivery_document_id.strip()

        return body

    def _prepare_parse_response(self, endpoint, response_item):
        """
        Validate BAST data before parsing.
        - Check duplicate by deliveryDocumentId
        - Validate detail items array exists and not empty
        """
        delivery_doc_id = response_item.get('deliveryDocumentId', '')
        detail_items = response_item.get('detail', [])

        # Validate detail data exists
        if not detail_items:
            return f"Skipped: deliveryDocumentId {delivery_doc_id} has no detail data"

        # Check duplicate batch by delivery_document_id
        if delivery_doc_id:
            existing_obj = self.env['stock.picking.batch'].sudo().search([
                ('dgi_delivery_document_id', '=', delivery_doc_id),
                ('state', '!=', 'cancel'),
            ], limit=1)
            if existing_obj:
                return f"Skipped: deliveryDocumentId {delivery_doc_id} already exists as {existing_obj.name}"

        return True

    def _get_item_identifier(self, endpoint, item):
        """Override to extract BAST-specific identifiers from DGI JSON."""
        if item.get('deliveryDocumentId'):
            return f"Delivery {item.get('deliveryDocumentId')}"
        return super()._get_item_identifier(endpoint, item)

    def _create_record_from_response(self, endpoint, values):
        """
        Override untuk create Batch Transfer Out dari BAST response.

        Custom logic:
        - Loop detail items dari response
        - Find DSO directly by source_document (idSPK)
        - Validate DSO: state == 'sale', division == 'Unit', picking not done
        - Find stock.lot by noMesin
        - Assign lot to DSO picking line
        - Create batch transfer and attach pickings
        """
        company_id = values.get('company_id')
        company_obj = self.env['res.company'].sudo().browse(company_id) if company_id else self.company_id

        delivery_doc_id = values.get('_delivery_document_id') or self.env.context.get('_delivery_document_id', '')
        tanggal_pengiriman = values.get('_tanggal_pengiriman') or self.env.context.get('_tanggal_pengiriman', '')
        detail_items = values.pop('_detail_items', None)
        if detail_items is None:
            detail_items = self.env.context.get('_detail_items', [])

        # Parse scheduled date
        scheduled_date = False
        if tanggal_pengiriman:
            try:
                scheduled_date = datetime.strptime(tanggal_pengiriman, '%d/%m/%Y')
            except ValueError:
                _logger.warning(f"BAST: Invalid tanggalPengiriman format: {tanggal_pengiriman}")

        # Collect valid pickings to attach to batch
        pickings_to_batch = self.env['stock.picking']
        skipped_details = []

        if not isinstance(detail_items, list):
            detail_items = [detail_items] if detail_items else []

        for detail in detail_items:
            id_spk = detail.get('idSPK', '')
            no_mesin = detail.get('noMesin', '')
            no_rangka = detail.get('noRangka', '')

            # --- 1. Find DSO directly by source_document (idSPK) ---
            dso_obj = self.env['tw.dealer.sale.order'].sudo().search([
                ('source_document', '=', id_spk),
                ('company_id', '=', company_obj.id),
            ], limit=1)
        
            if not dso_obj:
                skipped_details.append(f"idSPK {id_spk}: DSO not found")
                continue

            # --- 2. Validate DSO ---
            if dso_obj.state != 'sale':
                skipped_details.append(
                    f"idSPK {id_spk}: DSO {dso_obj.name} state is '{dso_obj.state}', expected 'sale'"
                )
                continue

            if dso_obj.division != 'Unit':
                skipped_details.append(
                    f"idSPK {id_spk}: DSO {dso_obj.name} division is '{dso_obj.division}', expected 'Unit'"
                )
                continue

            # Get outgoing picking not yet validated
            valid_pickings = dso_obj.picking_ids.filtered(
                lambda p: p.picking_type_id.code == 'outgoing'
                and p.state not in ('done', 'cancel')
            )
            if not valid_pickings:
                skipped_details.append(
                    f"idSPK {id_spk}: DSO {dso_obj.name} has no pending outgoing picking"
                )
                continue

            # --- 3. Validate Serial Number (noMesin) against DSO order_line.lot_id ---
            lot_obj = None
            if no_mesin:
                # Ambil lot yang sudah ter-assign di DSO line (item_type='main')
                dso_main_lines = dso_obj.order_line.filtered(
                    lambda l: l.item_type == 'main' and l.lot_id
                )
                dso_lot_names = dso_main_lines.mapped('lot_id.name')

                # Cek apakah noMesin dari DGI ada di DSO line
                matched_lot = dso_main_lines.filtered(
                    lambda l: l.lot_id.name == no_mesin
                ).mapped('lot_id')

                if not matched_lot:
                    # noMesin dari DGI tidak match dengan DSO line
                    skipped_details.append(
                        f"idSPK {id_spk}: Serial mismatch - "
                        f"DGI noMesin '{no_mesin}' tidak ditemukan di DSO {dso_obj.name}. "
                        f"DSO lots: {', '.join(dso_lot_names) or '-'}"
                    )
                    continue

                lot_obj = matched_lot[0]

                # Validate chassis number (noRangka) jika tersedia
                if no_rangka and lot_obj.chassis_number and lot_obj.chassis_number != no_rangka:
                    skipped_details.append(
                        f"idSPK {id_spk}: Chassis mismatch - "
                        f"DSO lot chassis: '{lot_obj.chassis_number}', DGI noRangka: '{no_rangka}'"
                    )
                    continue

                # --- 4. Assign lot to picking move line ---
                self._assign_lot_to_picking(valid_pickings[0], lot_obj)


            # Collect the picking for batch
            pickings_to_batch |= valid_pickings[0]


        # Log skipped details
        for msg in skipped_details:
            self._add_process_log(msg, 'WARNING')

        if not pickings_to_batch:
            # Return empty record if no valid pickings found
            self._add_process_log(
                f"deliveryDocumentId {delivery_doc_id}: No valid pickings to create batch",
                'WARNING',
            )
            return self.env['stock.picking.batch']

        # --- 5. Generate Batch Lines ---
        batch_lines = []
        for picking in pickings_to_batch:
            for move in picking.move_ids:
                if not move.move_line_ids:
                    move._action_assign()
                
                quant_obj = False
                if hasattr(move, '_get_location_from_stock_avb'):
                    quant_obj = move._get_location_from_stock_avb(picking, move.product_id.id)
                    
                for move_line in move.move_line_ids:
                    line_vals = {
                        'move_id': move_line.move_id.id,
                        'product_id': move_line.product_id.id,
                        'quantity': move_line.quantity,
                        'product_uom_qty': move_line.move_id.product_uom_qty,
                        'location_id': move_line.location_id.id,
                        'location_dest_id': move_line.location_dest_id.id,
                    }
                    if move_line.lot_id:
                        line_vals['lot_id'] = move_line.lot_id.id
                    if move_line.lot_name:
                        line_vals['lot_name'] = move_line.lot_name

                    if quant_obj:
                        if picking.picking_type_id.sequence_code in ('PICK', 'OUT'):
                            line_vals['location_id'] = quant_obj.location_id.id
                        if picking.picking_type_id.code == 'incoming':
                            line_vals['location_dest_id'] = quant_obj.location_id.id

                    batch_lines.append((0, 0, line_vals))

        # --- 6. Create Batch Transfer ---
        batch_vals = {
            'company_id': company_obj.id,
            'dgi_delivery_document_id': delivery_doc_id,
            'picking_type_id': pickings_to_batch[0].picking_type_id.id,
            'picking_ids': [(6, 0, pickings_to_batch.ids)],
            'source_picking_ids': [(6, 0, pickings_to_batch.ids)],
            'batch_line_ids': batch_lines,
            'is_dgi': True,
            'dgi_get_date': fields.Datetime.now(),
            'dgi_get_uid': self.env.user.id,
            'division': 'Unit',
            'type': 'Retail',
        }
        if scheduled_date:
            batch_vals['scheduled_date'] = scheduled_date

        batch_obj = self.env['stock.picking.batch'].sudo().with_company(company_obj).create(batch_vals)
        
        return batch_obj

    # -------------------------------------------------------------------------
    # PRIVATE
    # -------------------------------------------------------------------------
    def _assign_lot_to_picking(self, picking_obj, lot_obj):
        """Assign lot to the first matching move line in the picking.

        Find the stock.move.line that matches the product of the lot
        and assign the lot_id to it.
        """
        for move in picking_obj.move_ids:
            if move.product_id == lot_obj.product_id:
                # Check if any move line already has this lot
                existing_ml = move.move_line_ids.filtered(
                    lambda ml: ml.lot_id == lot_obj
                )
                if existing_ml:
                    return  # Already assigned

                # Find unassigned move line
                unassigned_ml = move.move_line_ids.filtered(
                    lambda ml: not ml.lot_id
                )
                if unassigned_ml:
                    unassigned_ml[0].lot_id = lot_obj.id
                    return

                # No unassigned line found, create one
                move.move_line_ids.create({
                    'move_id': move.id,
                    'picking_id': picking_obj.id,
                    'product_id': lot_obj.product_id.id,
                    'lot_id': lot_obj.id,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    'quantity': 1,
                })
                return

    def _get_success_log_lines(self, endpoint, item, record):
        """Return grouped success detail lines for BAST transaction."""
        details = item.get('detail', [])
        lines = [
            f"- Batch: {record.name}",
            f"- Pickings: {len(record.picking_ids)}",
            f"- Details DGI: {len(details)}",
        ]
        return lines
