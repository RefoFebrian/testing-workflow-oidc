# -*- coding: utf-8 -*-

# 1: imports of python lib
import base64
import re
import xlsxwriter
import calendar
from io import StringIO, BytesIO
from datetime import date, datetime, time, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwReportCash(models.TransientModel):
    _name = "tw.report.cash"
    _description = "TW Report Cash"

    # 7: defaults methods

    # 8: fields
    wbf = {}
    start_date = fields.Date('Start Date', required=True, default=fields.Date.context_today)
    end_date = fields.Date('End Date', required=True, default=fields.Date.context_today)
    option = fields.Selection([
        ('Petty Cash', 'Petty Cash'),
        ('All Non Petty Cash', 'All Non Petty Cash'),
        ('Cash', 'Cash'),
        ('Bank', 'Bank & Checks'),
        ('EDC', 'EDC'),
        ('Cash Reconcile', 'Cash Reconcile')
    ], string='Option', required=True)
    state = fields.Selection([
        ('outstanding', 'Outstanding'),
        ('reconcile', 'Reconciled')
    ], string='State')

    # 9: relation fields
    company_ids = fields.Many2many('res.company', string='Branch')
    journal_id = fields.Many2one('account.journal', string='Journal', domain="[('type', '=', 'petty_cash')]")
    journal_ids = fields.Many2many(
        'account.journal',
        'tw_report_cash_journal_rel',
        'tw_report_cash_id',
        'journal_id',
        string='Journals',
        required=True
    )

    # 10: constraints & sql constraints
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise Warning(_('End Date harus lebih besar dari Start Date.'))

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_generate_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        if self.option == 'Petty Cash':
            return self._generate_report_pattycash()
        elif self.option == 'Cash Reconcile':
            return self._generate_report_cash_reconcile()
        else:
            return self._generate_report_non_pettycash()

    def action_print_pdf_report(self):
        if self.option in ('Cash', 'Bank', 'EDC', 'All Non Petty Cash'):
            self._get_data_non_pettycash(check_empty=True)
            return self.env.ref('tw_report_cash.action_report_non_petty_cash').report_action(self)
        elif self.option == 'Petty Cash':
            return self.env.ref('tw_report_cash.action_report_petty_cash').report_action(self)
        else:
            raise Warning("PDF Report is not available for this option.")
    
    # 14: private methods
    def add_workbook_format(self, workbook):
        self.wbf['header'] = workbook.add_format({
            'bold': 1,
            'align': 'center',
            'bg_color': '#FFFFDB',
            'font_color': '#000000'
        })
        self.wbf['header'].set_border()

        self.wbf['header_no'] = workbook.add_format({
            'bold': 1,
            'align': 'center',
            'bg_color': '#FFFFDB',
            'font_color': '#000000'
        })
        self.wbf['header_no'].set_border()
        self.wbf['header_no'].set_align('vcenter')
                
        self.wbf['footer'] = workbook.add_format({'align': 'left'})
        self.wbf['footer_center'] = workbook.add_format({'align': 'center'})

        self.wbf['content_datetime'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
        self.wbf['content_datetime'].set_left()
        self.wbf['content_datetime'].set_right()
                
        self.wbf['content_date'] = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        self.wbf['content_date'].set_left()
        self.wbf['content_date'].set_right()
        
        self.wbf['title_doc'] = workbook.add_format({
            'bold': 1,
            'align': 'left'})
        self.wbf['title_doc'].set_font_size(12)
        
        self.wbf['company'] = workbook.add_format({'align': 'left'})
        self.wbf['company'].set_font_size(11)
        
        self.wbf['content'] = workbook.add_format()
        self.wbf['content'].set_left()
        self.wbf['content'].set_right()
        
        self.wbf['content_float'] = workbook.add_format({
            'align': 'right',
            'num_format': '#,##0.00'
        })
        self.wbf['content_float'].set_right()
        self.wbf['content_float'].set_left()

        self.wbf['content_center'] = workbook.add_format({'align': 'centre'})
        
        self.wbf['content_number'] = workbook.add_format({'align': 'right'})
        self.wbf['content_number'].set_right()
        self.wbf['content_number'].set_left()
                
        self.wbf['content_percent'] = workbook.add_format({
            'align': 'right',
            'num_format': '0.00%'
        })
        self.wbf['content_percent'].set_right()
        self.wbf['content_percent'].set_left()
                
        self.wbf['total_float'] = workbook.add_format({
            'bold': 1,
            'bg_color': '#FFFFDB',
            'align': 'right',
            'num_format': '#,##0.00'
        })
        self.wbf['total_float'].set_top()
        self.wbf['total_float'].set_bottom()
        self.wbf['total_float'].set_left()
        self.wbf['total_float'].set_right()
        
        self.wbf['total_number'] = workbook.add_format({
            'align': 'right',
            'bg_color': '#FFFFDB',
            'bold': 1
        })
        self.wbf['total_number'].set_top()
        self.wbf['total_number'].set_bottom()
        self.wbf['total_number'].set_left()
        self.wbf['total_number'].set_right()
        
        self.wbf['total'] = workbook.add_format({
            'bold': 1,
            'bg_color': '#FFFFDB',
            'align': 'center'
        })
        self.wbf['total'].set_left()
        self.wbf['total'].set_right()
        self.wbf['total'].set_top()
        self.wbf['total'].set_bottom()
        
        return workbook

    def _generate_report_pattycash(self):
        wbf = self.wbf
        data_res = self._get_data_pattycash()
        saldo_awal = data_res['saldo_awal']
        ress = data_res['ress']
        default_account_code = data_res['default_account_code']
        default_account_name = data_res['default_account_name']
        default_account_sap = data_res['default_account_sap']
        
        start_date = self.start_date
        end_date = self.end_date

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)
        workbook = self.add_workbook_format(workbook)
        worksheet = workbook.add_worksheet('Cash')
        worksheet.set_column('B1:B1', 13)
        worksheet.set_column('C1:C1', 10)
        worksheet.set_column('D1:D1', 20)
        worksheet.set_column('E1:E1', 25)
        worksheet.set_column('F1:F1', 29)
        worksheet.set_column('G1:G1', 20)
        worksheet.set_column('H1:H1', 20)
        worksheet.set_column('I1:I1', 20)
        worksheet.set_column('J1:J1', 20)
        worksheet.set_column('K1:K1', 20)
        worksheet.set_column('L1:L1', 20)
                        
        today = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        company_name = self.env.company.name
        user = self.env.user.name
        
        filename = f'report_petty_cash_{str(today)}.xlsx'
        worksheet.write('A1', company_name, wbf['company'])
        worksheet.write('A2', 'Laporan Buku Besar Harian Per Posting', wbf['title_doc'])
        
        worksheet.write('A4', 'Options : Petty Cash', wbf['company'])
        worksheet.write('A5', 'Tanggal : %s s/d %s' % (str(start_date) if start_date else '-', str(end_date) if end_date else '-'), wbf['company'])
        
        worksheet.write('A7', 'No.Rekening : %s - %s' % (str(default_account_code), str(default_account_name)), wbf['company'])
        worksheet.write('A8', 'No.Sun : %s' % (str(default_account_sap)), wbf['company'])
        
        worksheet.write('E7', 'Saldo Awal Tanggal :', wbf['company'])
        worksheet.write('E8', 'Mutasi Debit :', wbf['company'])
        worksheet.write('E9', 'Mutasi Credit :', wbf['company'])
        worksheet.write('E10', 'Saldo Akhir Tanggal:', wbf['company'])
        
        row = 11
        row += 1

        worksheet.write('A%s' % (row + 1), 'No', wbf['header'])
        worksheet.write('B%s' % (row + 1), 'Tgl Konf', wbf['header'])
        worksheet.write('C%s' % (row + 1), 'Status', wbf['header'])
        worksheet.write('D%s' % (row + 1), 'No Mutasi', wbf['header'])
        worksheet.write('E%s' % (row + 1), 'Partner', wbf['header'])
        worksheet.write('F%s' % (row + 1), 'Keterangan', wbf['header'])
        worksheet.write('G%s' % (row + 1), 'Debet', wbf['header'])
        worksheet.write('H%s' % (row + 1), 'Credit', wbf['header'])
        worksheet.write('I%s' % (row + 1), 'Saldo', wbf['header'])
        worksheet.write('J%s' % (row + 1), 'Posting', wbf['header'])
        worksheet.write('K%s' % (row + 1), 'Jam', wbf['header'])
        worksheet.write('L%s' % (row + 1), 'No PCR', wbf['header'])
           
        row += 2
        no = 1
        row1 = row
        
        total_debit = 0
        total_credit = 0
        total_saldo = saldo_awal
        
        for res in ress:
            debit = res.get('debit', 0)
            credit = res.get('credit', 0)
            saldo = debit - credit

            worksheet.write('A%s' % row, no, wbf['content_number'])
            worksheet.write('B%s' % row, res.get('date'), wbf['content_date'])
            worksheet.write('C%s' % row, res.get('state'), wbf['content'])
            worksheet.write('D%s' % row, res.get('move_line_name'), wbf['content'])
            worksheet.write('E%s' % row, res.get('partner_name'), wbf['content'])
            worksheet.write('F%s' % row, res.get('keterangan'), wbf['content'])
            worksheet.write('G%s' % row, res.get('debit'), wbf['content_float'])
            worksheet.write('H%s' % row, res.get('credit'), wbf['content_float'])
            if no == 1:
                worksheet.write_formula('I%s' % row, '=%s+(%s)' % (saldo_awal, saldo), wbf['content_float'])
            else:
                worksheet.write_formula('I%s' % row, '=I%s+(%d)' % (row - 1, saldo), wbf['content_float'])
            worksheet.write('J%s' % row, res.get('user_name'), wbf['content'])
            worksheet.write('K%s' % row, res.get('jam'), wbf['content'])
            worksheet.write('L%s' % row, res.get('name_reimbursed'), wbf['content'])
            
            no += 1
            row += 1
                
            total_debit += debit
            total_credit += credit
            total_saldo += saldo
        
        worksheet.autofilter('A13:L%s' % (row))
        worksheet.freeze_panes(13, 3)

        worksheet.write_number('F7', saldo_awal, wbf['content_float'])
        worksheet.write('F8', total_debit, wbf['content_float'])
        worksheet.write('F9', total_credit, wbf['content_float'])
        worksheet.write('F10', saldo_awal + total_debit - total_credit, wbf['content_float'])
        
        # TOTAL
        worksheet.merge_range('A%s:E%s' % (row, row), '', wbf['total'])
        worksheet.write('F%s' % (row), 'Total Per Tanggal', wbf['total'])
        worksheet.merge_range('I%s:L%s' % (row, row), '', wbf['total'])
        
        if row > row1:
            formula_total_debit = '{=subtotal(9,G%s:G%s)}' % (row1, row - 1)
            formula_total_credit = '{=subtotal(9,H%s:H%s)}' % (row1, row - 1)

            worksheet.write_formula(row - 1, 6, formula_total_debit, wbf['total_number'], total_debit)
            worksheet.write_formula(row - 1, 7, formula_total_credit, wbf['total_float'], total_credit)
        else:
            worksheet.write_number(row - 1, 6, total_debit, wbf['total_number'])
            worksheet.write_number(row - 1, 7, total_credit, wbf['total_float'])

        # Footer information
        worksheet.write(f'A{row + 3}', f'{today} {user}', wbf['footer'])
        
        # Signature blocks
        signatures = [
            ('OPERATOR', 'Bag.Komputer'),
            ('DIPERIKSA', 'Bag.Arsip'),
            ('DIPERIKSA2', 'Kep.Kasir'),
            ('DICEK ULANG', 'Petugas Kas'),
            ('DISETUJUI', 'Pimpinan'),
        ]
        # Define column ranges for 5 signature blocks across columns A-L
        sig_ranges = [('A', 'B'), ('C', 'D'), ('E', 'F'), ('G', 'I'), ('J', 'L')]
        
        for i, (title, dept) in enumerate(signatures):
            c_start, c_end = sig_ranges[i]
            # Write title, department, and signature placeholder
            worksheet.merge_range(f'{c_start}{row + 5}:{c_end}{row + 5}', title, wbf['footer_center'])
            worksheet.merge_range(f'{c_start}{row + 6}:{c_end}{row + 6}', dept, wbf['footer_center'])
            worksheet.merge_range(f'{c_start}{row + 10}:{c_end}{row + 10}', '(..................)', wbf['footer_center'])

        # Note section
        worksheet.write(f'A{row + 12}', 'NB:- harus ditandatangi kepala bagian masing-2,dan dicocokkan nilainya.', wbf['footer'])

        workbook.close()
        out = base64.encodebytes(fp.getvalue())
        report = self.env['web.report'].suspend_security().create({
            'report_file': out,
            'name': filename,
        })
        fp.close()
        
        return {
            'type': 'ir.actions.act_url',
            "target": "self",
            'url': '/web/content/web.report/%s/report_file/%s?download=true' % (report.id, filename)
        }
    
    def _generate_report_cash_reconcile(self):
        company_name = self.env.company.name
        filename = f'report_cash_reconcile_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

        branch_ids = self.company_ids.ids
        journal_ids = self.journal_ids.ids
        status = self.state
        start_date = self.start_date
        end_date = self.end_date

        status_str = ""
        query_select_br = " "
        query_from_br = " "
        query_order_br = " "

        query_where = " WHERE 1=1  "
        if status == 'outstanding':
            status_str = "Outstanding"
            query_select_br = " , '' as reconcile_code, '' as reconcile_date "
            query_where += " AND aml.bank_reconcile_id IS NULL "
        elif status == 'reconcile':
            status_str = "Reconciled"
            query_select_br = " , br.name as reconcile_code, (br.create_date + interval '7 hours')::timestamp::date as reconcile_date "
            query_from_br = " LEFT JOIN tw_bank_reconcile br on aml.bank_reconcile_id = br.id "
            query_order_br = " , br.create_date, br.name "
            if start_date:
                query_where += f" AND br.create_date >= '{start_date}' "
            if end_date:
                query_where += f" AND br.create_date <= '{end_date}' "

        if branch_ids:
            query_where += " AND aml.company_id in %s " % str(tuple(branch_ids)).replace(',)', ')')
        else:
            branch_ids = self.env.company.ids
            query_where += " AND aml.company_id in %s " % str(tuple(branch_ids)).replace(',)', ')')

        if journal_ids:
            journals = self.env['account.journal'].browse(journal_ids)
            query_where += " AND aml.account_id in %s " % str(tuple([x.default_debit_account_id.id for x in journals if x.type == 'cash'])).replace(',)', ')')
        else:
            journal_ids = self.env['account.journal'].suspend_security().search([
                ('company_id', 'in', branch_ids),
                ('type', '=', 'cash')
            ])

        query = f"""
            SELECT rc.code as branch_code
                , rc.name as branch_name
                , COALESCE(aa.code_store->>CAST(rc.id AS VARCHAR), aa.code_store->>CAST(rc.parent_id AS VARCHAR)) as account_code
                , aa.name->>'en_US' as account_name
                {query_select_br}
                , aml.ref as transaction_ref
                , aml.name as transaction_name
                , aml.date as transaction_date
                , aml.debit as debit
                , aml.credit as credit
                , aj.name->>'en_US' as journal_name
            FROM account_move_line aml
            {query_from_br}
            LEFT JOIN account_journal aj ON aj.id = aml.journal_id
            LEFT JOIN res_company rc ON rc.id = aml.company_id
            LEFT JOIN account_account aa ON aml.account_id = aa.id
            {query_where}
            ORDER BY rc.code, account_code, aml.id {query_order_br}
        """
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        branch_code_prev = False
        account_code_prev = False
        balance = 0
        new_ress = []
        for res in ress:
            branch_code = res.get('branch_code')
            account_code = res.get('account_code')
            restart_balance = False
            
            if (account_code_prev != account_code or branch_code_prev != branch_code):
                restart_balance = True

            if not account_code_prev or account_code_prev != account_code or branch_code_prev != branch_code:
                account_code_prev = account_code
                branch_code_prev = branch_code

            if restart_balance:
                balance = (res.get('debit', 0) - res.get('credit', 0))
            else:
                balance += (res.get('debit', 0) - res.get('credit', 0))
            
            row = {}
            for key, value in res.items():
                if key == 'journal_name':
                    row['balance'] = balance
                row[key] = value
            if 'balance' not in row:
                row['balance'] = balance
            new_ress.append(row)
        
        ress = new_ress
        
        if not ress:
            row_dummy = {
                'branch_code': '',
                'branch_name': '',
                'account_code': '',
                'account_name': '',
                'transaction_ref': '',
                'transaction_name': '',
                'transaction_date': '',
                'debit': '',
                'credit': '',
                'balance': '',
                'journal_name': '',
            }
            if status == 'reconcile':
                row_dummy['reconcile_code'] = ''
                row_dummy['reconcile_date'] = ''
            ress = [row_dummy]

        summary_header = {
            'A1': company_name,
            'A2': 'Report Cash Reconcile',
            'A3': f"Status : {status_str}"
        }
        if self.state == 'reconcile':
            summary_header['A4'] = f"Reconcile : {start_date} - {end_date}"

        return self.env['web.report'].sudo().generate_report(
            filename,
            ress,
            data_summary_header=summary_header,
            data_summary_header_col_size=False,
            return_fp=False,
            is_by_pass_generate=True
        )

    def _generate_report_non_pettycash(self):
        filename = f'report_cash_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        data_res = self._get_data_non_pettycash()

        summary_header = {
            'A1': self.env.company.name,
            'A2': 'LAPORAN PENERIMAAN DAN PENGELUARAN HARIAN',
            'A4': f"Options : {self.option}",
            'A5': f"Tanggal : {self.start_date} s/d {self.end_date if self.end_date else ''}"
        }

        return self.env['web.report'].sudo().generate_report(
            filename,
            data_res,
            data_summary_header=summary_header,
            data_summary_header_col_size=False,
            freeze_panes_column=3 if self.option == 'EDC' else 0,
            return_fp=False,
            is_by_pass_generate=True
        )

    def _get_data_non_pettycash(self, check_empty=False):
        branch_ids = self.company_ids.ids
        journal_ids = self.journal_ids
        status = self.state
        start_date = self.start_date
        end_date = self.end_date
        option = self.option
        
        journal_type = ['bank', 'cash', 'edc']
        if option == 'All Non Petty Cash':
            journal_type = ['bank', 'cash', 'edc']
        elif option == 'Cash':
            journal_type = ['cash']
        elif option == 'EDC':
            journal_type = ['edc']
        elif option == 'Bank':
            journal_type = ['bank']
        elif option == 'Petty Cash':
            journal_type = ['petty_cash']

        query_where = " WHERE 1=1 "
        if branch_ids:
            branch_ids = branch_ids + self.env.company.parent_id.ids
            query_where += " AND aml.company_id in %s " % str(tuple(branch_ids)).replace(',)', ')')
        else:
            branch_ids = self.env.company.ids + self.env.company.parent_id.ids
            query_where += " AND aml.company_id in %s " % str(tuple(branch_ids)).replace(',)', ')')

        if not journal_ids:
            journal_ids = self.env['account.journal'].suspend_security().search([
                ('company_id', 'in', branch_ids),
                ('type', 'in', journal_type)
            ])

        if option == 'EDC':
            digital_money_accounts = self.env['account.account'].suspend_security().search([
                ('name', 'ilike', 'digital money')
            ])
            if digital_money_accounts:
                digital_money_journals = self.env['account.journal'].suspend_security().search([
                    ('company_id', 'in', branch_ids),
                    ('type', '=', 'bank'),
                    ('default_debit_account_id', 'in', digital_money_accounts.ids)
                ])
                if digital_money_journals:
                    journal_ids |= digital_money_journals

        if journal_ids:
            query_where += " AND aml.journal_id in %s " % str(tuple(journal_ids.ids)).replace(',)', ')')
            account_ids = [x.default_debit_account_id.id for x in journal_ids if x.default_debit_account_id]
            if account_ids:
                query_where += " AND aml.account_id in %s " % str(tuple(account_ids)).replace(',)', ')')

        query_where_saldo = query_where

        if status == 'outstanding':
            query_where += " AND aml.full_reconcile_id IS NULL "
        elif status == 'reconcile':
            query_where += " AND aml.full_reconcile_id IS NOT NULL "

        if start_date:
            query_where_saldo += " AND aml.date < '%s' " % start_date
            query_where += " AND aml.date >= '%s' " % start_date
        if end_date:
            query_where += " AND aml.date <= '%s' " % end_date

        query_saldo_awal = f"""
            (SELECT 0 as id
                , '{start_date}'::date - interval '1 day' as tanggal
                , rc.code as branch_code
                , '11:59 PM' as jam
                , '' as kwitansi_name
                , COALESCE(aa.code_store->>CAST(rc.id AS VARCHAR), aa.code_store->>CAST(rc.parent_id AS VARCHAR)) as account_code
                , 'Saldo Awal' || ' ' || COALESCE(aa.code_store->>CAST(rc.id AS VARCHAR), aa.code_store->>CAST(rc.parent_id AS VARCHAR))::TEXT as keterangan
                , SUM(aml.debit - aml.credit) as balance
                , 'saldo_awal' as journal_type
                , '' as scr
                , '' as supplier_code
                , '' as supplier_name
                , '' as status
            FROM account_move_line aml
            LEFT JOIN account_account aa ON aa.id = aml.account_id
            LEFT JOIN res_company rc ON rc.id = aml.company_id
            {query_where_saldo}
            GROUP BY rc.code, account_code)
        """

        query_trx = f"""
            (SELECT DISTINCT ON (aml.id)
                aml.id as id
                , aml.date as tanggal
                , rc.code as branch_code
                , TO_CHAR(am.create_date + interval '7 hours', 'HH12:MI AM') as jam
                , rkl.name as kwitansi_name
                , COALESCE(aa.code_store->>CAST(rc.id AS VARCHAR), aa.code_store->>CAST(rc.parent_id AS VARCHAR)) as account_code
                , aml.name as keterangan
                , aml.debit - aml.credit as balance
                , aj.type as journal_type
                , am.name as scr
                , p.ref as supplier_code
                , p.name as supplier_name
                , am.state as status
            FROM account_move_line aml
            LEFT JOIN account_move am ON am.id = aml.move_id
            LEFT JOIN account_journal aj ON aj.id = aml.journal_id
            LEFT JOIN account_account aa ON aa.id = aml.account_id
            LEFT JOIN res_company rc ON rc.id = aml.company_id
            LEFT JOIN res_partner p ON p.id = aml.partner_id
            LEFT JOIN tw_account_payment tap ON tap.move_id = am.id
            LEFT JOIN tw_register_kwitansi_line rkl ON rkl.payment_id = tap.id
            {query_where}
            ORDER BY aml.id, rkl.id DESC NULLS LAST)
        """

        query = f"""
            SELECT * FROM (
                {query_saldo_awal}
                UNION ALL
                {query_trx}
            ) a
        """

        if check_empty:
            self.env.cr.execute(query + " LIMIT 1")
            if not self.env.cr.fetchone():
                raise Warning("Data tidak ditemukan")
            return True

        query += " ORDER BY branch_code, account_code, id "
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
        
        branch_code_prev = False
        account_code_prev = False
        balance = 0
        final_data = []

        for res in ress:
            branch_code = res.get('branch_code')
            account_code = res.get('account_code')

            if account_code_prev != account_code or branch_code_prev != branch_code:
                balance = 0

            account_code_prev = account_code
            branch_code_prev = branch_code

            val = res.get('balance', 0)
            balance += val
            res_type = res.get('journal_type')

            row = {
                'Kode Cabang': branch_code,
                'Tanggal': res.get('tanggal'),
                'Jam': res.get('jam'),
                'No Kwitansi': res.get('kwitansi_name'),
                'REK': account_code,
                'Keterangan': res.get('keterangan'),
                'Saldo Awal': val if res_type == 'saldo_awal' else 0.0,
                'Tunai': val if res_type == 'cash' else 0.0,
                'Bank & Checks': val if (res_type == 'bank' and option != 'EDC') else 0.0,
                'EDC': val if (res_type == 'edc' or (option == 'EDC' and res_type == 'bank')) else 0.0,
                'Total': balance,
                'SCR': res.get('scr'),
                'Supplier Code': res.get('supplier_code'),
                'Supplier Name': res.get('supplier_name'),
                'Status': res.get('status'),
            }
            final_data.append(row)
        
        if not final_data:
            final_data = [{
                'Kode Cabang': '',
                'Tanggal': '',
                'Jam': '',
                'No Kwitansi': '',
                'REK': '',
                'Keterangan': '',
                'Saldo Awal': '',
                'Tunai': '',
                'Bank & Checks': '',
                'EDC': '',
                'Total': '',
                'SCR': '',
                'Supplier Code': '',
                'Supplier Name': '',
                'Status': '',
            }]
        
        return final_data

    def _get_data_pattycash(self, check_empty=False):
        start_date = self.start_date
        end_date = self.end_date
        journal_id = self.journal_id
        company_ids = self.company_ids

        default_account = journal_id.default_debit_account_id or journal_id.default_credit_account_id
        default_account_code = default_account.code or ''
        default_account_name = default_account.name or ''
        default_account_sap = default_account.sap or ''
        
        query_where = " WHERE a.account_type = 'asset_cash' "
        query_saldo_where = ""
        if company_ids:
            query_where += " AND aml.company_id in %s " % str(tuple(company_ids.ids)).replace(',)', ')')
        else:
            company_ids = self.env.company.ids
            query_where += " AND aml.company_id in %s " % str(tuple(company_ids)).replace(',)', ')')

        if journal_id:
            journal_ids = journal_id
        else:
            journal_ids = self.env['account.journal'].suspend_security().search([
                ('company_id', 'in', company_ids.ids),
                ('type', '=', 'petty_cash')
            ])

        if journal_ids:
            query_where += " AND aml.account_id in %s " % str(tuple([x.default_debit_account_id.id for x in journal_ids if x.type == 'petty_cash'])).replace(',)', ')')
            query_saldo_where += " AND aml.account_id in %s " % str(tuple([x.default_debit_account_id.id for x in journal_ids if x.type == 'petty_cash'])).replace(',)', ')')

        if start_date:
            query_where += " AND aml.date >= '%s' " % start_date
        if end_date:
            query_where += " AND aml.date <= '%s' " % end_date

        query_saldo = f"""
            SELECT SUM(debit - credit) as balance
            FROM account_move_line aml
            WHERE date < '{start_date}'
            {query_saldo_where}
            GROUP BY account_id
        """
        self.env.cr.execute(query_saldo)
        result = self.env.cr.fetchall()
        saldo_awal = 0
        if len(result) > 0 and len(result[0]) > 0:
            saldo_awal += result[0][0]
                                                     
        query = f"""
            SELECT
                aml.date as date,
                am.state as state,
                am.name as move_line_name,
                p.name as partner_name,
                aml.name as keterangan,
                aml.debit as debit,
                aml.credit as credit,
                res.name as user_name,
                to_char(aml.create_date + interval '7 hours', 'HH12:MI AM') as jam,
                s.name as name_reimbursed
            FROM account_move_line aml
            LEFT JOIN account_move am ON am.id = aml.move_id
            LEFT JOIN account_account a ON a.id = aml.account_id
            LEFT JOIN account_journal aj ON aj.default_debit_account_id = aml.account_id
            LEFT JOIN res_partner p ON p.id = aml.partner_id
            LEFT JOIN res_company company ON company.id = aml.company_id
            LEFT JOIN res_users u ON u.id = aml.create_uid
            LEFT JOIN res_partner res ON res.id = u.partner_id
            LEFT JOIN tw_petty_cash_out m ON m.move_id = am.id
            LEFT JOIN tw_reimbursement_petty_cash s ON s.id = m.reimbursed_id
            {query_where}
        """

        if check_empty:
            self.env.cr.execute(f"SELECT 1 FROM ({query}) AS tmp LIMIT 1")
            if not self.env.cr.fetchone():
                raise Warning(_("Data tidak ditemukan"))
            return True
            
        query += " ORDER BY aml.id "
                    
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()

        for res in ress:
            date_value = res.get('date')
            res['date_display'] = date_value.strftime('%d-%m-%Y') if hasattr(date_value, 'strftime') else (date_value or '')

        return {
            'saldo_awal': saldo_awal,
            'ress': ress,
            'default_account_code': default_account_code,
            'default_account_name': default_account_name,
            'default_account_sap': default_account_sap,
        }
