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


class TwDgiPinbWizard(models.TransientModel):
    """
    Wizard untuk sync Part Inbound (PINB) dari DGI API.
    Menggunakan mixin dari tw_dgi.

    Response structure (actual):
    {
        "data": [{
            "noPenerimaan": "RCV-100814-26-04-00007",
            "tglPenerimaan": "21/04/2026",
            "noShippingList": "MND/26/04/123670",
            "dealerId": "13074",
            "po": [{
                "noPO": "P-SLUKAG-20260417-154120",
                "jenisOrder": "2",
                "idWarehouse": "WH/13074/1",
                "partsNumber": "34908GA7701",
                "kuantitas": 12,
                "uom": "PCS",
                ...
            }]
        }]
    }
    """
    _name = "tw.dgi.pinb.wizard"
    _description = "DGI Part Inbound Sync Wizard"
    _inherit = ["tw.dgi.wizard.mixin"]

    # 8: fields — additional filter params
    po_id = fields.Char(
        string='No PO/Invoice MD',
        help='Filter berdasarkan No PO dari Main Dealer',
    )

    # 11: onchange
    def _prepare_api_request_body(self):
        """Override to add noPO to request body."""
        body = super()._prepare_api_request_body()

        if self.po_id:
            body['noPO'] = self.po_id.strip()

        return body

    # 13: action methods
    def action_get_dgi_data(self):
        """Main action: GET Part Inbound data dari DGI."""
        return self.action_sync_dgi_data(endpoint_code='dgi_pinb')

    def _prepare_parse_response(self, endpoint, response_item):
        """
        Validate PINB data before parsing.
        - Check duplicate by noPenerimaan
        - Validate po items array exists and not empty
        """
        no_penerimaan = response_item.get('noPenerimaan', '')
        po_items = response_item.get('po', [])

        # Validate part data exists
        if not po_items:
            return f"Skipped: noPenerimaan {no_penerimaan} has no PO data"

        # Check duplicate PO by md_reference_sl (noPenerimaan)
        if no_penerimaan:
            existing = self.env['purchase.order'].sudo().search([
                ('md_reference_sl', '=', no_penerimaan),
                ('state', '!=', 'cancel'),
            ], limit=1)
            if existing:
                return f"Skipped: noPenerimaan {no_penerimaan} already exists as {existing.name}"

        return True

    def _get_item_identifier(self, endpoint, item):
        """Override to extract PINB-specific identifiers from DGI JSON."""
        if item.get('noInvoice'):
            return f"Invoice {item.get('noInvoice')}"
        if item.get('noShippingList'):
            return f"Shipping List {item.get('noShippingList')}"
        if item.get('poId'):
            return f"PO {item.get('poId')}"
        return super()._get_item_identifier(endpoint, item)

    def _prepare_line_vals(self, line_field, vals, source_item, index, endpoint):
        """
        Hook untuk custom processing part lines.
        Map kuantitas to product_qty.
        """
        vals = super()._prepare_line_vals(line_field, vals, source_item, index, endpoint)

        if line_field == 'order_line':
            # Rename kuantitas → product_qty
            if 'kuantitas' in vals:
                vals['product_qty'] = vals.pop('kuantitas')

            if not vals.get('product_qty'):
                vals['product_qty'] = 1

        return vals

    def _create_record_from_response(self, endpoint, values):
        """
        Override untuk create Purchase Order (Sparepart) dari PINB response.

        Custom logic:
        - Group PO lines by noPO → 1 PO per noPO group
        - Lookup product by partsNumber (name/default_code)
        - Determine picking type dan PO type
        - Keep business validation yang tidak cocok dipindah ke template

        Note: Jika response memiliki multiple noPO dalam satu noPenerimaan,
        maka semua masuk ke satu PO (sesuai behaviour legacy).
        """
        company_id = values.get('company_id')
        company = self.env['res.company'].sudo().browse(company_id) if company_id else self.company_id

        if not values.get('company_id'):
            values.update({
                'company_id': self.company_id.id
            })
            
        # Picking Type
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id.company_id', '=', company.id),
            '|', ('division', '=', 'Sparepart'), ('division', '=', False),
        ], limit=1)
        if not picking_type:
            raise UserError(f"Picking type incoming tidak ditemukan untuk branch {company.name}")

        # Determine PO Type from jenisOrder
        jenis_order = values.pop('_jenis_order', '') or ''
        po_type_name = self._map_jenis_order_to_po_type(jenis_order)
        po_type = self.env['tw.purchase.order.type'].sudo().search([
            ('name', '=', po_type_name),
            ('division', '=', 'Sparepart'),
        ], limit=1)

        raw_lines = values.pop('order_line', [])

        # Keep DGI metadata from core mixin and trust template-driven defaults.
        values.update({
            'picking_type_id': picking_type.id,
            'order_line': raw_lines,
        })
        values = self._prepare_record_value(endpoint, values)

        if not values.get('partner_id'):
            if not company.default_supplier_id.id:
                raise UserError(f"Default supplier belum di-set untuk branch {company.name}")
            values.update({'partner_id': company.default_supplier_id.id})
        if po_type:
            values['purchase_order_type_id'] = po_type.id
            values.update(self._build_po_period_values(po_type))

        # Create PO
        po = self.env['purchase.order'].sudo().with_company(company).create(values)
        return po.with_context(dgi_po_type_name=po_type_name)

    # 14: private methods
    def _get_success_log_lines(self, endpoint, item, record):
        """Return grouped success detail lines for PINB transaction."""
        lines = [
            f"- PO: {record.name}",
            f"- Status: Draft",
            f"- Division: {record.division or '-'}",
            f"- PO Type: {record.env.context.get('dgi_po_type_name') or '-'}",
            f"- MD PO: {record.md_reference_po or '-'}",
        ]
        return lines

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

    @staticmethod
    def _map_jenis_order_to_po_type(jenis_order):
        """Map DGI jenisOrder code to PO Type name.

        Maps:
        - 1/01 → Additional
        - 2/02 → Hotline
        - 3/03 → Urgent
        - 4/04 → Fix
        """
        mapping = {
            '1': 'Additional', '01': 'Additional',
            '2': 'Hotline', '02': 'Hotline',
            '3': 'Urgent', '03': 'Urgent',
            '4': 'Fix', '04': 'Fix',
        }
        return mapping.get(str(jenis_order).strip(), 'Additional')
