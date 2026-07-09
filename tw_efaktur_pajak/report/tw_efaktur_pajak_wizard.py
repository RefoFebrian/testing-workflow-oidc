# -*- coding: utf-8 -*-
"""E-Faktur Pajak Report Wizard.

This module generates E-Faktur Pajak Excel reports for DJP import.
Dynamically detects available transaction modules and includes their data.
All data transformation is done in SQL for optimal performance.
"""

# 1: imports of python lib
import base64
import logging
import math
from io import BytesIO
from datetime import datetime

# 3: imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def round_excel(n, decimals=0):
    """Excel-compatible rounding function."""
    multiplier = 10 ** decimals
    if n >= 0:
        result = math.floor(n * multiplier + 0.5) / multiplier
    else:
        result = math.ceil(n * multiplier - 0.5) / multiplier
    if result == int(result):
        return int(result)
    return result


def round_excel_str(n, decimals=0):
    """Excel-compatible rounding returning string."""
    result = round_excel(n, decimals)
    return str(result).rstrip("0").rstrip(".") if isinstance(result, float) else str(result)


class TwEFakturPajakWizard(models.TransientModel):
    """E-Faktur Pajak Report Wizard.
    
    Generates E-Faktur Pajak Excel report compatible with DJP import format.
    Dynamically includes data from installed transaction modules.
    """

    _name = "tw.efaktur.pajak.wizard"
    _description = "Generate eFaktur Pajak Report"

    # Fields
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    no_faktur = fields.Char('No. Faktur')
    ref_ids = fields.Many2many(
        'tw.faktur.pajak.out',
        'tw_efaktur_pajak_wizard_ref_rel',
        'wizard_id',
        'faktur_pajak_out_id',
        string='No Transaksi'
    )
    partner_ids = fields.Many2many(
        'res.partner',
        'tw_efaktur_pajak_wizard_partner_rel',
        'wizard_id',
        'partner_id',
        string="Partners"
    )
    company_ids = fields.Many2many(
        'res.company',
        'tw_efaktur_pajak_wizard_company_rel',
        'wizard_id',
        'company_id',
        string="Branch"
    )

    # Constraints
    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        """Validate that start_date is not greater than end_date."""
        for rec in self:
            if rec.start_date and rec.end_date and rec.start_date > rec.end_date:
                raise UserError(_("Start Date tidak boleh lebih besar dari End Date."))

    # Private Methods
    def _table_exists(self, table_name):
        """Check if a database table exists."""
        self.env.cr.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = %s
            )
        """, (table_name,))
        return self.env.cr.fetchone()[0]

    def _get_ppn12_cutoff(self):
        """Get PPN 12% cutoff date from config."""
        return self.env['ir.config_parameter'].sudo().get_param('ppn12', '2025-01-01')

    def _build_query_where(self):
        """Build WHERE clause for queries based on wizard filters."""
        conditions = ["fp.state IN ('print', 'close')"]
        params = {}

        if self.start_date and self.end_date:
            conditions.append("fp.date BETWEEN %(start_date)s AND %(end_date)s")
            params['start_date'] = self.start_date
            params['end_date'] = self.end_date

        if self.partner_ids:
            conditions.append("fp.partner_id = ANY(%(partner_ids)s)")
            params['partner_ids'] = self.partner_ids.ids

        if self.no_faktur:
            conditions.append("regexp_replace(fp.name, '[^0-9]+', '', 'g') = %(no_faktur)s")
            params['no_faktur'] = self.no_faktur

        if self.ref_ids:
            ref_values = [r.ref for r in self.ref_ids if r.ref]
            if ref_values:
                conditions.append("fp.ref = ANY(%(ref_values)s)")
                params['ref_values'] = ref_values

        if self.company_ids:
            conditions.append("fp.company_id = ANY(%(company_ids)s)")
            params['company_ids'] = self.company_ids.ids
        else:
            companies = self.env.user._get_company_ids()
            conditions.append("fp.company_id = ANY(%(company_ids)s)")
            params['company_ids'] = list(companies)

        return " AND ".join(conditions), params

    def _get_header_query(self, where_clause, cutoff_date):
        """Build header query for FK (Faktur) rows with all transformations in SQL."""
        return f"""
            SELECT 
                fp.id AS fp_id,
                fp.transaction_id,
                0 AS sort_id,
                'FK' AS "FK",
                -- Kode Jenis Transaksi: 04 if >= cutoff_date, else 01
                CASE WHEN fp.date >= '{cutoff_date}'::date THEN '04' ELSE '01' END AS "Kode Jenis Transaksi",
                '0' AS "FG Pengganti",
                regexp_replace(fp.name, '[^0-9]+', '', 'g') AS "Nomor Faktur",
                DATE_PART('month', fp.date)::INTEGER AS "Masa Pajak",
                DATE_PART('year', fp.date)::INTEGER AS "Tahun Pajak",
                TO_CHAR(fp.date, 'DD/MM/YYYY') AS "Tanggal Faktur",
                COALESCE(
                    regexp_replace(COALESCE(rp.no_npwp, '000000000000000'), '[^0-9]+', '', 'g'), 
                    '000000000000000'
                ) AS "NPWP",
                COALESCE(rp.identification_number, '000000000000000') || '#NIK#NAMA#' || rp.name AS "Nama",
                -- Alamat logic: pkp=true and alamat_pkp empty -> alamat_partner, pkp=true -> alamat_pkp, else alamat_lengkap
                CASE 
                    WHEN rp.is_pkp = TRUE AND COALESCE(rp.alamat_pkp, '') = '' THEN
                        CONCAT(rp.street, ' RT/RW ', rp.rt, '/', rp.rw, ' Kel. ', rsd.name, ' Kec. ', rd.name)
                    WHEN rp.is_pkp = TRUE THEN 
                        rp.alamat_pkp
                    ELSE 
                        CONCAT(
                            COALESCE(regexp_replace(rp.street, E'\\r|\\n|\\t', ' ', 'g'), ''),
                            COALESCE(' RT.' || rp.rt, ''),
                            COALESCE(' RW.' || rp.rw, ''),
                            COALESCE(' Kel.' || rsd.name, ''),
                            COALESCE(' Kec.' || rd.name, ''),
                            COALESCE(' ' || rc.name, ''),
                            COALESCE(' ' || rcs.name, '')
                        )
                END AS "Alamat Lengkap",
                ROUND(fp.untaxed_amount) AS "Jumlah DPP",
                ROUND(fp.tax_amount)::TEXT AS "Jumlah PPN",
                0 AS "Jumlah PPNBM",
                0 AS "ID Keterangan Tambahan",
                0 AS "FG Uang Muka",
                0 AS "Uang Muka DPP",
                0 AS "Uang Muka PPN",
                0 AS "Uang Muka PPNBM",
                COALESCE(fp.ref, '') AS "Referensi",
                '' AS "Kode Dokumen Pendukung"
            FROM tw_faktur_pajak_out fp
            LEFT JOIN res_partner rp ON fp.partner_id = rp.id
            LEFT JOIN res_city rc ON rp.city_id = rc.id
            LEFT JOIN res_country_state rcs ON rp.state_id = rcs.id
            LEFT JOIN res_district rd ON rp.district_id = rd.id
            LEFT JOIN res_sub_district rsd ON rp.sub_district_id = rsd.id
            WHERE {where_clause}
            AND fp.model_id NOT IN (
                SELECT id FROM ir_model 
                WHERE model = 'tw.faktur.pajak.other'
            )
        """

    def _get_sale_order_query(self, where_clause, cutoff_date):
        """Build query for Sale Order details (OF rows)."""
        if not self._table_exists('tw_sale_order'):
            return None
            
        return f"""
            SELECT 
                fp.id AS fp_id,
                fp.transaction_id,
                sol.id AS sort_id,
                'OF' AS "FK",
                COALESCE(pt.name->>'en_US', pp.default_code, '') AS "Kode Jenis Transaksi",
                regexp_replace(COALESCE(pt.description->>'en_US', pt.name->>'en_US', ''), E'\\r|\\n', ' ', 'g') AS "FG Pengganti",
                -- Harga Satuan (tanpa ppn)
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(ROUND(sol.price_unit / (1 + COALESCE(at.amount, 0) / 100)) * 0.91666666667)::TEXT
                    ELSE
                        ROUND(sol.price_unit / (1 + COALESCE(at.amount, 0) / 100))::TEXT
                END AS "Nomor Faktur",
                -- Jumlah Barang
                ROUND(sol.product_uom_qty)::INTEGER AS "Masa Pajak",
                -- Harga Total = Harga Satuan * Qty
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(ROUND(sol.price_unit / (1 + COALESCE(at.amount, 0) / 100) * sol.product_uom_qty) * 0.91666666667)
                    ELSE
                        ROUND(sol.price_unit / (1 + COALESCE(at.amount, 0) / 100) * sol.product_uom_qty)
                END::INTEGER AS "Tahun Pajak",
                -- Diskon
                ROUND(
                    (COALESCE(sod.discount_cash, 0) + COALESCE(sod.discount_lain, 0) + COALESCE(sod.discount_program, 0)) 
                    / NULLIF(tent.total_qty, 0) * sol.product_uom_qty
                )::TEXT AS "Tanggal Faktur",
                -- DPP 
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(
                            ROUND((sol.price_unit * (1 - COALESCE(sol.discount, 0) / 100) / (1 + COALESCE(at.amount, 0) / 100) * sol.product_uom_qty) 
                            - (COALESCE(sod.discount_cash, 0) / NULLIF(tent.total_qty, 0) * sol.product_uom_qty)
                            - (COALESCE(sod.discount_lain, 0) / NULLIF(tent.total_qty, 0) * sol.product_uom_qty)
                            - (COALESCE(sod.discount_program, 0) / NULLIF(tent.total_qty, 0) * sol.product_uom_qty)) * 0.91666666667
                        )::TEXT
                    ELSE
                        ROUND(
                            (sol.price_unit * (1 - COALESCE(sol.discount, 0) / 100) / (1 + COALESCE(at.amount, 0) / 100) * sol.product_uom_qty) 
                            - (COALESCE(sod.discount_cash, 0) / NULLIF(tent.total_qty, 0) * sol.product_uom_qty)
                            - (COALESCE(sod.discount_lain, 0) / NULLIF(tent.total_qty, 0) * sol.product_uom_qty)
                            - (COALESCE(sod.discount_program, 0) / NULLIF(tent.total_qty, 0) * sol.product_uom_qty)
                        )::TEXT
                END AS "NPWP",
                -- PPN
                ROUND(
                    ((sol.price_unit * (1 - COALESCE(sol.discount, 0) / 100) / (1 + COALESCE(at.amount, 0) / 100) * sol.product_uom_qty)
                    - (COALESCE(sod.discount_cash, 0) / NULLIF(tent.total_qty, 0) * sol.product_uom_qty)
                    - (COALESCE(sod.discount_lain, 0) / NULLIF(tent.total_qty, 0) * sol.product_uom_qty)
                    - (COALESCE(sod.discount_program, 0) / NULLIF(tent.total_qty, 0) * sol.product_uom_qty))
                    * COALESCE(at.amount, 0) / 100
                )::TEXT AS "Nama",
                '0' AS "Alamat Lengkap",
                0 AS "Jumlah DPP",
                '' AS "Jumlah PPN",
                0 AS "Jumlah PPNBM",
                0 AS "ID Keterangan Tambahan",
                0 AS "FG Uang Muka",
                NULL AS "Uang Muka DPP",
                NULL AS "Uang Muka PPN",
                NULL AS "Uang Muka PPNBM",
                '' AS "Referensi",
                '' AS "Kode Dokumen Pendukung"
            FROM tw_faktur_pajak_out fp
            INNER JOIN tw_sale_order so ON fp.id = so.faktur_pajak_out_id
                AND fp.model_id IN (SELECT id FROM ir_model WHERE model = 'tw.sale.order')
            INNER JOIN (
                SELECT tent_so.id, COALESCE(SUM(tent_sol.product_uom_qty), 0) AS total_qty 
                FROM tw_sale_order tent_so 
                INNER JOIN tw_sale_order_line tent_sol ON tent_so.id = tent_sol.order_id 
                GROUP BY tent_so.id
            ) tent ON so.id = tent.id
            INNER JOIN tw_sale_order_line sol ON so.id = sol.order_id
            LEFT JOIN account_tax_tw_sale_order_line_rel solt ON solt.tw_sale_order_line_id = sol.id
            LEFT JOIN account_tax at ON at.id = solt.account_tax_id
            LEFT JOIN (
                SELECT sale_order_id,
                    SUM(CASE WHEN name = 'Discount Cash' THEN amount ELSE 0 END) AS discount_cash,
                    SUM(CASE WHEN name = 'Discount Lain' THEN amount ELSE 0 END) AS discount_lain,
                    SUM(CASE WHEN name = 'Discount Program' THEN amount ELSE 0 END) AS discount_program
                FROM tw_sale_order_discount GROUP BY sale_order_id
            ) sod ON so.id = sod.sale_order_id
            LEFT JOIN product_product pp ON sol.product_id = pp.id
            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
            WHERE {where_clause}
        """

    def _get_work_order_query(self, where_clause, cutoff_date):
        """Build query for Work Order details (OF rows)."""
        if not self._table_exists('tw_work_order'):
            return None
            
        return f"""
            SELECT 
                fp.id AS fp_id,
                fp.transaction_id,
                wol.id AS sort_id,
                'OF' AS "FK",
                COALESCE(pt.name->>'en_US', pp.default_code, '') AS "Kode Jenis Transaksi",
                CASE 
                    WHEN wol.division = 'Sparepart' THEN pp.default_code 
                    ELSE regexp_replace(COALESCE(pt.description->>'en_US', pt.name->>'en_US', ''), E'\\r|\\n', ' ', 'g') 
                END AS "FG Pengganti",
                -- Harga Satuan
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(ROUND(wol.price_unit / (1 + COALESCE(at.amount, 0) / 100)) * 0.91666666667)::TEXT
                    ELSE
                        ROUND(wol.price_unit / (1 + COALESCE(at.amount, 0) / 100))::TEXT
                END AS "Nomor Faktur",
                -- Jumlah Barang
                CASE 
                    WHEN wol.division = 'Sparepart' THEN wol.qty_delivered 
                    ELSE wol.product_uom_qty 
                END::INTEGER AS "Masa Pajak",
                -- Harga Total
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(
                            ROUND(wol.price_unit / (1 + COALESCE(at.amount, 0) / 100) 
                            * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE wol.product_uom_qty END) * 0.91666666667
                        )
                    ELSE
                        ROUND(
                            wol.price_unit / (1 + COALESCE(at.amount, 0) / 100) 
                            * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE wol.product_uom_qty END
                        )
                END::INTEGER AS "Tahun Pajak",
                -- Diskon
                ROUND(
                    wol.price_unit / (1 + COALESCE(at.amount, 0) / 100) 
                    * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE wol.product_uom_qty END 
                    * COALESCE(wol.discount, 0) / 100
                )::TEXT AS "Tanggal Faktur",
                -- DPP
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(
                            ROUND(wol.price_unit / (1 + COALESCE(at.amount, 0) / 100) 
                            * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE wol.product_uom_qty END 
                            * (1 - COALESCE(wol.discount, 0) / 100)) * 0.91666666667
                        )::TEXT
                    ELSE
                        ROUND(
                            wol.price_unit / (1 + COALESCE(at.amount, 0) / 100) 
                            * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE wol.product_uom_qty END 
                            * (1 - COALESCE(wol.discount, 0) / 100)
                        )::TEXT
                END AS "NPWP",
                -- PPN
                ROUND(
                    wol.price_unit / (1 + COALESCE(at.amount, 0) / 100) 
                    * CASE WHEN wol.division = 'Sparepart' THEN wol.qty_delivered ELSE wol.product_uom_qty END 
                    * (1 - COALESCE(wol.discount, 0) / 100) 
                    * COALESCE(at.amount, 0) / 100
                )::TEXT AS "Nama",
                '0' AS "Alamat Lengkap",
                0 AS "Jumlah DPP",
                '' AS "Jumlah PPN",
                0 AS "Jumlah PPNBM",
                0 AS "ID Keterangan Tambahan",
                0 AS "FG Uang Muka",
                NULL AS "Uang Muka DPP",
                NULL AS "Uang Muka PPN",
                NULL AS "Uang Muka PPNBM",
                '' AS "Referensi",
                '' AS "Kode Dokumen Pendukung"
            FROM tw_faktur_pajak_out fp
            INNER JOIN tw_work_order wo ON fp.id = wo.faktur_pajak_out_id 
                AND fp.model_id IN (SELECT id FROM ir_model WHERE model = 'tw.work.order')
            INNER JOIN tw_work_order_line wol ON wo.id = wol.order_id
            LEFT JOIN account_tax_tw_work_order_line_rel wolt ON wolt.tw_work_order_line_id = wol.id
            LEFT JOIN account_tax at ON at.id = wolt.account_tax_id
            LEFT JOIN product_product pp ON wol.product_id = pp.id
            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
            WHERE {where_clause}
        """

    def _get_dealer_sale_order_query(self, where_clause, cutoff_date):
        """Build query for Dealer Sale Order details (OF rows)."""
        if not self._table_exists('tw_dealer_sale_order'):
            return None
            
        return f"""
            SELECT 
                fp.id AS fp_id,
                fp.transaction_id,
                dsol.id AS sort_id,
                'OF' AS "FK",
                COALESCE(pt.name->>'en_US', pp.default_code, '') AS "Kode Jenis Transaksi",
                CONCAT('HONDA # ', COALESCE(wps.name->>'en_US', ''), ' # ', COALESCE(pc2.name, ''), ' # MH1', COALESCE(lot.chassis_number, '')) AS "FG Pengganti",
                -- Harga Satuan
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(
                            ROUND((dsol.price_unit / (1 + COALESCE(at.amount, 0) / 100)) 
                            + (COALESCE(dsol.bbn_serv_margin_amount, 0) / (1 + COALESCE(at.amount, 0) / 100))) * 0.91666666667
                        )::TEXT
                    ELSE
                        ROUND(
                            (dsol.price_unit / (1 + COALESCE(at.amount, 0) / 100)) 
                            + (COALESCE(dsol.bbn_serv_margin_amount, 0) / (1 + COALESCE(at.amount, 0) / 100))
                        )::TEXT
                END AS "Nomor Faktur",
                dsol.product_uom_qty::INTEGER AS "Masa Pajak",
                -- Harga Total
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(
                            ROUND(((dsol.price_unit / (1 + COALESCE(at.amount, 0) / 100)) 
                            + (COALESCE(dsol.bbn_serv_margin_amount, 0) / (1 + COALESCE(at.amount, 0) / 100))) 
                            * dsol.product_uom_qty) * 0.91666666667
                        )
                    ELSE
                        ROUND(
                            ((dsol.price_unit / (1 + COALESCE(at.amount, 0) / 100)) 
                            + (COALESCE(dsol.bbn_serv_margin_amount, 0) / (1 + COALESCE(at.amount, 0) / 100))) 
                            * dsol.product_uom_qty
                        )
                END::INTEGER AS "Tahun Pajak",
                -- Diskon
                COALESCE(ROUND((dsol.discount_regular + COALESCE(disc.total, 0)) / (1 + COALESCE(at.amount, 0) / 100)), 0)::TEXT AS "Tanggal Faktur",
                -- DPP
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        COALESCE(
                            ROUND(ROUND(CASE
                                WHEN dsol.is_bbn = TRUE
                                THEN (((dsol.price_unit - (COALESCE(disc.total, 0) + (dsol.discount_regular - COALESCE(vc.total, 0))))
                                        + dsol.bbn_serv_amount
                                        + (dsol.bbn_serv_amount * COALESCE(at.amount, 0) / 100)
                                        + (dsol.bbn_amount - COALESCE(dsol.bbn_purchase_amount, 0)))) / (1 + COALESCE(at.amount, 0) / 100)
                                ELSE (dsol.price_unit - ((dsol.discount_regular + COALESCE(disc.total, 0)) - COALESCE(vc.total, 0))) / (1 + COALESCE(at.amount, 0) / 100) * dsol.product_uom_qty 
                            END) * 0.91666666667), 0)::TEXT
                    ELSE
                        COALESCE(
                            ROUND(CASE
                                WHEN dsol.is_bbn = TRUE
                                THEN (((dsol.price_unit - (COALESCE(disc.total, 0) + (dsol.discount_regular - COALESCE(vc.total, 0))))
                                        + dsol.bbn_serv_amount
                                        + (dsol.bbn_serv_amount * COALESCE(at.amount, 0) / 100)
                                        + (dsol.bbn_amount - COALESCE(dsol.bbn_purchase_amount, 0)))) / (1 + COALESCE(at.amount, 0) / 100)
                                ELSE (dsol.price_unit - ((dsol.discount_regular + COALESCE(disc.total, 0)) - COALESCE(vc.total, 0))) / (1 + COALESCE(at.amount, 0) / 100) * dsol.product_uom_qty 
                            END), 0)::TEXT
                END AS "NPWP",
                -- PPN
                COALESCE(
                    ROUND(CASE
                        WHEN dsol.is_bbn = TRUE
                        THEN ((((dsol.price_unit - (COALESCE(disc.total, 0) + (dsol.discount_regular - COALESCE(vc.total, 0))))
                                + dsol.bbn_serv_amount
                                + (dsol.bbn_serv_amount * COALESCE(at.amount, 0) / 100)
                                + (dsol.bbn_amount - COALESCE(dsol.bbn_purchase_amount, 0)))) / (1 + COALESCE(at.amount, 0) / 100)) * COALESCE(at.amount, 0) / 100
                        ELSE ((dsol.price_unit - ((dsol.discount_regular + COALESCE(disc.total, 0)) - COALESCE(vc.total, 0))) / (1 + COALESCE(at.amount, 0) / 100) * dsol.product_uom_qty) * COALESCE(at.amount, 0) / 100
                    END), 0)::TEXT AS "Nama",
                '0' AS "Alamat Lengkap",
                0 AS "Jumlah DPP",
                '' AS "Jumlah PPN",
                0 AS "Jumlah PPNBM",
                0 AS "ID Keterangan Tambahan",
                0 AS "FG Uang Muka",
                NULL AS "Uang Muka DPP",
                NULL AS "Uang Muka PPN",
                NULL AS "Uang Muka PPNBM",
                '' AS "Referensi",
                '' AS "Kode Dokumen Pendukung"
            FROM tw_faktur_pajak_out fp
            INNER JOIN tw_dealer_sale_order dso ON fp.id = dso.faktur_pajak_out_id
                AND fp.model_id IN (SELECT id FROM ir_model WHERE model = 'tw.dealer.sale.order')
            INNER JOIN tw_dealer_sale_order_line dsol ON dso.id = dsol.order_id
            LEFT JOIN tw_dealer_sale_order_line_tax_rel dsolt ON dsolt.order_line_id = dsol.id
            LEFT JOIN account_tax at ON at.id = dsolt.tax_id
            LEFT JOIN stock_lot lot ON dsol.lot_id = lot.id
            LEFT JOIN product_product pp ON lot.product_id = pp.id
            LEFT JOIN product_template pt ON pp.product_tmpl_id = pt.id
            LEFT JOIN product_series wps ON pt.series_id = wps.id
            LEFT JOIN product_category pc ON pt.categ_id = pc.id
            LEFT JOIN product_category pc2 ON pc.parent_id = pc2.id
            LEFT JOIN (
                SELECT vc.order_line_id AS id, 
                       COALESCE(SUM(vc.amount), 0) AS total
                FROM tw_dealer_sale_order_line_voucher vc
                GROUP BY vc.order_line_id
            ) vc ON vc.id = dsol.id
            LEFT JOIN (
                SELECT disc.order_line_id AS id, 
                       COALESCE(SUM(disc.discount_customer), 0) AS total
                FROM tw_dealer_sale_order_line_program disc
                GROUP BY disc.order_line_id
            ) disc ON disc.id = dsol.id
            WHERE {where_clause}
        """

    def _get_fp_other_query(self, where_clause, cutoff_date):
        """Build query for Faktur Pajak Other details (OF rows)."""
        if not self._table_exists('tw_faktur_pajak_other'):
            return None
            
        return f"""
            SELECT 
                fp.id AS fp_id,
                fp.transaction_id,
                fpo.id AS sort_id,
                'OF' AS "FK",
                '' AS "Kode Jenis Transaksi",
                COALESCE(fpo.memo, '') AS "FG Pengganti",
                -- Harga Satuan
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(ROUND(fpo.untaxed_amount) * 0.91666666667)::TEXT
                    ELSE
                        ROUND(fpo.untaxed_amount)::TEXT
                END AS "Nomor Faktur",
                1 AS "Masa Pajak",
                -- Harga Total
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(ROUND(fpo.untaxed_amount) * 0.91666666667)
                    ELSE
                        ROUND(fpo.untaxed_amount)
                END::INTEGER AS "Tahun Pajak",
                '0' AS "Tanggal Faktur",
                -- DPP
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(ROUND(fpo.untaxed_amount) * 0.91666666667)::TEXT
                    ELSE
                        ROUND(fpo.untaxed_amount)::TEXT
                END AS "NPWP",
                -- PPN
                ROUND(fpo.tax_amount)::TEXT AS "Nama",
                '0' AS "Alamat Lengkap",
                0 AS "Jumlah DPP",
                '' AS "Jumlah PPN",
                0 AS "Jumlah PPNBM",
                0 AS "ID Keterangan Tambahan",
                0 AS "FG Uang Muka",
                NULL AS "Uang Muka DPP",
                NULL AS "Uang Muka PPN",
                NULL AS "Uang Muka PPNBM",
                '' AS "Referensi",
                '' AS "Kode Dokumen Pendukung"
            FROM tw_faktur_pajak_out fp
            INNER JOIN tw_faktur_pajak_other fpo ON fp.transaction_id = fpo.id 
                AND fp.model_id IN (SELECT id FROM ir_model WHERE model = 'tw.faktur.pajak.other')
            WHERE {where_clause}
            AND fpo.pajak_gabungan = TRUE
        """

    def _get_disposal_asset_query(self, where_clause, cutoff_date):
        """Build query for Disposal Asset details (OF rows)."""
        if not self._table_exists('tw_asset_disposal'):
            return None
            
        return f"""
            SELECT 
                fp.id AS fp_id,
                fp.transaction_id,
                da.id AS sort_id,
                'OF' AS "FK",
                '' AS "Kode Jenis Transaksi",
                COALESCE(da.name, '') AS "FG Pengganti",
                -- Harga Satuan
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(ROUND(da.amount_untaxed) * 0.91666666667)::TEXT
                    ELSE
                        ROUND(da.amount_untaxed)::TEXT
                END AS "Nomor Faktur",
                1 AS "Masa Pajak",
                -- Harga Total
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(ROUND(da.amount_untaxed) * 0.91666666667)
                    ELSE
                        ROUND(da.amount_untaxed)
                END::INTEGER AS "Tahun Pajak",
                '0' AS "Tanggal Faktur",
                -- DPP
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(ROUND(da.amount_untaxed) * 0.91666666667)::TEXT
                    ELSE
                        ROUND(da.amount_untaxed)::TEXT
                END AS "NPWP",
                ROUND(da.amount_tax)::TEXT AS "Nama",
                '0' AS "Alamat Lengkap",
                0 AS "Jumlah DPP",
                '' AS "Jumlah PPN",
                0 AS "Jumlah PPNBM",
                0 AS "ID Keterangan Tambahan",
                0 AS "FG Uang Muka",
                NULL AS "Uang Muka DPP",
                NULL AS "Uang Muka PPN",
                NULL AS "Uang Muka PPNBM",
                '' AS "Referensi",
                '' AS "Kode Dokumen Pendukung"
            FROM tw_faktur_pajak_out fp
            INNER JOIN tw_asset_disposal da ON fp.id = da.faktur_pajak_out_id 
                AND fp.model_id IN (SELECT id FROM ir_model WHERE model = 'tw.asset.disposal')
            WHERE {where_clause}
        """

    def _get_other_receivable_query(self, where_clause, cutoff_date):
        """Build query for Other Receivable / DN details (OF rows)."""
        if not self._table_exists('tw_other_receivable'):
            return None
            
        return f"""
            SELECT 
                fp.id AS fp_id,
                fp.transaction_id,
                dn.id AS sort_id,
                'OF' AS "FK",
                '' AS "Kode Jenis Transaksi",
                COALESCE(dn.name, '') AS "FG Pengganti",
                -- Harga Satuan
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(ROUND(fp.untaxed_amount) * 0.91666666667)::TEXT
                    ELSE
                        ROUND(fp.untaxed_amount)::TEXT
                END AS "Nomor Faktur",
                1 AS "Masa Pajak",
                -- Harga Total
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(ROUND(fp.untaxed_amount) * 0.91666666667)
                    ELSE
                        ROUND(fp.untaxed_amount)
                END::INTEGER AS "Tahun Pajak",
                '0' AS "Tanggal Faktur",
                -- DPP
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(ROUND(fp.untaxed_amount) * 0.91666666667)::TEXT
                    ELSE
                        ROUND(fp.untaxed_amount)::TEXT
                END AS "NPWP",
                ROUND(fp.tax_amount)::TEXT AS "Nama",
                '0' AS "Alamat Lengkap",
                0 AS "Jumlah DPP",
                '' AS "Jumlah PPN",
                0 AS "Jumlah PPNBM",
                0 AS "ID Keterangan Tambahan",
                0 AS "FG Uang Muka",
                NULL AS "Uang Muka DPP",
                NULL AS "Uang Muka PPN",
                NULL AS "Uang Muka PPNBM",
                '' AS "Referensi",
                '' AS "Kode Dokumen Pendukung"
            FROM tw_faktur_pajak_out fp
            INNER JOIN tw_other_receivable dn ON fp.id = dn.faktur_pajak_out_id 
                AND fp.model_id IN (SELECT id FROM ir_model WHERE model = 'tw.other.receivable')
            WHERE {where_clause}
        """

    def _get_payment_request_query(self, where_clause, cutoff_date):
        """Build query for Payment Request / NC details (OF rows)."""
        if not self._table_exists('tw_payment_request'):
            return None
            
        return f"""
            SELECT 
                fp.id AS fp_id,
                fp.transaction_id,
                nc.id AS sort_id,
                'OF' AS "FK",
                '' AS "Kode Jenis Transaksi",
                COALESCE(nc.name, '') AS "FG Pengganti",
                -- Harga Satuan
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(ROUND(fp.untaxed_amount) * 0.91666666667)::TEXT
                    ELSE
                        ROUND(fp.untaxed_amount)::TEXT
                END AS "Nomor Faktur",
                1 AS "Masa Pajak",
                -- Harga Total
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(ROUND(fp.untaxed_amount) * 0.91666666667)
                    ELSE
                        ROUND(fp.untaxed_amount)
                END::INTEGER AS "Tahun Pajak",
                '0' AS "Tanggal Faktur",
                -- DPP
                CASE 
                    WHEN fp.date >= '{cutoff_date}'::date THEN
                        ROUND(ROUND(fp.untaxed_amount) * 0.91666666667)::TEXT
                    ELSE
                        ROUND(fp.untaxed_amount)::TEXT
                END AS "NPWP",
                ROUND(fp.tax_amount)::TEXT AS "Nama",
                '0' AS "Alamat Lengkap",
                0 AS "Jumlah DPP",
                '' AS "Jumlah PPN",
                0 AS "Jumlah PPNBM",
                0 AS "ID Keterangan Tambahan",
                0 AS "FG Uang Muka",
                NULL AS "Uang Muka DPP",
                NULL AS "Uang Muka PPN",
                NULL AS "Uang Muka PPNBM",
                '' AS "Referensi",
                '' AS "Kode Dokumen Pendukung"
            FROM tw_faktur_pajak_out fp
            INNER JOIN tw_payment_request nc ON fp.id = nc.faktur_pajak_out_id 
                AND fp.model_id IN (SELECT id FROM ir_model WHERE model = 'tw.payment.request')
            WHERE {where_clause}
        """

    # 13: action methods
    def action_print_report(self):
        """Generate E-Faktur Pajak Excel report.
        
        Dispatches to manual or web.report rendering based on ir.config_parameter.
        """
        self.ensure_one()
        use_web_report = self.env['ir.config_parameter'].sudo().get_param(
            'efaktur.use_web_report', 'False'
        ) == 'True'
        if use_web_report:
            return self._generate_report_web()
        return self._generate_report_manual()

    # 14: private methods
    def _get_union_query(self, where_clause, cutoff_date):
        """Build full UNION query combining header and all detail queries."""
        queries = []
        queries.append(f"({self._get_header_query(where_clause, cutoff_date)})")

        detail_queries = [
            self._get_sale_order_query(where_clause, cutoff_date),
            self._get_work_order_query(where_clause, cutoff_date),
            self._get_dealer_sale_order_query(where_clause, cutoff_date),
            self._get_fp_other_query(where_clause, cutoff_date),
            self._get_disposal_asset_query(where_clause, cutoff_date),
            self._get_other_receivable_query(where_clause, cutoff_date),
            self._get_payment_request_query(where_clause, cutoff_date),
        ]
        for q in detail_queries:
            if q:
                queries.append(f"({q})")

        return f"""
            SELECT * FROM (
                {' UNION '.join(queries)}
            ) a
            ORDER BY fp_id, transaction_id, sort_id
        """

    def _execute_report_query(self):
        """Execute the full eFaktur query and return results + cutoff_date."""
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        where_clause, params = self._build_query_where()
        cutoff_date = self._get_ppn12_cutoff()
        full_query = self._get_union_query(where_clause, cutoff_date)
        self.env.cr.execute(full_query, params)
        return cutoff_date

    def _generate_report_manual(self):
        """Generate eFaktur report using direct xlsxwriter (Odoo 8 style).
        
        Writes cells explicitly per column for exact alignment control.
        Includes DPP/PPN cross-check logic from old code.
        """
        import xlsxwriter

        cutoff_date = self._execute_report_query()
        ress = self.env.cr.fetchall()

        if not ress:
            raise UserError(_("Tidak ada data yang ditemukan untuk kriteria yang dipilih."))

        # Create workbook
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf = self._add_workbook_format(workbook)
        worksheet = workbook.add_worksheet('eFaktur Pajak')

        # Set column widths
        for col_idx in range(20):
            worksheet.set_column(col_idx + 1, col_idx + 1, 20)
        worksheet.set_column(20, 20, 35)  # Column U wider

        # Title rows
        company_name = self.env.company.name
        worksheet.write('A1', company_name, wbf['title_doc'])
        worksheet.write('A2', 'eFaktur Pajak Periode %s - %s' % (
            str(self.start_date), str(self.end_date)
        ), wbf['title_doc'])

        # Header rows (row 4=FK, row 5=LT, row 6=OF) — 0-indexed: row 3,4,5
        row = 3
        row += 1  # row = 4

        # Row FK (row+1 = 5 in 1-indexed = row 4 in 0-indexed)
        worksheet.merge_range('A%s:A%s' % (row + 1, row + 3), 'No', wbf['header'])
        fk_headers = ['FK', 'Kode Jenis Transaksi', 'FG Pengganti', 'Nomor Faktur',
                      'Masa Pajak', 'Tahun Pajak', 'Tanggal Faktur',
                      'NPWP', 'Nama', 'Alamat Lengkap',
                      'Jumlah DPP', 'Jumlah PPN', 'Jumlah PPNBM',
                      'ID Keterangan Tambahan', 'FG Uang Muka', 'Uang Muka DPP',
                      'Uang Muka PPN', 'Uang Muka PPNBM', 'Referensi', 'Kode Dokumen Pendukung']
        for i, h in enumerate(fk_headers):
            worksheet.write(row, i + 1, h, wbf['header'])

        row += 1  # row = 5
        lt_headers = ['LT', 'NPWP', 'Nama', 'Jalan', 'Blok', 'Nomor', 'RT', 'RW',
                      'Kecamatan', 'Kelurahan', 'Kabupaten', 'Propinsi', 'Kode Pos',
                      'Nomor Telepon', ' ', ' ', ' ', ' ', ' ', ' ']
        for i, h in enumerate(lt_headers):
            worksheet.write(row, i + 1, h, wbf['header'])

        row += 1  # row = 6
        of_headers = ['OF', 'Kode Objek', 'Nama', 'Harga Satuan', 'Jumlah Barang',
                      'Harga Total', 'Diskon', 'DPP', 'PPN', 'Tarif PPNBM', 'PPNBM',
                      ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ']
        for i, h in enumerate(of_headers):
            worksheet.write(row, i + 1, h, wbf['header'])

        row += 1  # data starts right after OF header

        # Data rows — cell-by-cell writing like Odoo 8
        no = 1
        total_dpp = 0
        total_ppn = 0
        header_dpp = 0
        header_ppn = 0
        header_row = 0
        fp_date = None

        for res in ress:
            fk = res[3]
            kd_jenis_trans = res[4]
            fg_pengganti = res[5]
            no_faktur = res[6]
            masa_pajak = res[7]
            thn_pajak = res[8]
            tgl_faktur = res[9]
            npwp = res[10]
            nama = res[11]
            alamat = res[12]
            jml_dpp = res[13]
            jml_ppn = res[14]
            jml_ppnbm = res[15]
            id_ket_tambahan = res[16]
            fg_uang_muka = res[17]
            uang_muka_dpp = res[18]
            uang_muka_ppn = res[19]
            uang_muka_ppnbm = res[20]
            referensi = res[21]

            # Cross-check DPP/PPN: replace header with detail totals if different
            if fk == 'FK':
                if header_row and header_dpp != total_dpp:
                    worksheet.write(header_row, 11, total_dpp, wbf['content_number'])  # col L
                if header_row and header_ppn != total_ppn:
                    worksheet.write(header_row, 12, total_ppn, wbf['content_number'])  # col M
                header_row = row
                header_dpp = jml_dpp or 0
                header_ppn = jml_ppn or 0
                total_dpp = 0
                total_ppn = 0
            else:
                # OF row: accumulate DPP/PPN from detail
                try:
                    dpp_val = int(npwp) if npwp else 0  # NPWP column = DPP for OF
                    ppn_val = int(nama) if nama else 0  # Nama column = PPN for OF
                    total_dpp += dpp_val
                    total_ppn += ppn_val
                except (ValueError, TypeError):
                    pass

            # Write common cells
            worksheet.write(row, 0, no, wbf['content_number'])       # A: No
            worksheet.write(row, 1, fk or '', wbf['content'])        # B: FK/OF
            worksheet.write(row, 2, kd_jenis_trans or '', wbf['content'])  # C
            worksheet.write(row, 3, fg_pengganti or '', wbf['content'])    # D
            worksheet.write(row, 5, masa_pajak or '', wbf['content_number'])  # F: Masa Pajak / Jumlah Barang
            worksheet.write(row, 6, thn_pajak or '', wbf['content_number'])  # G: Tahun Pajak / Harga Total

            if fk == 'FK':
                worksheet.write(row, 4, no_faktur or '', wbf['content'])         # E: Nomor Faktur
                worksheet.write(row, 7, tgl_faktur or '', wbf['content'])        # H: Tanggal Faktur
                worksheet.write(row, 8, npwp or '', wbf['content'])              # I: NPWP
                worksheet.write(row, 9, nama or '', wbf['content'])              # J: Nama
                worksheet.write(row, 10, alamat or '', wbf['content'])           # K: Alamat
                worksheet.write(row, 12, jml_ppn or 0, wbf['content_number'])    # M: Jumlah PPN
            else:
                worksheet.write(row, 4, no_faktur or '', wbf['content_number'])  # E: Harga Satuan
                worksheet.write(row, 7, tgl_faktur or '', wbf['content_number']) # H: Diskon
                worksheet.write(row, 8, npwp or '', wbf['content_number'])       # I: DPP
                worksheet.write(row, 9, nama or '', wbf['content_number'])       # J: PPN
                worksheet.write(row, 10, alamat or '', wbf['content_number'])    # K: Tarif PPNBM
                worksheet.write(row, 12, jml_ppn or '', wbf['content'])          # M: Detail Referensi

            worksheet.write(row, 11, jml_dpp or 0, wbf['content_number'])        # L: Jumlah DPP / PPNBM
            worksheet.write(row, 13, jml_ppnbm or 0, wbf['content_number'])      # N
            worksheet.write(row, 14, id_ket_tambahan or '', wbf['content'])       # O
            worksheet.write(row, 15, fg_uang_muka or '', wbf['content'])         # P
            worksheet.write(row, 16, uang_muka_dpp or 0, wbf['content_number'])  # Q
            worksheet.write(row, 17, uang_muka_ppn or 0, wbf['content_number'])  # R
            worksheet.write(row, 18, uang_muka_ppnbm or 0, wbf['content_number']) # S
            worksheet.write(row, 19, referensi or '', wbf['content'])            # T
            worksheet.write(row, 20, '', wbf['content'])                         # U

            no += 1
            row += 1

        # Cross-check DPP/PPN for last group
        if header_row and header_dpp != total_dpp:
            worksheet.write(header_row, 11, total_dpp, wbf['content_number'])
        if header_row and header_ppn != total_ppn:
            worksheet.write(header_row, 12, total_ppn, wbf['content_number'])

        # Auto-filter and freeze
        worksheet.autofilter(7, 0, row - 1, 20)
        worksheet.freeze_panes(8, 3)

        # Footer
        user_name = self.env.user.name
        now_str = fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        worksheet.write(row + 1, 0, '%s %s' % (now_str, user_name), wbf['footer'])

        workbook.close()

        # Save report via web.report
        out = base64.encodebytes(fp.getvalue())
        filename = 'eFaktur Pajak %s.xlsx' % now_str
        report = self.env['web.report'].sudo().create({
            'report_file': out,
            'name': filename,
        })
        fp.close()

        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': '/web/content/web.report/%s/report_file/%s?download=true' % (report.id, filename)
        }

    def _add_workbook_format(self, workbook):
        """Add workbook formats matching Odoo 8 style."""
        wbf = {}

        wbf['header'] = workbook.add_format({
            'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000'
        })
        wbf['header'].set_border()

        wbf['footer'] = workbook.add_format({'align': 'left'})

        wbf['title_doc'] = workbook.add_format({'bold': 1, 'align': 'left'})
        wbf['title_doc'].set_font_size(12)

        wbf['content'] = workbook.add_format()
        wbf['content'].set_left()
        wbf['content'].set_right()

        wbf['content_number'] = workbook.add_format({'align': 'right'})
        wbf['content_number'].set_right()
        wbf['content_number'].set_left()

        wbf['content_date'] = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        wbf['content_date'].set_left()
        wbf['content_date'].set_right()

        return wbf

    def _generate_report_web(self):
        """Generate eFaktur report using web.report module."""
        cutoff_date = self._execute_report_query()
        raw_results = self.env.cr.dictfetchall()

        if not raw_results:
            raise UserError(_("Tidak ada data yang ditemukan untuk kriteria yang dipilih."))

        # Remove metadata columns (fp_id, transaction_id, sort_id) — web.report writes all dict keys
        metadata_keys = {'fp_id', 'transaction_id', 'sort_id'}
        results = [{k: v for k, v in row.items() if k not in metadata_keys} for row in raw_results]

        web_report = self.env['web.report']
        col_name = web_report._excel_index_to_column_name

        fk_labels = [
            '', 'FK', 'Kode Jenis Transaksi', 'FG Pengganti', 'Nomor Faktur',
            'Masa Pajak', 'Tahun Pajak', 'Tanggal Faktur',
            'NPWP', 'Nama', 'Alamat Lengkap',
            'Jumlah DPP', 'Jumlah PPN', 'Jumlah PPNBM',
            'ID Keterangan Tambahan', 'FG Uang Muka', 'Uang Muka DPP',
            'Uang Muka PPN', 'Uang Muka PPNBM', 'Referensi', 'Kode Dokumen Pendukung'
        ]
        lt_labels = [
            'No', 'LT', 'NPWP', 'Nama', 'Jalan',
            'Blok', 'Nomor', 'RT', 'RW',
            'Kecamatan', 'Kelurahan', 'Kabupaten',
            'Propinsi', 'Kode Pos', 'Nomor Telepon',
            '', '', '', '', '', ''
        ]
        of_labels = [
            '', 'OF', 'Kode Objek', 'Nama', 'Harga Satuan',
            'Jumlah Barang', 'Harga Total', 'Diskon',
            'DPP', 'PPN', 'Tarif PPNBM', 'PPNBM',
            '', '', '', '', '', '', '', '', ''
        ]

        custom_header = {}
        for i, label in enumerate(fk_labels):
            custom_header[f'{col_name(i + 1)}4'] = label
        for i, label in enumerate(lt_labels):
            custom_header[f'{col_name(i + 1)}5'] = label
        for i, label in enumerate(of_labels):
            custom_header[f'{col_name(i + 1)}6'] = label

        return web_report.generate_report(
            report_name='eFaktur Pajak',
            data=results,
            data_summary_header=custom_header,
            data_summary_style='header',
            start_date=self.start_date,
            end_date=self.end_date,
            capitalize=False,
            numbering=True,
            header=False,
            auto_filter=True,
            freeze_panes=True,
            show_total_footer=False,
        )
