# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
import pytz
import base64
import csv
import xlsxwriter
import calendar
from io import StringIO,BytesIO
from datetime import date, datetime, time, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwReportB2BDGIRetailWizard(models.TransientModel):
    _name = 'tw.dgi.report.wizard'
    _description = 'Laporan Utilisasi DGI'

    def _get_default_start_date(self):
        return datetime.now().replace(day=1).date()

    def _get_default_end_date(self):
        return datetime.now().date()

    def _get_default_endpoint_ids(self):
        """Default recordset for the wizard - ensuring unique codes."""
        div_values = [self.division] if self.division in ('H1', 'H23') else ['H1', 'H23']
            
        domain = [
            ('dgi_division_id.type', '=', 'DivisionDGI'),
            ('dgi_division_id.value', 'in', div_values)
        ]
        
        # Use _read_group to perform deduplication directly in the database (GROUP BY code)
        endpoints_data = self.env['tw.endpoint.configuration'].sudo()._read_group(
            domain, ['code'], ['id:min']
        )
        unique_ids = [ep_id for code, ep_id in endpoints_data if ep_id]
        
        return self.env['tw.endpoint.configuration'].sudo().browse(unique_ids)

    start_date = fields.Date(string='Start Date', default=_get_default_start_date)
    end_date = fields.Date(string='End Date', default=_get_default_end_date)
    division = fields.Selection([
        ('H123', 'H123'),
        ('H1', 'H1'),
        ('H23', 'H23')
    ], string='Division', default='H123')
    
    report_type = fields.Selection([
        ('summary', 'Summary'),
        ('detail', 'Detail')
    ], string='Report Type', required=True, default='summary')

    report_summary_type = fields.Selection([
        ('per_bulan', 'Per Bulan'),
        ('per_hari', 'Per Hari')
    ], string='Report Summary Type', default='per_bulan')
    
    end_point_ids = fields.Many2many('tw.endpoint.configuration', string='Titik DGI', default=_get_default_endpoint_ids)
    available_endpoint_ids = fields.Many2many('tw.endpoint.configuration', compute='_compute_available_endpoints', string='Available Titik DGI')
    company_ids = fields.Many2many('res.company', 'report_dgi_company_rel', 'tw_dgi_report_wizard_id', 'res_company_id', string='Branch', domain="[('active', '=', True), ('branch_type_id.value', '=', 'DL')]")
    md_ids = fields.Many2many('res.partner', 'report_dgi_md_rel', 'tw_dgi_report_wizard_id', 'partner_id', string='Main Dealer', domain="[('active', '=', True), ('category_id.name','=','Principle')]")

    @api.depends('division')
    def _compute_available_endpoints(self):
        for record in self:
            record.available_endpoint_ids = record._get_default_endpoint_ids()

    @api.onchange('start_date', 'end_date')
    def _check_date(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise Warning('End date tidak boleh kurang dari start date!')
            if hasattr(self.env['web.report'], '_check_date_range_limit'):
                self.env['web.report'].sudo()._check_date_range_limit(record.start_date, record.end_date)

    @api.onchange('division')
    def _onchange_division(self):
        self.end_point_ids = self._get_default_endpoint_ids()
    
    def action_export_excel(self):
        self.ensure_one()
        if hasattr(self.env['web.report'], '_check_date_range_limit'):
            self.env['web.report'].sudo()._check_date_range_limit(self.start_date, self.end_date)
            
        if self.report_type == 'summary':
            return self._print_summary_report()
        else:
            return self._print_detail_report()

    def _get_division_list(self):
        """Map wizard division to internal database values."""
        if self.division == 'H1':
            return ['Unit']
        elif self.division == 'H23':
            return ['Sparepart']
        return ['Unit', 'Sparepart']

    def _get_where_clause(self, table_alias='b', trx_alias=False):
        where = ""
        if self.company_ids:
            where += f" AND {table_alias}.id IN ({','.join(map(str, self.company_ids.ids))}) "
        if self.md_ids:
            where += f" AND parent.id IN ({','.join(map(str, self.md_ids.ids))}) "
        
        if trx_alias:
            divs = self._get_division_list()
            divs_str = ','.join([f"'{d}'" for d in divs])
            where += f" AND {trx_alias}.division IN ({divs_str}) "
            
        return where

    def _print_summary_report(self):
        query = self._set_query_summary()
        self._cr.execute(query)
        res = self._cr.dictfetchall()
        
        report_name = 'Laporan Summary Utilisasi DGI'
        summary_header = {
            'A1': self.env.company.name,
            'A2': report_name,
            'A3': 'Periode: %s s/d %s' % (self.start_date, self.end_date),
            'A4': 'Division: %s | Summary: %s' % (dict(self._fields['division'].selection).get(self.division), dict(self._fields['report_summary_type'].selection).get(self.report_summary_type)),
        }
        
        return self.env['web.report'].sudo().generate_report(report_name, res, data_summary_header=summary_header)

    def _print_detail_report(self):
        query = self._set_query_detail()
        self._cr.execute(query)
        res = self._cr.dictfetchall()
        
        report_name = 'Laporan Detail Utilisasi DGI'
        summary_header = {
            'A1': self.env.company.name,
            'A2': report_name,
            'A3': 'Periode: %s s/d %s' % (self.start_date, self.end_date),
            'A4': 'Division: %s' % dict(self._fields['division'].selection).get(self.division),
        }
        
        return self.env['web.report'].sudo().generate_report(report_name, res, data_summary_header=summary_header)

    def _get_endpoint_code(self, endpoint):
        """Map configuration codes to standard reporting keys."""
        code = endpoint.code.upper() if endpoint.code else ''
        if 'UINB' in code: return 'UINB'
        if 'SPK' in code: return 'SPK'
        if 'PROSPECT' in code: return 'PRSP'
        if 'LSNG' in code: return 'LSNG'
        if 'BAST' in code: return 'BAST'
        if 'INV1' in code: return 'INV1'
        if 'DOCH_PROSES' in code: return 'DOCH_PROSES'
        if 'DOCH_RECEIPT_STNK' in code: return 'DOCH_TERIMA_STNK'
        if 'DOCH_RECEIPT_BPKB' in code: return 'DOCH_TERIMA_BPKB'
        if 'DOCH_HANDOVER_STNK' in code: return 'DOCH_SERAH_STNK'
        if 'DOCH_HANDOVER_BPKB' in code: return 'DOCH_SERAH_BPKB'
        if 'PINB' in code: return 'PINB'
        if 'WO' in code: return 'PKB'
        if 'PRSL' in code: return 'PRSL'
        if 'INV2' in code: return 'INV2'
        return False

    def _get_endpoints_by_division(self, division):
        """Define which standard keys belong to which division based on metadata."""
        div_values = [division] if division in ['H1', 'H23'] else ['H1', 'H23']
        domain = [
            ('dgi_division_id.type', '=', 'DivisionDGI'),
            ('dgi_division_id.value', 'in', div_values)
        ]
        endpoints = self.env['tw.endpoint.configuration'].sudo().search(domain)
        codes = []
        for ep in endpoints:
            code = self._get_endpoint_code(ep)
            if code:
                codes.append(code)
        return list(set(codes))

    def _get_active_endpoint_codes(self):
        """Return a list of standardized keys for SQL building."""
        if not self.end_point_ids:
            return self._get_endpoints_by_division(self.division)
        
        active = []
        for ep in self.end_point_ids:
            code = self._get_endpoint_code(ep)
            if code:
                active.append(code)
        
        return list(set(active))

    def _set_query_summary(self):
        start_date = self.start_date
        end_date = self.end_date
        divs = self._get_division_list()
        active_eps = self._get_active_endpoint_codes()
        
        period_interval = '1 month' if self.report_summary_type == 'per_bulan' else '1 day'
        date_format = 'YYYY-MM' if self.report_summary_type == 'per_bulan' else 'YYYY-MM-DD'
        date_label = 'Bulan' if self.report_summary_type == 'per_bulan' else 'Tanggal'
        
        # CTE for Period and Branches
        base_queries = f"""
            WITH periods AS (
                SELECT TO_CHAR(i, '{date_format}') as d_group
                FROM GENERATE_SERIES('{start_date}'::date, '{end_date}'::date, '{period_interval}'::INTERVAL) i
                GROUP BY 1
            ),
            branches AS (
                SELECT 
                    b.id as branch_id, 
                    b.name as branch_name,
                    supplier.id as md_id,
                    supplier.name as md_name
                FROM res_company b
                JOIN res_company parent ON parent.id = b.parent_id
                JOIN res_partner supplier ON supplier.id = parent.partner_id
                WHERE b.active = True AND b.branch_type_id IS NOT NULL 
                {self._get_where_clause(table_alias='b')}
            ),
            base_grid AS (
                SELECT b.*, p.d_group FROM branches b CROSS JOIN periods p
            )
        """

        endpoint_subqueries = []
        
        # Helper to build subquery for an endpoint
        def build_ep_subquery(ep_key, table, date_field, dgi_condition, extra_where="", alias='t'):
            tz_offset = " + INTERVAL '7 hours'" if date_field != 'invoice_date' else ""
            return f"""
                {ep_key}_data AS (
                    SELECT 
                        {alias}.company_id as branch_id,
                        TO_CHAR({alias}.{date_field}{tz_offset}, '{date_format}') as d_group,
                        COUNT({alias}.id) as total_all,
                        COUNT({alias}.id) FILTER (WHERE {dgi_condition}) as total_dgi
                    FROM {table} {alias}
                    WHERE {alias}.{date_field}::date BETWEEN '{start_date}'::date - INTERVAL '1 day' AND '{end_date}'::date + INTERVAL '1 day'
                    {extra_where}
                    GROUP BY 1, 2
                )
            """

        # H1 Endpoints
        if 'Unit' in divs:
            if 'UINB' in active_eps:
                endpoint_subqueries.append(f"""
                    UINB_data AS (
                        SELECT branch_id, d_group, SUM(total_all) as total_all, SUM(total_dgi) as total_dgi FROM (
                            SELECT po.company_id as branch_id, TO_CHAR(po.date_order + INTERVAL '7 hours', '{date_format}') as d_group, COUNT(po.id) as total_all, COUNT(po.id) FILTER (WHERE po.is_dgi = True) as total_dgi
                            FROM purchase_order po WHERE po.division = 'Unit' AND po.date_order::date BETWEEN '{start_date}'::date - INTERVAL '1 day' AND '{end_date}'::date + INTERVAL '1 day' GROUP BY 1,2
                            UNION ALL
                            SELECT sd.company_id as branch_id, TO_CHAR(sd.date + INTERVAL '7 hours', '{date_format}') as d_group, COUNT(sd.id) as total_all, COUNT(sd.id) FILTER (WHERE sd.model_name IS NOT NULL) as total_dgi
                            FROM tw_stock_distribution sd WHERE sd.division = 'Unit' AND sd.date::date BETWEEN '{start_date}'::date - INTERVAL '1 day' AND '{end_date}'::date + INTERVAL '1 day' GROUP BY 1,2
                        ) uinb_raw GROUP BY 1,2
                    )
                """)
            if 'SPK' in active_eps:
                endpoint_subqueries.append(build_ep_subquery('SPK', 'tw_dealer_spk', 'create_date', 'spk.is_dgi = True', alias='spk'))
            if 'PRSP' in active_eps:
                endpoint_subqueries.append(build_ep_subquery('PRSP', 'tw_lead', 'create_date', 'lead.is_dgi = True', alias='lead'))
            if 'LSNG' in active_eps:
                endpoint_subqueries.append(build_ep_subquery('LSNG', 'tw_dealer_spk', 'create_date', "lsng.is_dgi = True AND lsng.finco_id IS NOT NULL", alias='lsng'))
            if 'BAST' in active_eps:
                endpoint_subqueries.append(build_ep_subquery('BAST', 'stock_picking_batch', 'create_date', 'batch.is_dgi = True', alias='batch'))
            if 'INV1' in active_eps:
                endpoint_subqueries.append(build_ep_subquery('INV1', 'account_move', 'invoice_date', "(SELECT is_dgi FROM tw_dealer_sale_order WHERE name = inv.invoice_origin LIMIT 1) = True", "AND inv.move_type = 'out_invoice' AND (SELECT division FROM tw_dealer_sale_order WHERE name = inv.invoice_origin LIMIT 1) = 'Unit'", alias='inv'))
            
            doch_map = {
                'DOCH_PROSES': 'tw_vehicle_registration_process',
                'DOCH_TERIMA_STNK': 'tw_vehicle_registration_receipt',
                'DOCH_TERIMA_BPKB': 'tw_vehicle_ownership_receipt',
                'DOCH_SERAH_STNK': 'tw_vehicle_registration_handover',
                'DOCH_SERAH_BPKB': 'tw_vehicle_ownership_handover'
            }
            for ep, table in doch_map.items():
                if ep in active_eps:
                    endpoint_subqueries.append(build_ep_subquery(ep, table, 'create_date', f'{ep.lower()}.is_dgi = True', alias=ep.lower()))

        # H23 Endpoints
        if 'Sparepart' in divs:
            if 'PINB' in active_eps:
                endpoint_subqueries.append(f"""
                    PINB_data AS (
                        SELECT branch_id, d_group, SUM(total_all) as total_all, SUM(total_dgi) as total_dgi FROM (
                            SELECT po.company_id as branch_id, TO_CHAR(po.date_order + INTERVAL '7 hours', '{date_format}') as d_group, COUNT(po.id) as total_all, COUNT(po.id) FILTER (WHERE po.is_dgi = True) as total_dgi
                            FROM purchase_order po WHERE po.division = 'Sparepart' AND po.date_order::date BETWEEN '{start_date}'::date - INTERVAL '1 day' AND '{end_date}'::date + INTERVAL '1 day' GROUP BY 1,2
                            UNION ALL
                            SELECT sd.company_id as branch_id, TO_CHAR(sd.date + INTERVAL '7 hours', '{date_format}') as d_group, COUNT(sd.id) as total_all, COUNT(sd.id) FILTER (WHERE sd.model_name IS NOT NULL) as total_dgi
                            FROM tw_stock_distribution sd WHERE sd.division = 'Sparepart' AND sd.date::date BETWEEN '{start_date}'::date - INTERVAL '1 day' AND '{end_date}'::date + INTERVAL '1 day' GROUP BY 1,2
                        ) pinb_raw GROUP BY 1,2
                    )
                """)
            if 'PKB' in active_eps:
                endpoint_subqueries.append(build_ep_subquery('PKB', 'tw_work_order', 'date', 'wo.is_dgi = True', "AND wo.type != 'SLS'", alias='wo'))
            if 'PRSL' in active_eps:
                endpoint_subqueries.append(build_ep_subquery('PRSL', 'tw_work_order', 'date', 'wo.is_dgi = True', "AND wo.type = 'SLS'", alias='wo'))
            if 'INV2' in active_eps:
                endpoint_subqueries.append(build_ep_subquery('INV2', 'account_move', 'invoice_date', "(SELECT is_dgi FROM tw_work_order WHERE name = inv.invoice_origin LIMIT 1) = True", "AND inv.move_type = 'out_invoice' AND (SELECT division FROM tw_work_order WHERE name = inv.invoice_origin LIMIT 1) = 'Sparepart'", alias='inv'))

        # Final Query Assembly
        final_cols = []
        final_joins = []
        for ep in active_eps:
            final_cols.append(f'COALESCE({ep}.total_all, 0) as "{ep} All", COALESCE({ep}.total_dgi, 0) as "{ep} DGI", (COALESCE({ep}.total_all, 0) - COALESCE({ep}.total_dgi, 0)) as "{ep} not DGI"')
            final_joins.append(f'LEFT JOIN {ep}_data {ep} ON g.branch_id = {ep}.branch_id AND g.d_group = {ep}.d_group')

        query = f"""
            {base_queries},
            {", ".join(endpoint_subqueries)}
            SELECT 
                g.md_name as "Main Dealer",
                g.branch_name as "Nama Cabang",
                g.d_group as "Periode",
                {", ".join(final_cols)}
            FROM base_grid g
            {" ".join(final_joins)}
            ORDER BY g.md_name, g.branch_name, g.d_group
        """
        return query

    def _set_query_detail(self):
        start_date = self.start_date
        end_date = self.end_date
        divs = self._get_division_list()
        active_eps = self._get_active_endpoint_codes()
        
        union_queries = []
        
        # H1 Endpoints
        if 'Unit' in divs:
            if 'UINB' in active_eps:
                union_queries.append(f"""
                    SELECT t.company_id as branch_id, t.date_order + INTERVAL '7 hours' as tgl_trx, 'H1 - UINB' as end_point, t.name as no_trx, t.md_reference_po as no_trx_md, NULL as no_prsp_md, NULL as no_lsng_md
                    FROM purchase_order t WHERE t.division = 'Unit' AND t.date_order::date BETWEEN '{start_date}' AND '{end_date}' AND t.is_dgi = True
                    UNION ALL
                    SELECT t.company_id as branch_id, t.date + INTERVAL '7 hours' as tgl_trx, 'H1 - UINB' as end_point, t.name as no_trx, t.origin as no_trx_md, NULL as no_prsp_md, NULL as no_lsng_md
                    FROM tw_stock_distribution t WHERE t.division = 'Unit' AND t.date::date BETWEEN '{start_date}' AND '{end_date}' AND t.model_name IS NOT NULL
                """)
            if 'SPK' in active_eps:
                union_queries.append(f"""
                    SELECT spk.company_id as branch_id, spk.create_date + INTERVAL '7 hours' as tgl_trx, 'H1 - SPK' as end_point, spk.name as no_trx, spk.source_document as no_trx_md, spk.lead_reference as no_prsp_md, NULL as no_lsng_md
                    FROM tw_dealer_spk spk WHERE spk.create_date::date BETWEEN '{start_date}' AND '{end_date}' AND spk.is_dgi = True
                """)
            if 'PRSP' in active_eps:
                union_queries.append(f"""
                    SELECT company_id as branch_id, create_date + INTERVAL '7 hours' as tgl_trx, 'H1 - PRSP' as end_point, name as no_trx, source_document as no_trx_md, NULL as no_prsp_md, NULL as no_lsng_md
                    FROM tw_lead WHERE create_date::date BETWEEN '{start_date}' AND '{end_date}' AND is_dgi = True
                """)
            if 'LSNG' in active_eps:
                union_queries.append(f"""
                    SELECT lsng.company_id as branch_id, lsng.create_date + INTERVAL '7 hours' as tgl_trx, 'H1 - LSNG' as end_point, lsng.name as no_trx, lsng.source_document as no_trx_md, NULL as no_prsp_md, NULL as no_lsng_md
                    FROM tw_dealer_spk lsng WHERE lsng.create_date::date BETWEEN '{start_date}' AND '{end_date}' AND lsng.is_dgi = True AND lsng.finco_id IS NOT NULL
                """)
            if 'BAST' in active_eps:
                union_queries.append(f"""
                    SELECT company_id as branch_id, create_date + INTERVAL '7 hours' as tgl_trx, 'H1 - BAST' as end_point, name as no_trx, NULL as no_trx_md, NULL as no_prsp_md, NULL as no_lsng_md
                    FROM stock_picking_batch WHERE create_date::date BETWEEN '{start_date}' AND '{end_date}' AND is_dgi = True
                """)
            if 'INV1' in active_eps:
                union_queries.append(f"""
                    SELECT t.company_id as branch_id, t.invoice_date as tgl_trx, 'H1 - INV1' as end_point, t.name as no_trx, t.invoice_origin as no_trx_md, NULL as no_prsp_md, NULL as no_lsng_md
                    FROM account_move t WHERE t.move_type = 'out_invoice' AND t.invoice_date BETWEEN '{start_date}' AND '{end_date}' AND (SELECT is_dgi FROM tw_dealer_sale_order WHERE name = t.invoice_origin LIMIT 1) = True
                    AND (SELECT division FROM tw_dealer_sale_order WHERE name = t.invoice_origin LIMIT 1) = 'Unit'
                """)

            doch_map = {
                'DOCH_PROSES': ('tw_vehicle_registration_process', 'H1 - DOCH 1'),
                'DOCH_TERIMA_STNK': ('tw_vehicle_registration_receipt', 'H1 - DOCH 2'),
                'DOCH_TERIMA_BPKB': ('tw_vehicle_ownership_receipt', 'H1 - DOCH 3'),
                'DOCH_SERAH_STNK': ('tw_vehicle_registration_handover', 'H1 - DOCH 4'),
                'DOCH_SERAH_BPKB': ('tw_vehicle_ownership_handover', 'H1 - DOCH 5')
            }
            for ep, (table, label) in doch_map.items():
                if ep in active_eps:
                    union_queries.append(f"""
                        SELECT company_id as branch_id, create_date + INTERVAL '7 hours' as tgl_trx, '{label}' as end_point, name as no_trx, NULL as no_trx_md, NULL as no_prsp_md, NULL as no_lsng_md
                        FROM {table} WHERE create_date::date BETWEEN '{start_date}' AND '{end_date}' AND is_dgi = True
                    """)

        # H23 Endpoints
        if 'Sparepart' in divs:
            if 'PINB' in active_eps:
                union_queries.append(f"""
                    SELECT t.company_id as branch_id, t.date_order + INTERVAL '7 hours' as tgl_trx, 'H23 - PINB' as end_point, t.name as no_trx, t.md_reference_po as no_trx_md, NULL as no_prsp_md, NULL as no_lsng_md
                    FROM purchase_order t WHERE t.division = 'Sparepart' AND t.date_order::date BETWEEN '{start_date}' AND '{end_date}' AND t.is_dgi = True
                    UNION ALL
                    SELECT t.company_id as branch_id, t.date + INTERVAL '7 hours' as tgl_trx, 'H23 - PINB' as end_point, t.name as no_trx, t.origin as no_trx_md, NULL as no_prsp_md, NULL as no_lsng_md
                    FROM tw_stock_distribution t WHERE t.division = 'Sparepart' AND t.date::date BETWEEN '{start_date}' AND '{end_date}' AND t.model_name IS NOT NULL
                """)
            if 'PKB' in active_eps:
                union_queries.append(f"""
                    SELECT 
                        two.company_id as branch_id, 
                        two.date + INTERVAL '7 hours' as tgl_trx, 
                        'H23 - PKB' as end_point, name as no_trx, 
                        CASE 
                            WHEN two.md_reference_pkb IS NOT NULL THEN md_reference_pkb 
                            WHEN two.md_reference_sa IS NOT NULL THEN md_reference_sa 
                        END as no_trx_md, 
                        NULL as no_prsp_md, 
                        NULL as no_lsng_md
                    FROM tw_work_order two
                    LEFT JOIN tw_selection ts ON ts.id = two.type_id 
                    WHERE two.date::date BETWEEN '{start_date}' AND '{end_date}' AND is_dgi = True AND ts.value != 'SLS'
                """)
            if 'PRSL' in active_eps:
                union_queries.append(f"""
                    SELECT 
                        two.company_id as branch_id, 
                        two.date + INTERVAL '7 hours' as tgl_trx, 
                        'H23 - PRSL' as end_point, two.name as no_trx, 
                        CASE 
                            WHEN two.md_reference_pkb IS NOT NULL THEN md_reference_pkb 
                            ELSE NULL 
                        END as no_trx_md, 
                        NULL as no_prsp_md, 
                        NULL as no_lsng_md
                    FROM tw_work_order two
                    LEFT JOIN tw_selection ts ON ts.id = two.type_id 
                    WHERE two.date::date BETWEEN '{start_date}' AND '{end_date}' AND is_dgi = True AND ts.value = 'SLS'
                """)
            if 'INV2' in active_eps:
                union_queries.append(f"""
                    SELECT t.company_id as branch_id, t.invoice_date as tgl_trx, 'H23 - INV2' as end_point, t.name as no_trx, t.invoice_origin as no_trx_md, NULL as no_prsp_md, NULL as no_lsng_md
                    FROM account_move t WHERE t.move_type = 'out_invoice' AND t.invoice_date BETWEEN '{start_date}' AND '{end_date}' AND (SELECT is_dgi FROM tw_work_order WHERE name = t.invoice_origin LIMIT 1) = True
                    AND (SELECT division FROM tw_work_order WHERE name = t.invoice_origin LIMIT 1) = 'Sparepart'
                """)

        if not union_queries:
            return "SELECT 'No Data' as nama_md, 'No Data' as nama_cabang, NULL as tgl_trx, '' as end_point, '' as no_trx, '' as no_trx_md, '' as no_prsp_md, '' as no_lsng_md"

        query = f"""
            SELECT 
                supplier.name as "Main Dealer",
                b.name as "Nama Cabang",
                detail.tgl_trx as "Tgl Transaksi",
                detail.end_point as "Titik DGI",
                detail.no_trx as "Nomor Transaksi",
                detail.no_trx_md as "Nomor Transaksi MD",
                detail.no_prsp_md as "Nomor Prospek MD",
                detail.no_lsng_md as "Nomor Leasing MD"
            FROM res_company b
            JOIN res_company parent ON parent.id = b.parent_id
            JOIN res_partner supplier ON supplier.id = parent.partner_id
            JOIN ({ " UNION ALL ".join(union_queries) }) detail ON detail.branch_id = b.id
            WHERE b.active = True
            {self._get_where_clause(table_alias='b')}
            ORDER BY 1, 2, 3
        """
        return query
