# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TwDirectGiftExcelReport(models.Model):
    _inherit = "tw.stock.opname.direct.gift"

    def action_download_excel_direct_gift(self):
        self.ensure_one()
        return self._get_report()

    def _get_report(self):
        data_sheet = self._get_data_sheet()
        if not data_sheet:
            raise UserError(_("Tidak ada data untuk dicetak."))

        primary_data = next(iter(data_sheet.values()))

        summary_header = self._get_summary_header_data()

        return self.env['web.report'].sudo().generate_report("Stock Opname Direct Gift", data=primary_data, data_sheet=data_sheet, data_summary_header=summary_header)

    def _get_data_sheet(self):
        self.ensure_one()

        data_sheet = {}
        sheet1_data = self._get_direct_gift_line_data()
        sheet2_data = self._get_direct_gift_other_data()

        if sheet1_data:
            data_sheet["Stock Opname Direct Gift"] = sheet1_data
        if sheet2_data:
            data_sheet["Stock Opname Direct Gift Other"] = sheet2_data

        return data_sheet

    def _get_direct_gift_line_data(self):
        query = f"""
            SELECT
                rc.code AS branch_code,
                rc.name AS branch_name,
                pp.default_code,
                pt.name AS product_name,
                line.name AS description,
                line.unit_price,
                line.qty,
                (COALESCE(line.unit_price, 0) * COALESCE(line.qty, 0)) AS amount,
                line.qty_physical_good,
                line.qty_physical_broken,
                (COALESCE(line.qty_physical_good, 0) + COALESCE(line.qty_physical_broken, 0)) AS qty_physical_total,
                (COALESCE(line.unit_price, 0) * (COALESCE(line.qty_physical_good, 0) + COALESCE(line.qty_physical_broken, 0))) AS amount_total,
                ((COALESCE(line.qty_physical_good, 0) + COALESCE(line.qty_physical_broken, 0)) - COALESCE(line.qty, 0)) AS diff_qty,
                (COALESCE(line.unit_price, 0) * ((COALESCE(line.qty_physical_good, 0) + COALESCE(line.qty_physical_broken, 0)) - COALESCE(line.qty, 0))) AS diff_amount,
                line.balance_log_book,
                line.aging
            FROM tw_stock_opname_direct_gift_line line
            JOIN tw_stock_opname_direct_gift header ON line.opname_id = header.id
            JOIN res_company rc ON header.company_id = rc.id
            LEFT JOIN product_product pp ON line.product_id = pp.id
            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
            WHERE line.opname_id = {self.id}
        """
        self.env.cr.execute(query)
        results = self.env.cr.dictfetchall()

        sheet_data = []
        for res in results:
            product_name = res.get('product_name') or ''

            if isinstance(product_name, dict):
                product_name = next(iter(product_name.values()), '')
            elif isinstance(product_name, str) and product_name.startswith('{'):
                try:
                    import json
                    parsed = json.loads(product_name)
                    product_name = next(iter(parsed.values()), '')
                except Exception:
                    pass

            if res.get('default_code'):
                product_name = f"[{res['default_code']}] {product_name}"

            sheet_data.append({
                "Branch Code": res.get('branch_code'),
                "Branch Name": res.get('branch_name'),
                "Product": product_name,
                "Description": res.get('description') or "",
                "Harga Satuan": res.get('unit_price') or 0.00,
                "Qty Sistem": res.get('qty') or 0,
                "Amount Total Sistem": res.get('amount') or 0.00,
                "Qty Fisik Baik": res.get('qty_physical_good') or 0,
                "Qty Fisik Rusak": res.get('qty_physical_broken') or 0,
                "Total Qty Fisik": res.get('qty_physical_total') or 0,
                "Amount Total Fisik": res.get('amount_total') or 0.00,
                "Selisih Qty": res.get('diff_qty') or 0,
                "Selisih Amount": res.get('diff_amount') or 0.00,
                "Saldo Logbook": res.get('balance_log_book') or 0,
                "Aging": res.get('aging') or 0,
            })

        return sheet_data

    def _get_direct_gift_other_data(self):
        query = f"""
            SELECT
                rc.code AS branch_code,
                rc.name AS branch_name,
                other.product_name,
                other.qty_physical_good,
                other.qty_physical_broken,
                (COALESCE(other.qty_physical_good, 0) + COALESCE(other.qty_physical_broken, 0)) AS qty_physical_total,
                other.balance_log_book
            FROM tw_stock_opname_direct_gift_other other
            JOIN tw_stock_opname_direct_gift header ON other.opname_id = header.id
            JOIN res_company rc ON header.company_id = rc.id
            WHERE other.opname_id = {self.id}
        """
        self.env.cr.execute(query)
        results = self.env.cr.dictfetchall()

        sheet_data = []
        for res in results:
            sheet_data.append({
                "Branch Code": res.get('branch_code'),
                "Branch Name": res.get('branch_name'),
                "Nama Barang": res.get('product_name') or "",
                "Qty Fisik Baik": res.get('qty_physical_good') or 0,
                "Qty Fisik Rusak": res.get('qty_physical_broken') or 0,
                "Total Qty Fisik": res.get('qty_physical_total') or 0,
                "Saldo Logbook": res.get('balance_log_book') or 0,
            })

        return sheet_data

    def _get_summary_header_data(self):
        return {
            "A1": "No. Ref",
            "B1": self.name or "",
        }
