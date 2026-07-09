# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields
from odoo.exceptions import UserError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class DGIPartSalesWizard(models.TransientModel):
    """
    Wizard untuk mengambil data Part Sales dari DGI API.

    Implementasi berbasis DGI Engine (tw.dgi.wizard.mixin) — semua mapping
    field dilakukan via XML output_template dan tw.mapping.response record,
    sesuai standar modul tw_dgi_work_order dan tw_dgi_spk.

    Flow:
        1. User pilih branch + rentang tanggal + optional noSO
        2. Wizard call DGI API endpoint 'dgi_get_part_sales'
        3. Engine parse response: map company_id, partner_id, order_line
        4. _prepare_parse_response cek duplikasi berdasarkan noSO
        5. _prepare_record_value: enrich order_line dengan product uom & name
        6. _create_record_from_response: super() create + post-create actions
    """

    _name = "tw.dgi.part.sales.wizard"
    _inherit = "tw.dgi.wizard.mixin"
    _description = "DGI Part Sales Wizard"

    # -------------------------------------------------------------------------
    # FIELDS
    # -------------------------------------------------------------------------
    no_part_sales = fields.Char(string="Nomor Part Sales")

    # -------------------------------------------------------------------------
    # ACTIONS
    # -------------------------------------------------------------------------
    def action_get_dgi_data(self):
        """Main action: GET data Part Sales dari DGI dan proses."""
        return self.action_sync_dgi_data(endpoint_code='dgi_get_part_sales')

    # -------------------------------------------------------------------------
    # PRIVATE
    # -------------------------------------------------------------------------
    def _prepare_api_request_body(self):
        """Tambahkan filter noSO jika diisi."""
        prepare = super()._prepare_api_request_body()
        if self.no_part_sales:
            prepare['noSO'] = self.no_part_sales
        return prepare

    def _prepare_parse_response(self, endpoint, response_item):
        """
        Validasi sebelum parsing: cek apakah Part Sales sudah ada di sistem.

        Skip (WARNING) jika noSO sudah tercatat di tw.part.sales.
        """
        no_so = response_item.get('noSO')
        if no_so:
            existing = self.env['tw.part.sales'].sudo().search(
                [('md_reference_ps', '=', no_so)], limit=1
            )
            if existing:
                return {
                    'proceed': False,
                    'message': f"Part Sales {no_so} sudah ada: {existing.name}",
                    'log_type': 'WARNING'
                }
        return super()._prepare_parse_response(endpoint, response_item)

    def _get_item_identifier(self, endpoint, item):
        """Identifier untuk logging per item."""
        return f"Part Sales {item.get('noSO', 'Unknown')}"

    def _prepare_record_value(self, endpoint, values):
        """
        Enrich order_line sebelum create:
        - Isi product_uom dari product.uom_id
        - Isi name dari product.display_name

        Field ini tidak tersedia di DGI JSON sehingga harus diisi dari Odoo.
        """
        values = super()._prepare_record_value(endpoint, values)

        order_lines = values.get('order_line', [])
        enriched_lines = []
        for cmd in order_lines:
            # cmd format: (0, 0, line_vals)
            if cmd[0] == 0 and isinstance(cmd[2], dict):
                line_vals = cmd[2]
                product_id = line_vals.get('product_id')
                if product_id:
                    product = self.env['product.product'].sudo().browse(product_id)
                    line_vals.setdefault('name', product.display_name)
                    line_vals.setdefault('product_uom', product.uom_id.id)
                enriched_lines.append((0, 0, line_vals))
            else:
                enriched_lines.append(cmd)

        values['order_line'] = enriched_lines
        return values

    def _create_record_from_response(self, endpoint, values):
        """
        Override: setelah record dibuat, jalankan post-create actions.

        - _set_location(): assign lokasi gudang ke setiap order line
        - _check_stock_availabilty(): validasi ketersediaan stok (wajib lulus)
        """
        part_sales = super()._create_record_from_response(endpoint, values)
        if part_sales and part_sales.id:
            part_sales.order_line._set_location()
            # Gagalkan dengan warning jika stok tidak cukup
            part_sales._check_stock_availabilty()

        extra_logs = [
            f"MD Reference PS: {part_sales.md_reference_ps or '-'}",
            f"Status DGI: {part_sales.state_dgi or '-'}",
            f"Lines: {len(part_sales.order_line)} items",
        ]
        return part_sales.with_context(dgi_success_log_lines=extra_logs)