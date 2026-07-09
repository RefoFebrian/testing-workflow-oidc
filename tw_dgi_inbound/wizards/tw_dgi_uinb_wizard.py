# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields

# 4: imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)


class TwDgiUinbWizard(models.TransientModel):
    """
    Wizard untuk sync Unit Inbound (UINB) dari DGI API.
    Menggunakan mixin dari tw_dgi.

    Response structure (actual):
    {
        "data": [{
            "noShippingList": "15537-SLU-2600085",
            "tanggalTerima": "18/04/2026",
            "dealerId": "15537",
            "noInvoice": "3064059489",
            "statusShippingList": "1",
            "unit": [{
                "kodeTipeUnit": "MF1D",
                "kodeWarna": "BK",
                "kuantitasTerkirim": 1,
                "kuantitasDiterima": 1,
                "noMesin": "KFC1E1304657",
                "noRangka": "KFC11XTK304505",
                "statusRFS": "1",
                ...
            }]
        }]
    }
    """
    _name = "tw.dgi.uinb.wizard"
    _description = "DGI Unit Inbound Sync Wizard"
    _inherit = ["tw.dgi.wizard.mixin"]

    # 8: fields — additional filter params
    po_id = fields.Char(
        string='No PO/Invoice MD',
        help='Filter berdasarkan No Invoice / PO dari Main Dealer',
    )
    no_shipping_list = fields.Char(
        string='No Shipping List',
        help='Filter berdasarkan No Shipping List Main Dealer',
    )

    # 11: onchange
    def _prepare_api_request_body(self):
        """Override to add poId and noShippingList to request body."""
        body = super()._prepare_api_request_body()

        body['poId'] = self.po_id.strip() if self.po_id else ""
        body['noShippingList'] = self.no_shipping_list.strip() if self.no_shipping_list else ""

        return body

    # 13: action methods
    def action_get_dgi_data(self):
        """Main action: GET Unit Inbound data dari DGI."""
        return self.action_sync_dgi_data(endpoint_code='dgi_uinb')

    def _prepare_parse_response(self, endpoint, response_item):
        """
        Validate UINB data before parsing.
        - Check duplicate by kombinasi md_reference_po (noInvoice) + md_reference_sl (noShippingList)
        - 1 noInvoice bisa memiliki lebih dari 1 noShippingList → buat PO terpisah per SL
        """
        no_invoice = response_item.get('noInvoice', '')
        no_sl = response_item.get('noShippingList', '')

        # Duplicate check: kombinasi noInvoice + noShippingList
        # Jika salah satu tidak ada, fallback ke field yang tersedia
        if no_invoice or no_sl:
            domain = [('state', '!=', 'cancel')]
            if no_invoice and no_sl:
                # Cek exact match keduanya → duplikat sejati
                domain += [
                    ('md_reference_po', '=', no_invoice),
                    ('md_reference_sl', '=', no_sl),
                ]
            elif no_invoice:
                domain += [('md_reference_po', '=', no_invoice)]
            else:
                domain += [('md_reference_sl', '=', no_sl)]

            existing = self.env['purchase.order'].sudo().search(domain, limit=1)
            if existing:
                ref_info = f"noInvoice={no_invoice}, noSL={no_sl}" if (no_invoice and no_sl) else (no_invoice or no_sl)
                return f"Skipped: {ref_info} already exists as {existing.name}"

        return True


    def _get_item_identifier(self, endpoint, item):
        """Override to extract UINB-specific identifiers from DGI JSON."""
        if item.get('noInvoice'):
            return f"Invoice {item.get('noInvoice')}"
        if item.get('noShippingList'):
            return f"Shipping List {item.get('noShippingList')}"
        if item.get('poId'):
            return f"PO {item.get('poId')}"
        return super()._get_item_identifier(endpoint, item)

    def _prepare_line_vals(self, line_field, vals, source_item, index, endpoint):
        """
        Hook untuk custom processing unit lines.
        Keep parsed payload ready for PO aggregation and serial prefill.
        """
        vals = super()._prepare_line_vals(line_field, vals, source_item, index, endpoint)

        if line_field == 'order_line':
            # Default qty = 1 per unit entry (aggregation done in _create_record_from_response)
            if not vals.get('product_qty'):
                vals['product_qty'] = 1
        elif line_field == 'serial_line':
            vals['is_rfs'] = str(vals.get('is_rfs', '1')) == '1'

        return vals

    def _create_record_from_response(self, endpoint, values):
        """
        Override untuk create Purchase Order (Unit) dari UINB response.

        Flow (sesuai DGI PO Flow Process diagram):
        1. Create PO (Draft)
        2. Cek Branch Config: dgi_auto_confirm_po
           - False → simpan sebagai Draft (selesai)
           - True  → Confirm PO → Odoo auto-generate Picking Transfer
                   → Generate Draft Vendor Bill (Invoice)
        """
        company_id = values.get('company_id')
        company = self.env['res.company'].sudo().browse(company_id) if company_id else self.company_id

        raw_order_lines = values.pop('order_line', [])
        raw_serial_lines = values.pop('serial_line', [])
        aggregated_lines = self._aggregate_order_lines(raw_order_lines)
        serial_payload_by_product = self._group_serial_lines(raw_serial_lines)
        if not aggregated_lines:
            raise UserError("Order line kosong setelah processing unit data!")
        values.update(
            self._prepare_purchase_order_values(company, aggregated_lines)
        )

        values = self._prepare_record_value(endpoint, values)
        if not values.get('partner_id'):
            if not company.default_supplier_id.id:
                raise UserError(f"Default supplier belum di-set untuk branch {company.name}")
            values.update({'partner_id': company.default_supplier_id.id})

        # Step 1: Create PO (always starts as Draft)
        po = self.env['purchase.order'].sudo().with_company(company).create(values)

        # Step 2: Check Branch Setting — dgi_auto_confirm_po
        branch_setting = company.branch_setting_id
        auto_confirm = branch_setting.dgi_auto_confirm_po if branch_setting else False

        if not auto_confirm:
            extra_logs = [
                f"Shipping List: {po.md_reference_sl or '-'}",
                f"PO: {po.name}",
                "Status: Draft",
                f"Branch Setting auto_confirm={auto_confirm}"
            ]
            return po.with_context(dgi_success_log_lines=extra_logs)

        # Step 3: Auto Confirm PO → Odoo generates Picking Transfer automatically
        po.button_confirm()
        
        # Bypass Odoo double validation / approval matrix for automated API sync
        if po.state in ('to approve', 'waiting_for_approval', 'approved'):
            po.button_approve()
            
        self._prefill_incoming_picking_serials(po, serial_payload_by_product)

        # Step 4: Generate Draft Vendor Bill (Invoice)
        invoice, inv_msg = self._generate_draft_vendor_bill(po, company)
        
        extra_logs = [
            f"Shipping List: {po.md_reference_sl or '-'}",
            f"PO: {po.name}",
            "Status: Confirmed",
            f"Branch Setting auto_confirm={auto_confirm}",
            f"Picking: {len(po.picking_ids)} transfer",
            f"Vendor Bill: {inv_msg}"
        ]
        
        return po.with_context(dgi_success_log_lines=extra_logs)

    # 14: private methods
    def _aggregate_order_lines(self, raw_order_lines):
        """
        Aggregate parsed order lines by product_id.

        Output template already handles extraction from DGI response.
        This helper keeps PO lines focused on purchase.order.line values only.
        """
        aggregated = {}
        for command in raw_order_lines:
            if len(command) < 3:
                continue

            line_vals = command[2]
            product_id = line_vals.get('product_id')
            if not product_id:
                continue

            if product_id not in aggregated:
                aggregated[product_id] = dict(line_vals)
                aggregated[product_id]['product_qty'] = 0

            aggregated[product_id]['product_qty'] += line_vals.get('product_qty', 1)

        return [(0, 0, line_vals) for line_vals in aggregated.values()]

    def _prepare_purchase_order_values(self, company, aggregated_lines):
        """
        Build PO business values that are not part of DGI output template.
        """
        picking_type_obj = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id.company_id', '=', company.id),
        ], limit=1)
        if not picking_type_obj:
            raise UserError(f"Picking type incoming tidak ditemukan untuk branch {company.name}")

        po_type_obj = self.env['tw.purchase.order.type'].sudo().search([
            ('name', '=', 'Additional'),
            ('division', '=', 'Unit'),
        ], limit=1)

        po_values = {
            'picking_type_id': picking_type_obj.id,
            'order_line': aggregated_lines,
        }

        if po_type_obj:
            po_values['purchase_order_type_id'] = po_type_obj.id
            po_values.update(self._build_po_period_values(po_type_obj))

        return po_values

    def _generate_draft_vendor_bill(self, po, company):
        """
        Generate Draft Vendor Bill dari Purchase Order yang sudah di-Confirm.
        Menggunakan standard Odoo action_create_invoice untuk konsistensi.

        Returns:
            Tuple (account.move record or None, status message string)
        """
        if po.invoice_status == 'no':
            return None, "Menunggu Receipt (Policy Kuantitas Diterima)"

        try:
            po.action_create_invoice()
            invoices = po.invoice_ids.filtered(lambda inv: inv.state == 'draft')
            if invoices:
                return invoices[0], invoices[0].name
        except Exception as e:
            error_msg = str(e)
            if "invoiceable line" in error_msg.lower():
                return None, "Menunggu Receipt (Policy Kuantitas Diterima)"
            else:
                return None, f"Gagal Generate: {error_msg}"
        return None, "-"

    def _group_serial_lines(self, raw_serial_lines):
        """Group parsed serial_line payload by product_id for picking prefill."""
        serial_payload_by_product = {}
        for command in raw_serial_lines:
            if len(command) < 3:
                continue

            line_vals = command[2]
            product_id = line_vals.get('product_id')
            if not product_id:
                continue
                
            lot_name = line_vals.get('lot_name') or False
            if lot_name:
                lot_name = str(lot_name).replace(' ', '')
                
            chassis_number = line_vals.get('chassis_number') or False
            if chassis_number:
                chassis_number = str(chassis_number).replace(' ', '')

            serial_payload_by_product.setdefault(product_id, []).append({
                'lot_name': lot_name,
                'chassis_number': chassis_number,
                'is_rfs': line_vals.get('is_rfs', True),
            })

        return serial_payload_by_product

    def _prefill_incoming_picking_serials(self, po, serial_payload_by_product):
        """
        Prefill serial/chassis on incoming picking move lines without validating receipt.
        """
        if not serial_payload_by_product:
            return

        incoming_picking_obj = po.picking_ids.filtered(
            lambda picking: picking.state not in ("cancel", "done") and picking.picking_type_id.code == "incoming"
        )[:1]
        if not incoming_picking_obj:
            self._add_process_log(
                f"Picking incoming tidak ditemukan untuk PO {po.name}; serial tidak diprefill.",
                "WARNING",
            )
            return

        for move_obj in incoming_picking_obj.move_ids_without_package.filtered(lambda move: move.product_id.id in serial_payload_by_product):
            serial_payloads = serial_payload_by_product.get(move_obj.product_id.id, [])
            expected_qty = int(round(move_obj.product_uom_qty or 0))
            if expected_qty and len(serial_payloads) != expected_qty:
                self._add_process_log(
                    (
                        f"Serial count mismatch untuk produk {move_obj.product_id.display_name} "
                        f"di picking {incoming_picking_obj.name}: expected {expected_qty}, got {len(serial_payloads)}."
                    ),
                    "WARNING",
                )
                continue

            existing_move_lines = move_obj.move_line_ids.filtered(lambda line: not line.lot_id)
            for index, payload in enumerate(serial_payloads):
                move_line_vals = self._prepare_serial_move_line_vals(move_obj, incoming_picking_obj, payload)
                if index < len(existing_move_lines):
                    existing_move_lines[index].write(move_line_vals)
                else:
                    self.env["stock.move.line"].sudo().create(move_line_vals)

    def _prepare_serial_move_line_vals(self, move_obj, picking_obj, payload):
        """Build stock move line values for serial/chassis prefill on UINB picking."""
        return {
            "move_id": move_obj.id,
            "picking_id": picking_obj.id,
            "company_id": picking_obj.company_id.id,
            "product_id": move_obj.product_id.id,
            "product_uom_id": move_obj.product_uom.id,
            "location_id": move_obj.location_id.id,
            "location_dest_id": move_obj.location_dest_id.id,
            "quantity": 1,
            "lot_name": payload.get("lot_name"),
            "chassis_number": payload.get("chassis_number"),
            "is_rfs": payload.get("is_rfs", True),
        }

    def _build_po_period_values(self, po_type_obj):
        """Build start/end date from PO type with safe end-date fallback."""
        start_date = po_type_obj.get_date(po_type_obj.start_date_id.value) if po_type_obj.start_date_id else False
        end_date = po_type_obj.get_date(po_type_obj.end_date_id.value) if po_type_obj.end_date_id else False

        if start_date and not end_date:
            end_date = start_date + relativedelta(days=30)

        return {
            "start_date": start_date,
            "end_date": end_date,
        }

