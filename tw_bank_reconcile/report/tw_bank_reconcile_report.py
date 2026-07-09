# 1: imports of python lib
import calendar
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import base64
from io import BytesIO
import xlsxwriter

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib


class BankReconcileReport(models.TransientModel):
    _name = "tw.bank.reconcile.report"
    _description = 'Laporan Bank Reconcile'

    # 7: defaults methods
    def _get_default_branch(self):
        return self.env.company.id
    
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()
    
    def _get_default_datetime(self):
        return datetime.now()

    # 8: fields
    name = fields.Char('Filename', readonly=True)
    state_x = fields.Selection((
        ('choose', 'choose'),
        ('get', 'get')
    ), default='choose')
    options = fields.Selection([
        ('Outstanding', 'Outstanding')
    ], string='Options', default='Outstanding')
    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)
    data_x = fields.Binary('File', readonly=True)

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', default=_get_default_branch)
    account_id = fields.Many2one(
        comodel_name='account.account', 
        string='Account', 
        domain="[('account_type','in',('asset_cash', 'asset_current')), ('company_ids','=',company_id)]"
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal', 
        string='Journal', 
        domain="[('company_id','parent_of',company_id), ('type','=','bank')]"
    )

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_bank_reconcile_report_tree(self):
        form_view_id = self.env.ref('tw_bank_reconcile.tw_bank_reconcile_report_wizard_view').id
        return {
            'type': 'ir.actions.act_window',
            'name': 'Laporan Bank Reconcile',
            'path': 'laporan-bank-reconcile',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'tw.bank.reconcile.report',
            'views': [(form_view_id, 'form')],
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def action_export(self):
        self.ensure_one()
        if self.options == 'Outstanding':
            return self._print_export_account_outstanding()

    # 14: private methods
    def _get_workbook_formats(self, workbook):
        wbf = {}
        # Basic Formats
        wbf['company'] = workbook.add_format({'bold': 1, 'align': 'left', 'font_size': 10, 'num_format': 'dd-mm-yyyy'})
        wbf['header2'] = workbook.add_format({'font_size': 10, 'top': 2, 'right': 2})
        wbf['footer_border'] = workbook.add_format({'border': 2})

        # Header Formats
        wbf['bg_gl'] = workbook.add_format({'bg_color': '#21610B', 'font_color': '#FFFFFF', 'align': 'center', 'border': 2, 'font_size': 10})
        wbf['bg_rk'] = workbook.add_format({'bg_color': '#0000FF', 'font_color': '#FFFFFF', 'align': 'center', 'border': 2, 'font_size': 10})
        wbf['header'] = workbook.add_format({'bold': 1, 'align': 'center', 'top': 1, 'bottom': 1, 'font_size': 10})
        wbf['header_right'] = workbook.add_format({'bold': 1, 'align': 'center', 'top': 1, 'bottom': 1, 'right': 2, 'font_size': 10})
        wbf['header_right2'] = workbook.add_format({'bold': 1, 'align': 'center', 'right': 2})
        wbf['header_saldo'] = workbook.add_format({'bold': 1, 'align': 'left', 'font_color': '#0080ff', 'font_size': 10})
        wbf['header_saldo_right'] = workbook.add_format({'bold': 1, 'align': 'right', 'font_color': '#0080ff', 'num_format': '#,##0.00', 'right': 2, 'font_size': 10})

        # Content Formats
        wbf['content'] = workbook.add_format({'align': 'left', 'font_size': 10})
        wbf['content_date'] = workbook.add_format({'align': 'center', 'num_format': 'yyyy-mm-dd', 'font_size': 10})
        wbf['content_float'] = workbook.add_format({'align': 'right', 'num_format': '#,##0.00', 'right': 2, 'font_size': 10})
        
        # New Content Formats (Blue)
        wbf['content_new'] = workbook.add_format({'align': 'left', 'font_color': '#2E9AFE', 'font_size': 10})
        wbf['content_date_new'] = workbook.add_format({'align': 'center', 'num_format': 'yyyy-mm-dd', 'font_color': '#2E9AFE', 'font_size': 10})
        wbf['content_float_new'] = workbook.add_format({'align': 'right', 'num_format': '#,##0.00', 'font_color': '#2E9AFE', 'right': 2, 'font_size': 10})
        
        # Footer Formats
        wbf['footer1'] = workbook.add_format({'font_color': '#B45F04', 'font_size': 10, 'bottom': 2})
        wbf['footer1_right'] = workbook.add_format({'font_color': '#B45F04', 'align': 'right', 'num_format': '#,##0.00', 'bottom': 2, 'right': 2, 'font_size': 10})

        return wbf

    def _prepare_outstanding_data(self):
        """Gather all necessary data using optimized SQL queries."""
        self.ensure_one()
        cr = self.env.cr
        account_id = self.account_id.id
        periode = self.end_date

        # 1. Saldo Sebelum Reconcile
        cr.execute("""
            SELECT COALESCE(SUM(debit - credit), 0) AS saldo
            FROM account_move_line
            WHERE date <= %s AND account_id = %s
        """, (periode, account_id))
        saldo_sb_rec = cr.fetchone()[0]

        # 2. Saldo Rekening Koran
        cr.execute("""
            SELECT COALESCE(SUM(credit - debit), 0) AS saldo
            FROM tw_bank_mutasi
            WHERE (date <= %s OR date IS NULL) AND account_id = %s
        """, (periode, account_id))
        saldo_rk = cr.fetchone()[0]

        # 3. Data Account Move Line (AML)
        cr.execute("""
            SELECT 
                date::VARCHAR as date, 
                COALESCE(ref, '') as ref, 
                COALESCE(name, '') as name, 
                (credit - debit) as amount
            FROM account_move_line
            WHERE (effective_date_reconcile > %s OR effective_date_reconcile IS NULL)
            AND account_id = %s
            ORDER BY date ASC
        """, (periode, account_id))
        aml_results = cr.dictfetchall()

        # 4. Data Bank Mutasi (BM)
        cr.execute("""
            SELECT 
                date::VARCHAR as date, 
                COALESCE(name, '') as name, 
                COALESCE(no_sistem, '') as no_sistem, 
                COALESCE(remark, '') as remark, 
                (credit - debit) as amount
            FROM tw_bank_mutasi
            WHERE (effective_date_reconcile > %s OR effective_date_reconcile IS NULL)
            AND account_id = %s
            ORDER BY date ASC
        """, (periode, account_id))
        bm_results = cr.dictfetchall()

        # Prepare metadata
        account_sap = self.account_id.sap or ''
        return {
            'code_branch': self.company_id.code,
            'name_branch': self.company_id.name,
            'profit_branch': self.company_id.profit_centre,
            'periode': periode,
            'account_code': self.account_id.code,
            'account_name': self.account_id.name,
            'account_sap': account_sap[0:6],
            'account_sap_code': account_sap[-3:],
            'saldo_sb_rec': saldo_sb_rec,
            'saldo_rk': saldo_rk,
            'aml_results': aml_results,
            'bm_results': bm_results,
            'company_name': self.company_id.sudo().parent_id.name or self.env.company.name,
            'user_name': self.env.user.name,
            'date_now': datetime.now(),
        }

    def _write_outstanding_report(self, worksheet, wbf, data):
        """Write the data to the worksheet."""
        # Columns Width
        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 22)
        worksheet.set_column('C:C', 54)
        worksheet.set_column('D:D', 24)
        worksheet.set_column('E:E', 24)
        worksheet.set_column('F:F', 17)
        worksheet.set_column('G:G', 24)
        worksheet.set_column('H:H', 21)
        worksheet.set_column('I:I', 24)

        # Header Info
        worksheet.write('A1', data['company_name'], wbf['company'])
        worksheet.write('A2', 'REKONSILIASI BANK', wbf['company'])
        worksheet.write('A4', 'CABANG', wbf['company'])
        worksheet.write('B4', f"[{data['code_branch']}] {data['name_branch']}", wbf['company'])
        worksheet.write('A5', 'PERIODE', wbf['company'])
        worksheet.write('B5', data['periode'], wbf['company'])
        worksheet.write('A6', 'ACCOUNT', wbf['company'])
        worksheet.write('B6', data['account_code'], wbf['company'])
        worksheet.write('C6', f"{data['account_sap']}-{data['profit_branch']}-{data['account_sap_code']}", wbf['company'])
        worksheet.write('A7', 'Description', wbf['company'])
        worksheet.write('B7', data['account_name'], wbf['company'])

        row = 9
        # Table Headers
        worksheet.merge_range('A%s:E%s' % (row, row), 'SALDO GL TEDS', wbf['bg_gl'])
        worksheet.merge_range('F%s:I%s' % (row, row), 'SALDO REKENING KORAN', wbf['bg_rk'])
        row += 1
        
        worksheet.write('A%s' % row, 'Tanggal', wbf['header'])
        worksheet.write('B%s' % row, 'No. Sistem', wbf['header'])
        worksheet.write('C%s' % row, 'Keterangan', wbf['header'])
        worksheet.write('D%s' % row, 'No. Bank Mutasi', wbf['header'])
        worksheet.write('E%s' % row, 'Jumlah', wbf['header_right'])
        worksheet.write('F%s' % row, 'Tanggal', wbf['header'])
        worksheet.write('G%s' % row, 'No. Sistem', wbf['header'])
        worksheet.write('H%s' % row, 'Keterangan', wbf['header'])
        worksheet.write('I%s' % row, 'Jumlah', wbf['header_right'])
        row += 1

        # Border for column E and I
        worksheet.write('E%s' % row, '', wbf['header_right2'])
        worksheet.write('I%s' % row, '', wbf['header_right2'])
        row += 1

        # Opening Saldo
        worksheet.write('C%s' % row, 'Saldo Sebelum Reconcile ', wbf['header_saldo'])
        worksheet.write('E%s' % row, data['saldo_sb_rec'], wbf['header_saldo_right'])
        worksheet.write('G%s' % row, 'Saldo Rekening Koran ', wbf['header_saldo'])
        worksheet.write('I%s' % row, data['saldo_rk'], wbf['header_saldo_right'])
        row += 1

        # Borders after opening saldo
        worksheet.write('E%s' % row, '', wbf['header_right2'])
        worksheet.write('I%s' % row, '', wbf['header_right2'])
        row += 1
        
        row_start_data = row
        total_kiri = data['saldo_sb_rec']
        total_kanan = data['saldo_rk']

        # 1. Bank Mutasi Positive
        for res in data['bm_results']:
            if res['amount'] >= 0:
                dt = datetime.strptime(res['date'], '%Y-%m-%d').date() if res['date'] else ''
                worksheet.write('A%s' % row, dt, wbf['content_date'])
                worksheet.write('B%s' % row, res['no_sistem'], wbf['content'])
                worksheet.write('C%s' % row, res['remark'], wbf['content'])
                worksheet.write('D%s' % row, res['name'], wbf['content'])
                worksheet.write('E%s' % row, res['amount'], wbf['content_float'])
                worksheet.write('I%s' % row, '', wbf['content_float'])
                row += 1
        
        # Border between sections
        worksheet.write('E%s' % row, '', wbf['header_right2'])
        worksheet.write('I%s' % row, '', wbf['header_right2'])
        row += 1

        # 2. AML Positive
        for res in data['aml_results']:
            if res['amount'] >= 0:
                total_kiri += res['amount']
                dt = datetime.strptime(res['date'], '%Y-%m-%d').date() if res['date'] else ''
                worksheet.write('A%s' % row, dt, wbf['content_date_new'])
                worksheet.write('B%s' % row, res['ref'], wbf['content_new'])
                worksheet.write('C%s' % row, res['name'], wbf['content_new'])
                worksheet.write('D%s' % row, '', wbf['content_new'])
                worksheet.write('E%s' % row, res['amount'], wbf['content_float_new'])
                worksheet.write('I%s' % row, '', wbf['content_float'])
                row += 1

        # Border between sections
        worksheet.write('E%s' % row, '', wbf['header_right2'])
        worksheet.write('I%s' % row, '', wbf['header_right2'])
        row += 1

        # 3. Bank Mutasi Negative
        for res in data['bm_results']:
            if res['amount'] < 0:
                dt = datetime.strptime(res['date'], '%Y-%m-%d').date() if res['date'] else ''
                worksheet.write('A%s' % row, dt, wbf['content_date'])
                worksheet.write('B%s' % row, res['no_sistem'], wbf['content'])
                worksheet.write('C%s' % row, res['remark'], wbf['content'])
                worksheet.write('D%s' % row, res['name'], wbf['content'])
                worksheet.write('E%s' % row, res['amount'], wbf['content_float'])
                worksheet.write('I%s' % row, '', wbf['content_float'])
                row += 1

        # Border between sections
        worksheet.write('E%s' % row, '', wbf['header_right2'])
        worksheet.write('I%s' % row, '', wbf['header_right2'])
        row += 1

        # 4. AML Negative
        for res in data['aml_results']:
            if res['amount'] < 0:
                total_kiri += res['amount']
                dt = datetime.strptime(res['date'], '%Y-%m-%d').date() if res['date'] else ''
                worksheet.write('A%s' % row, dt, wbf['content_date_new'])
                worksheet.write('B%s' % row, res['ref'], wbf['content_new'])
                worksheet.write('C%s' % row, res['name'], wbf['content_new'])
                worksheet.write('D%s' % row, '', wbf['content_new'])
                worksheet.write('E%s' % row, res['amount'], wbf['content_float_new'])
                worksheet.write('I%s' % row, '', wbf['content_float'])
                row += 1

        # Border before Pembulatan
        worksheet.write('E%s' % row, '', wbf['header_right2'])
        worksheet.write('I%s' % row, '', wbf['header_right2'])
        row += 1
        # Summary / Pembulat
        worksheet.write('C%s' % row, 'Pembulat ', wbf['header_saldo'])
        worksheet.write('E%s' % row, '', wbf['header_right2'])
        worksheet.write('I%s' % row, '', wbf['header_right2'])
        row += 1
        
        # Border before totals
        worksheet.write('E%s' % row, '', wbf['header_right2'])
        worksheet.write('I%s' % row, '', wbf['header_right2'])
        row += 1

        # Saldo Setelah Rekonsiliasi
        worksheet.write('B%s' % row, 'Saldo Setelah Rekonsiliasi ', wbf['header_saldo'])
        worksheet.write('G%s' % row, 'Saldo Setelah Rekonsiliasi ', wbf['header_saldo'])
        
        # Formulas
        formula_total_kiri = '{=subtotal(9,E%s:E%s)}' % (row_start_data, row - 1)
        formula_total_kanan = '{=subtotal(9,I%s:I%s)}' % (row_start_data, row - 1)
        
        worksheet.write_formula('E%s' % row, formula_total_kiri, wbf['header_saldo_right'], total_kiri)
        worksheet.write_formula('I%s' % row, formula_total_kanan, wbf['header_saldo_right'], total_kanan)
        row += 1

        # Selisih Section
        worksheet.write('A%s' % row, '', wbf['footer1'])
        worksheet.write('B%s' % row, '', wbf['footer1'])
        worksheet.write('C%s' % row, 'Selisih terhadap Rekening Koran / Listing ', wbf['footer1'])
        worksheet.write('D%s' % row, '', wbf['footer1'])
        worksheet.merge_range('F%s:I%s' % (row, row), '', wbf['footer1_right'])

        formula_selisih = f'=E{row-1}-I{row-1}'
        worksheet.write('E%s' % row, formula_selisih, wbf['footer1_right'])
        row += 2

        # Signatures
        worksheet.merge_range('A%s:I%s' % (row, row), '', wbf['header2'])
        row += 1
        worksheet.write('D%s' % row, 'Dipersiapkan Oleh,', wbf['content'])
        worksheet.write('E%s' % row, 'Di Periksa Oleh,', wbf['content'])
        worksheet.write('G%s' % row, 'Di Setujui Oleh,', wbf['content'])
        worksheet.write('I%s' % row, '', wbf['header_saldo_right'])
        row += 2
        worksheet.write('D%s' % row, 'Nama:', wbf['content'])
        worksheet.write('E%s' % row, 'Nama:', wbf['content'])
        worksheet.write('G%s' % row, 'Nama:', wbf['content'])
        worksheet.write('I%s' % row, '', wbf['header_saldo_right'])
        row += 1
        worksheet.write('D%s' % row, 'Tanggal:', wbf['content'])
        worksheet.write('E%s' % row, 'Tanggal:', wbf['content'])
        worksheet.write('G%s' % row, 'Tanggal:', wbf['content'])
        worksheet.write('I%s' % row, '', wbf['header_saldo_right'])
        row += 1
        worksheet.merge_range('A%s:I%s' % (row, row), '', wbf['footer1_right'])
        row += 2
        
        # Timestamp
        date_str = data['date_now'].strftime("%d-%m-%Y")
        worksheet.write('A%s' % row, f"{date_str} {data['user_name']}", wbf['content'])

        worksheet.freeze_panes(12, 2)

    def _print_export_account_outstanding(self):
        data = self._prepare_outstanding_data()
        
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        wbf = self._get_workbook_formats(workbook)
        worksheet = workbook.add_worksheet('Journal')
        
        self._write_outstanding_report(worksheet, wbf, data)
        
        workbook.close()
        out = base64.encodebytes(fp.getvalue())
        
        filename = f"Report Bank Reconcile {data['date_now'].strftime('%d-%m-%Y %H:%M:%S')}.xlsx"
        self.write({
            'data_x': out,
            'name': filename
        })
        fp.close()

        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': f'/web/content/tw.bank.reconcile.report/{self.id}/data_x/{filename}?download=true'
        }

    # 14: private methods