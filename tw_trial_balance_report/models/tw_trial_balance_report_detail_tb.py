# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import xlsxwriter
from io import BytesIO
from datetime import datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)


class TwTrialBalanceReportDetailTb(models.TransientModel):
    _inherit = "tw.trial.balance.report"

    def _print_excel_report_trial_balance(self,return_fp=False):
        """Generate Detail Trial Balance report with opening balance, mutation, and closing balance."""
        
        # Build company filter
        if self.company_ids:
            company_ids = tuple(self.company_ids.ids)
        else:
            company_ids = tuple(self.env.user._get_company_ids())
        
        # Build account filter
        account_filter = ""
        if self.account_ids:
            account_filter = f"AND a.id IN {tuple(self.account_ids.ids)}".replace(",)", ")")
        
        # Build status filter
        state_filter = ""
        if self.status == 'posted':
            state_filter = "AND m.state = 'posted'"
        
        # Build date filters - simplified since period_id is required
        start_date = self.start_date or self.period_id.date_from
        end_date = self.end_date or self.period_id.date_to
        
        # Optimized query using CTE for better performance
        query = f"""
            WITH move_lines AS (
                SELECT 
                    l.account_id,
                    l.company_id,
                    l.date,
                    l.debit,
                    l.credit
                FROM account_move_line l
                INNER JOIN account_move m ON m.id = l.move_id
                WHERE l.company_id IN {company_ids}
                    AND l.date <= '{end_date}'
                    {state_filter}
            ),
            saldo_awal AS (
                SELECT 
                    account_id,
                    company_id,
                    SUM(debit) as debit,
                    SUM(credit) as credit
                FROM move_lines
                WHERE date < '{start_date}'
                GROUP BY account_id, company_id
            ),
            mutasi AS (
                SELECT 
                    account_id,
                    company_id,
                    SUM(debit) as debit,
                    SUM(credit) as credit
                FROM move_lines
                WHERE date >= '{start_date}' AND date <= '{end_date}'
                GROUP BY account_id, company_id
            ),
            combined AS (
                SELECT 
                    COALESCE(s.account_id, m.account_id) as account_id,
                    COALESCE(s.company_id, m.company_id) as company_id,
                    COALESCE(s.debit, 0) as saldo_awal_debit,
                    COALESCE(s.credit, 0) as saldo_awal_credit,
                    COALESCE(m.debit, 0) as mutasi_debit,
                    COALESCE(m.credit, 0) as mutasi_credit
                FROM saldo_awal s
                FULL OUTER JOIN mutasi m ON s.account_id = m.account_id AND s.company_id = m.company_id
            )
            SELECT 
                COALESCE(a.code_store->>CAST(c.company_id AS VARCHAR), a.code_store->>'1') as account_code,
                a.name->>'en_US' as account_name,
                a.sap as account_sap,
                b.profit_centre,
                b.name as branch_name,
                b.code as branch_code,
                c.saldo_awal_debit,
                c.saldo_awal_credit,
                c.mutasi_debit,
                c.mutasi_credit,
                c.saldo_awal_debit - c.saldo_awal_credit as saldo_awal,
                c.saldo_awal_debit - c.saldo_awal_credit + c.mutasi_debit - c.mutasi_credit as saldo_akhir,
                COALESCE(LEFT(COALESCE(a.code_store->>CAST(c.company_id AS VARCHAR), a.code_store->>'1'), 6), '') 
                    || '-' || COALESCE(b.profit_centre, '') 
                    || COALESCE(RIGHT(a.sap, -6), '') as no_sun
            FROM combined c
            INNER JOIN account_account a ON a.id = c.account_id
            INNER JOIN res_company b ON b.id = c.company_id
            WHERE a.account_type IS NOT NULL
                {account_filter}
            ORDER BY b.code, COALESCE(a.code_store->>CAST(c.company_id AS VARCHAR), a.code_store->>'1')
        """
        
        self._cr.execute(query)
        all_lines = self._cr.dictfetchall()

        # Generate Excel
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf = self._add_workbook_format(workbook)
        worksheet = workbook.add_worksheet('Detail Trial Balance')

        # Set column widths
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 35)
        worksheet.set_column('F:F', 18)
        worksheet.set_column('G:G', 18)
        worksheet.set_column('H:H', 18)
        worksheet.set_column('I:I', 18)
        worksheet.set_column('J:J', 18)
        worksheet.set_column('K:K', 18)

        # Header
        company_name = self.env.user.company_id.name
        date_now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_name = self.env.user.name

        worksheet.write('A1', company_name, wbf['company'])
        worksheet.write('A2', 'Laporan Detail Trial Balance', wbf['title_doc'])
        worksheet.write('A3', f'Tanggal : {start_date} s/d {end_date}', wbf['company'])
        worksheet.write('A4', f'Periode : {self.period_id.name}', wbf['company'])

        # Column headers - Row 1 & 2 (merged for single headers)
        row = 6
        # Single headers - merge vertically
        worksheet.merge_range(row, 0, row + 1, 0, 'No', wbf['header'])
        worksheet.merge_range(row, 1, row + 1, 1, 'No Rek', wbf['header'])
        worksheet.merge_range(row, 2, row + 1, 2, 'Branch', wbf['header'])
        worksheet.merge_range(row, 3, row + 1, 3, 'No Sun', wbf['header'])
        worksheet.merge_range(row, 4, row + 1, 4, 'Keterangan', wbf['header'])
        # Multi-column headers - merge horizontally
        worksheet.merge_range(row, 5, row, 6, 'NERACA AWAL', wbf['header'])
        worksheet.merge_range(row, 7, row, 8, 'MUTASI', wbf['header'])
        worksheet.merge_range(row, 9, row, 10, 'NERACA SALDO', wbf['header'])

        # Column headers - Row 2 (sub-headers for Debit/Credit)
        row = 7
        worksheet.write(row, 5, 'Debit', wbf['header'])
        worksheet.write(row, 6, 'Credit', wbf['header'])
        worksheet.write(row, 7, 'Debit', wbf['header'])
        worksheet.write(row, 8, 'Credit', wbf['header'])
        worksheet.write(row, 9, 'Debit', wbf['header'])
        worksheet.write(row, 10, 'Credit', wbf['header'])

        # Data rows - starts right after header
        row = 8
        row_start = row
        no = 1

        total_saldo_awal_debit = 0
        total_saldo_awal_credit = 0
        total_mutasi_debit = 0
        total_mutasi_credit = 0
        total_neraca_debit = 0
        total_neraca_credit = 0

        for line in all_lines:
            saldo_awal = line.get('saldo_awal', 0) or 0
            saldo_akhir = line.get('saldo_akhir', 0) or 0
            
            saldo_awal_debit = saldo_awal if saldo_awal > 0 else 0
            saldo_awal_credit = -saldo_awal if saldo_awal < 0 else 0
            mutasi_debit = line.get('mutasi_debit', 0) or 0
            mutasi_credit = line.get('mutasi_credit', 0) or 0
            neraca_debit = saldo_akhir if saldo_akhir > 0 else 0
            neraca_credit = -saldo_akhir if saldo_akhir < 0 else 0

            no_sun = line.get('no_sun', '') or ''

            worksheet.write(row, 0, no, wbf['content_number'])
            worksheet.write(row, 1, line.get('account_code', ''), wbf['content'])
            worksheet.write(row, 2, line.get('branch_name', ''), wbf['content'])
            worksheet.write(row, 3, no_sun, wbf['content'])
            worksheet.write(row, 4, line.get('account_name', ''), wbf['content'])
            worksheet.write(row, 5, saldo_awal_debit, wbf['content_float'])
            worksheet.write(row, 6, saldo_awal_credit, wbf['content_float'])
            worksheet.write(row, 7, mutasi_debit, wbf['content_float'])
            worksheet.write(row, 8, mutasi_credit, wbf['content_float'])
            worksheet.write(row, 9, neraca_debit, wbf['content_float'])
            worksheet.write(row, 10, neraca_credit, wbf['content_float'])

            total_saldo_awal_debit += saldo_awal_debit
            total_saldo_awal_credit += saldo_awal_credit
            total_mutasi_debit += mutasi_debit
            total_mutasi_credit += mutasi_credit
            total_neraca_debit += neraca_debit
            total_neraca_credit += neraca_credit

            no += 1
            row += 1

        # Autofilter dan freeze
        worksheet.autofilter(7, 0, row - 1, 4)
        worksheet.freeze_panes(8, 3)

        # Totals
        worksheet.merge_range(row, 0, row, 4, 'Total', wbf['total'])
        worksheet.write_formula(row, 5, f'{{=SUBTOTAL(9,F{row_start + 1}:F{row})}}', wbf['total_float'], total_saldo_awal_debit)
        worksheet.write_formula(row, 6, f'{{=SUBTOTAL(9,G{row_start + 1}:G{row})}}', wbf['total_float'], total_saldo_awal_credit)
        worksheet.write_formula(row, 7, f'{{=SUBTOTAL(9,H{row_start + 1}:H{row})}}', wbf['total_float'], total_mutasi_debit)
        worksheet.write_formula(row, 8, f'{{=SUBTOTAL(9,I{row_start + 1}:I{row})}}', wbf['total_float'], total_mutasi_credit)
        worksheet.write_formula(row, 9, f'{{=SUBTOTAL(9,J{row_start + 1}:J{row})}}', wbf['total_float'], total_neraca_debit)
        worksheet.write_formula(row, 10, f'{{=SUBTOTAL(9,K{row_start + 1}:K{row})}}', wbf['total_float'], total_neraca_credit)

        # Footer
        worksheet.write(row + 2, 0, f'{date_now} {user_name}', wbf['footer'])

        workbook.close()

        # Return file pointer if return_fp is True
        if return_fp:
            return fp

        # Manual download - encode to base64 and return action
        import base64
        fp.seek(0)
        file_data = base64.b64encode(fp.read())
        
        attachment = self.env['ir.attachment'].create({
            'name': f'Detail_Trial_Balance_{start_date}_to_{end_date}.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

