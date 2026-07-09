# -*- coding: utf-8 -*-

# 1: imports of python lib
import math
from datetime import date, datetime
from itertools import groupby
from operator import itemgetter

# 2: import of known third party lib

# 3: imports of odoo
from odoo import models, fields, api

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwReportBranchGrading(models.TransientModel):
    """
    Laporan Branch Grading - Excel Report Wizard
    
    Menampilkan detail grading cabang berdasarkan piutang outstanding
    dan summary dengan perhitungan risk score menggunakan tw.calculator.risk.
    
    Output:
        - Sheet 1: Detail Grading Cabang
        - Sheet 2: Summary Grading Cabang
    """
    _name = "tw.report.branch.grading"
    _description = "Report Branch Grading"

    # 7: defaults methods

    # 8: fields
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    division = fields.Selection([
        ('Unit', 'Unit'),
        ('Sparepart', 'Sparepart'),
    ], string='Division', default='Unit')
    options = fields.Selection([
        ('current', 'Current Outstanding Piutang'),
        ('all', 'All Piutang'),
        ('Unit', 'Piutang Unit'),
        ('Other', 'Other Receivable'),
    ], string='Options', default='current')
    status = fields.Selection([
        ('reconciled', 'Reconciled'),
        ('outstanding', 'Outstanding'),
    ], string='Status')

    # 9: relation fields
    company_ids = fields.Many2many('res.company', string='Branch')
    partner_ids = fields.Many2many('res.partner', string='Partners')
    account_ids = fields.Many2many('account.account', string='Accounts')
    journal_ids = fields.Many2many('account.journal', string='Journals')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_tw_report_branch_grading_wizard(self):
        """
        Server action untuk membuka wizard Report Branch Grading
        dengan default accounts dari ir.config_parameter.
        
        Returns:
            dict: Action window configuration
        """
        ir_config = self.env['ir.config_parameter']
        parameter = ir_config.sudo().search([
            ('key', '=', 'tw.accounting.default_branch_grading_account')
        ], limit=1)
        
        if not parameter:
            raise Warning(
                'Tidak ada konfigurasi parameter yang tepat!\n'
                'Silahkan buat System Parameter baru dengan key (tanpa kutip): '
                '"tw.accounting.default_branch_grading_account" '
                'dan value:\n\n'
                '["11210202", "11210203", "11319902", "11319904", "11319912", "11319914"]'
            )
        
        import ast
        grading_account_code = ast.literal_eval(parameter.value)
        account_ids = self.env['account.account'].search([('code', 'in', grading_account_code)])
        
        return {
            'name': 'Report Branch Grading',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_id': self.env.ref('tw_report_branch_grading.view_tw_report_branch_grading_form').id,
            'target': 'new',
            'context': {
                'default_account_ids': [(6, 0, account_ids.ids)]
            },
        }

    def _get_where_clause(self):
        """Build SQL WHERE clause for filtering"""
        query_where = ''
        
        if self.division:
            query_where += f" AND aml.division = '{self.division}'"
        if self.start_date:
            query_where += f" AND aml.date >= '{self.start_date}'"
        if self.end_date:
            query_where += f" AND aml.date <= '{self.end_date}'"
        if self.status == 'reconciled':
            query_where += " AND (aml.debit = aml.credit)"
        elif self.status == 'outstanding' and self.options == 'all':
            query_where += " AND (aml.debit is null or aml.debit != aml.credit)"
        if self.company_ids:
            query_where += f" AND aml.company_id IN ({', '.join(str(b.id) for b in self.company_ids)})"
        else:
            companies = self.env.user._get_company_ids()
            query_where += f" AND aml.company_id IN {str(tuple(companies)).replace(',)', ')')}"
        if self.partner_ids:
            partner_ids = ', '.join(str(p.id) for p in self.partner_ids)
            query_where += f" AND aml.partner_id IN ({partner_ids})"
        if self.account_ids:
            account_ids = ', '.join(str(a.id) for a in self.account_ids)
            query_where += f" AND aml.account_id IN ({account_ids})"
        if self.journal_ids:
            journal_ids = ', '.join(str(j.id) for j in self.journal_ids)
            query_where += f" AND aml.journal_id IN ({journal_ids})"
        
        return query_where

    def _get_detail_query(self):
        """Return main SQL query for branch grading detail"""
        query_where = self._get_where_clause()
        
        query = """
            SELECT 
                b.code AS "CABANG",
                aml.division AS "DIVISION",
                rp.code AS "PARTNER_CODE",
                rp.name AS "PARTNER_NAME",
                acc.code_store->>'1' AS "NO_REK",
                COALESCE(acc.name->>'en_US', acc.name->>'id_ID', acc.name::text) AS "JENIS_AR",
                m.name AS "NO_SISTEM",
                aml.ref AS "NAMA_TRANSAKSI",
                aml.date AS "TANGGAL",
                EXTRACT(YEAR FROM aml.date)::INTEGER AS "TAHUN",
                -- Start claim calculation
                CASE
                    WHEN acc.sla > 0 THEN DATE_TRUNC('month', aml.date + (acc.sla || ' days')::INTERVAL)::DATE
                    ELSE (COALESCE(aml.date_maturity, aml.date) + INTERVAL '1 day')::DATE
                END AS "START_CLAIM",
                -- Master SLA from account.account.sla field
                COALESCE(acc.sla, 0)::INTEGER AS "MASTER_SLA",
                -- End claim = start_claim + master_sl days
                CASE
                    WHEN acc.sla > 0 THEN (DATE_TRUNC('month', aml.date + (acc.sla || ' days')::INTERVAL) + (acc.sla || ' days')::INTERVAL)::DATE
                    ELSE (COALESCE(aml.date_maturity, aml.date) + INTERVAL '1 day' + (COALESCE(acc.sla, 0) || ' days')::INTERVAL)::DATE
                END AS "END_CLAIM",
                -- SLA days: difference between now and start_claim
                CASE
                    WHEN acc.sla > 0 THEN CAST(EXTRACT('day' FROM NOW() - DATE_TRUNC('month', aml.date + (acc.sla || ' days')::INTERVAL)) AS INTEGER)
                    ELSE CAST(EXTRACT('day' FROM NOW() - (aml.date_maturity + INTERVAL '1 days')) AS INTEGER)
                END AS "SLA",
                -- SLA OD: difference between now and end_claim
                CASE
                    WHEN acc.sla > 0 THEN CAST(EXTRACT('day' FROM NOW() - (DATE_TRUNC('month', aml.date + (acc.sla || ' days')::INTERVAL) + (acc.sla || ' days')::INTERVAL)) AS INTEGER)
                    ELSE CAST(EXTRACT('day' FROM NOW() - (COALESCE(aml.date_maturity, aml.date) + INTERVAL '1 day' + (COALESCE(acc.sla, 0) || ' days')::INTERVAL)) AS INTEGER)
                END AS "SLA_OD",
                -- OD Status
                CASE
                    WHEN (
                        CASE
                            WHEN acc.sla > 0 THEN EXTRACT('day' FROM NOW() - (DATE_TRUNC('month', aml.date + (acc.sla || ' days')::INTERVAL) + (acc.sla || ' days')::INTERVAL))
                            ELSE EXTRACT('day' FROM NOW() - (COALESCE(aml.date_maturity, aml.date) + INTERVAL '1 day' + (COALESCE(acc.sla, 0) || ' days')::INTERVAL))
                        END
                    ) > 0 THEN 'OD'
                    ELSE 'Belum OD'
                END AS "OD_STATUS",
                aml.debit AS "TOTAL_INVOICE",
                -- Residual final: only count for first occurrence of partial
                CASE 
                    WHEN aml.matching_number IS NULL THEN A3.balance
                    WHEN ROW_NUMBER() OVER (PARTITION BY aml.matching_number ORDER BY aml.id) = 1 THEN A3.balance
                    ELSE 0
                END AS "SISA_PIUTANG",
                CASE 
                    WHEN b.code = 'MMA' THEN 'MD Babel'
                    WHEN b.code = 'MML' THEN 'MD Lampung'
                    WHEN b.code = 'HHO' THEN 'HO'
                    WHEN b.code = 'HHA' THEN 'HO Babel'
                    WHEN b.code = 'HHP' THEN 'HO Lampung'
                    WHEN b.code = 'MMT' THEN 'HO Lampung'
                    WHEN st.name ILIKE '%%Lampung%%' THEN 'Lampung'
                    WHEN st.name ILIKE '%%Bangka%%' OR st.name ILIKE '%%Belitung%%' THEN 'Babel'
                    ELSE 'IR'
                END AS "MASTER_AREA",
                b.code AS "MASTER_CABANG"
            FROM (
                    (
                        SELECT id,
                            debit - credit AS balance
                        FROM account_move_line
                        WHERE full_reconcile_id IS NULL
                            AND matching_number IS NULL
                            AND account_id IN (
                                SELECT id
                                FROM account_account
                                WHERE account_type = 'asset_receivable'
                            )
                    )
                    UNION
                    (
                        SELECT sub.id,
                            sub.balance
                        FROM (
                                SELECT MIN(id) AS id,
                                    matching_number,
                                    SUM(debit - credit) AS balance
                                FROM account_move_line
                                WHERE matching_number IS NOT NULL
                                    AND account_id IN (
                                        SELECT id
                                        FROM account_account
                                        WHERE account_type = 'asset_receivable'
                                    )
                                GROUP BY matching_number
                            ) AS sub
                    )
                ) AS A3
                INNER JOIN account_move_line aml ON aml.id = A3.id
                INNER JOIN account_account acc ON aml.account_id = acc.id
                LEFT JOIN res_company b ON aml.company_id = b.id
                LEFT JOIN res_partner bp ON b.partner_id = bp.id
                LEFT JOIN res_country_state st ON bp.state_id = st.id
                LEFT JOIN account_move m ON m.id = aml.move_id
                LEFT JOIN res_partner rp ON aml.partner_id = rp.id
                LEFT JOIN account_journal j ON j.id = aml.journal_id
            WHERE 1 = 1 
            AND A3.balance >= 1 %s
        """ % query_where
        
        return query


    def _calculate_risk_component(self, value, value_type):
        """Calculate risk component based on value and type"""
        if value_type == 'financial':
            if value <= 0:
                return '0'
            elif value <= 5000000:
                return '1'
            elif value <= 10000000:
                return '2'
            else:
                return '3'
        elif value_type == 'sla':
            if value <= 0:
                return '0'
            elif value <= 7:
                return '1'
            elif value <= 14:
                return '2'
            elif value <= 21:
                return '3'
            elif value <= 30:
                return '4'
            else:
                return '5'
        elif value_type == 'percentage':
            if value <= 0:
                return '0'
            elif value <= 10:
                return '1'
            elif value <= 20:
                return '2'
            elif value <= 30:
                return '3'
            elif value <= 40:
                return '4'
            else:
                return '5'
        return '0'

    def _prepare_summary_data(self, ress):
        """Process data into summary with risk calculation"""
        data = []
        
        grouper = itemgetter('CABANG', 'JENIS_AR')
        # Handle None values in sorting by providing default empty string
        sorted_res = sorted(ress, key=lambda x: (x.get('CABANG') or '', x.get('JENIS_AR') or ''))
        
        for key, records in groupby(sorted_res, grouper):
            records = list(records)
            
            residual = sum([rec.get('SISA_PIUTANG', 0) or 0 for rec in records])
            avg_sla = sum([rec.get('SLA', 0) or 0 for rec in records]) / len(records) if len(records) > 0 else 0
            avg_od = math.floor(sum([rec.get('SLA', 0) or 0 for rec in records if rec.get('OD_STATUS') == 'OD']) / len(records)) if len(records) > 0 else 0
            
            od_financial = 0 if avg_od <= 0 else sum([rec.get('SISA_PIUTANG', 0) or 0 for rec in records if rec.get('OD_STATUS') == 'OD'])
            od_sla = 0 if avg_od <= 0 else avg_od
            od_percentage = math.floor(od_financial / residual * 100) if residual > 0 else 0
            
            # Calculate risk components
            risk_financial = self._calculate_risk_component(od_financial, 'financial')
            risk_sla = self._calculate_risk_component(od_sla, 'sla')
            risk_percentage = self._calculate_risk_component(od_percentage, 'percentage')
            
            # Get risk from tw.calculator.risk
            code = risk_financial + risk_sla + risk_percentage
            risk = self.env['tw.calculator.risk'].search([('code', '=', code)], limit=1)
            risk_category = ''
            if risk:
                risk_category = dict(risk._fields['category'].selection).get(risk.category, '')
            
            data.append({
                'BRANCH': key[0],
                'JENIS_AR': key[1],
                'SISA_PIUTANG': residual,
                'AVG_SLA': round(avg_sla, 2),
                'OD_FINANCIAL': od_financial,
                'OD_SLA': od_sla,
                'OD_PERCENTAGE': od_percentage,
                'RISK_FINANCIAL': int(risk_financial),
                'RISK_SLA': int(risk_sla),
                'RISK_PERCENTAGE': int(risk_percentage),
                'RISK_CODE': code,
                'RISK_CATEGORY': risk_category,
            })
        
        return data

    def action_print_report(self):
        """Main entry point for report generation"""
        self.ensure_one()
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        
        # Execute query
        query = self._get_detail_query()
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
        
        if not ress:
            raise Warning('Data tidak ada...')
        
        # Prepare summary data from SQL result directly
        summary_data = self._prepare_summary_data(ress)
        
        # Define header groups for Summary sheet with custom colors
        summary_header_groups = [
            {
                # Default columns (white background)
                'columns': [
                    {'key': 'BRANCH', 'label': 'Branch'},
                    {'key': 'JENIS_AR', 'label': 'Jenis AR'},
                    {'key': 'SISA_PIUTANG', 'label': 'Sum of Sisa Piutang'},
                    {'key': 'AVG_SLA', 'label': 'Avg of SLA'},
                ]
            },
            {
                # Overdue group (yellow background)
                'name': 'Overdue',
                'bg_color': '#FFFF00',
                'columns': [
                    {'key': 'OD_FINANCIAL', 'label': 'Financial', 'bg_color': '#FFFF00'},
                    {'key': 'OD_SLA', 'label': 'SLA', 'bg_color': '#FFFF00'},
                    {'key': 'OD_PERCENTAGE', 'label': '%', 'bg_color': '#FFFF00'},
                ]
            },
            {
                # Grading Resiko group (green background)
                'name': 'Grading Resiko',
                'bg_color': '#92D050',
                'columns': [
                    {'key': 'RISK_FINANCIAL', 'label': 'Financial', 'bg_color': '#92D050'},
                    {'key': 'RISK_SLA', 'label': 'SLA', 'bg_color': '#92D050'},
                    {'key': 'RISK_PERCENTAGE', 'label': '%', 'bg_color': '#92D050'},
                    {'key': 'RISK_CODE', 'label': 'Risk Value', 'bg_color': '#92D050'},
                    {'key': 'RISK_CATEGORY', 'label': 'Risk Category', 'bg_color': '#92D050'},
                ]
            },
        ]
        
        # Generate report with per-sheet header_groups
        return self.env['web.report'].generate_report(
            report_name='Report Branch Grading',
            data=ress,
            data_sheet={
                'Detail Grading Cabang': ress,
                'Summary Grading Cabang': {
                    'data': summary_data,
                    'header_groups': summary_header_groups,
                },
            },
            start_date=self.start_date,
            end_date=self.end_date,
            show_total_footer=True,
        )

    # 14: Private Methods
