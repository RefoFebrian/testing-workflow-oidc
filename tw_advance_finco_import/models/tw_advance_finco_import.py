# 1: imports of python lib
from datetime import date, datetime, timedelta
import base64
import xlrd
from io import BytesIO
import xlsxwriter
import os

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools.misc import formatLang, file_path as file_path_util

# 5: local imports

# 6: Import of unknown third party lib


class TwAdvanceFincoImport(models.TransientModel):
    _name = "tw.advance.finco.import"
    _description = 'Advance Finco (Import)'

    # 7: defaults methods
    def _get_default_datetime(self):
        return datetime.now()

    wbf = {}

    # 8: fields
    name = fields.Char(string='File Name')
    state_x = fields.Selection([
        ('choose', 'choose'),
        ('get', 'get')
    ], string='State', default='choose')
    division = fields.Selection(string='Division', selection=lambda self: self.env['tw.selection'].get_division_options())
    amount_unreconcile = fields.Float(string='Open Balance')
    file_import = fields.Binary(string='File Import')
    file_export = fields.Binary(string='File Export')

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', domain=[('parent_id','!=',False)])
    partner_id = fields.Many2one(comodel_name='res.partner', string='Finance Company', domain=[('category_id.name','=','Finance Company')])
    move_line_id = fields.Many2one(comodel_name='account.move.line', string='No HL', domain="[('account_id.account_type','=','liability_payable'), ('credit','!=',0), ('full_reconcile_id','=',False), ('partner_id','=',partner_id), ('company_id','=',company_id)]")
    journal_id = fields.Many2one(comodel_name='account.journal', string='Journal', domain="[('type','in',('bank','cash','edc')), ('company_id','=',company_id)]")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('move_line_id')
    def _onchange_move_line_id(self):
        if self.move_line_id:
            self.amount_unreconcile = abs(self.move_line_id.amount_residual_currency)

    # 12: override methods

    # 13: action methods
    def action_advance_finco_import_tree(self):
        domain = []
        name = 'Advance Finco (Import)'
        path = 'advance-finco-import'
        form_view_id = self.env.ref('tw_advance_finco_import.tw_advance_finco_import_wizard_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tw.advance.finco.import',
            'domain': domain,
            'views': [(form_view_id, 'form')],
            'target': 'new',
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def add_workbook_format(self, workbook):
        self.wbf['header'] = workbook.add_format({'bold': 1, 'align': 'center', 'bg_color': '#E67E22', 'font_color': '#FFFFFF'})
        self.wbf['header'].set_border()
        self.wbf['header'].set_align('vcenter')
        self.wbf['header'].set_font_size(12)

        self.wbf['content'] = workbook.add_format()
        self.wbf['content'].set_left()
        self.wbf['content'].set_right()

        self.wbf['content_float'] = workbook.add_format({'align': 'right', 'num_format': '#,##0.00'})
        self.wbf['content_float'].set_right()
        self.wbf['content_float'].set_left()

        return workbook
    
    def action_download_format_file(self):
        """
            Download the Advance Finco upload template.
            Priority: tw.format.upload record → data/template_upload_advance_finco.xlsx
        """
        format_obj = self.env['tw.format.upload'].sudo().search([
            ('name','ilike','advance finco'),
            ('active','=',True),
        ], limit=1)
        if format_obj and format_obj.file_format_show and format_obj.filename_upload_format:
            return {
                'type': 'ir.actions.act_url',
                'name': 'adv_finco_template',
                'url': (
                    f'/web/content/tw.format.upload/{format_obj.id}'
                    f'/file_format_show/{format_obj.filename_upload_format}?download=true'
                ),
            }

        # Fallback: serve from module data/ folder
        filename = 'template_upload_advance_finco.xlsx'
        file_path = file_path_util(f'tw_advance_finco_import/data/{filename}')
        if not file_path or not os.path.exists(file_path):
            raise Warning('Format template belum tersedia. Silakan hubungi tim IT.')

        with open(file_path, 'rb') as f:
            file_content = base64.b64encode(f.read())

        # Create attachment
        attachment = self.env['ir.attachment'].sudo().create({
            'name': filename,
            'datas': file_content,
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}/{filename}?download=true',
            'target': 'self',
        }
    
    def action_import(self):
        lot_excel = {}
        data = base64.decodebytes(self.file_import)
        excel = xlrd.open_workbook(file_contents=data)
        sh = excel.sheet_by_index(0)
        
        for rx in range(1, sh.nrows):
            no_mesin = str([sh.cell(rx, ry).value for ry in range(sh.ncols)][5])
            chassis_no = str([sh.cell(rx, ry).value for ry in range(sh.ncols)][6])
            nilai = int([sh.cell(rx, ry).value for ry in range(sh.ncols)][2])

            if not lot_excel.get(no_mesin):
                lot_excel[no_mesin] = {
                    'nilai': nilai,
                    'chassis_no': chassis_no
                }

        # Excel
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)        
        workbook = self.add_workbook_format(workbook)
        wbf = self.wbf
        
        # ---------Sheet 1------------#
        worksheet1 = workbook.add_worksheet('Data Selisih Amount')
        worksheet1.set_column('A1:A1', 18)
        worksheet1.set_column('B1:B1', 20)
        worksheet1.set_column('C1:C1', 20)
        worksheet1.set_column('D1:D1', 20)
        worksheet1.set_column('E1:E1', 20)

        row_1 = 2
        worksheet1.write('A1', 'No Mesin' , wbf['header'])
        worksheet1.write('B1', 'No Sale Order' , wbf['header'])
        worksheet1.write('C1', 'Open Balance' , wbf['header'])
        worksheet1.write('D1', 'Pencairan FIF' , wbf['header'])
        worksheet1.write('E1', 'Selisih' , wbf['header'])

        # ---------Sheet 2------------#        
        worksheet2 = workbook.add_worksheet('Data Not Found')
        worksheet2.set_column('A1:A1', 18)
        worksheet2.set_column('B1:B1', 20)
        worksheet2.set_column('C1:C1', 25)

        row_2 = 2
        worksheet2.write('A1', 'No Mesin' , wbf['header'])
        worksheet2.write('B1', 'No Chassis' , wbf['header'])
        worksheet2.write('C1', 'Customer' , wbf['header'])
        
        # ---------Sheet 3------------#
        worksheet3 = workbook.add_worksheet('Data Customer Payment')
        worksheet3.set_column('A1:A1', 23)
        worksheet3.set_column('B1:B1', 13)
        worksheet3.set_column('C1:C1', 20)
        worksheet3.set_column('D1:D1', 19)
        worksheet3.set_column('E1:E1', 19)
        worksheet3.set_column('F1:F1', 16)
        
        row_3 = 2
        worksheet3.write('A1', 'Customer Payment' , wbf['header'])
        worksheet3.write('B1', 'Code Cabang' , wbf['header'])
        worksheet3.write('C1', 'Nama Cabang' , wbf['header'])
        worksheet3.write('D1', 'No SL' , wbf['header'])
        worksheet3.write('E1', 'No SO' , wbf['header'])
        worksheet3.write('F1', 'Alokasi' , wbf['header'])

        query = f"""
            SELECT
                dso.company_id
                , branch.code AS code_cabang
                , branch.name AS nama_cabang
                , lot.name AS no_mesin
                , aml.id AS aml_id
                , aml.account_id
                , aml.debit
                , aml.date AS aml_date
                , aml.date_maturity
                , dso.name AS no_so
                , am.name AS no_sl
            FROM stock_lot lot
                JOIN tw_dealer_sale_order_line tdsol ON tdsol.lot_id = lot.id
                JOIN tw_dealer_sale_order dso ON tdsol.order_id = dso.id
                JOIN res_company branch ON dso.company_id = branch.id
                JOIN tw_branch_setting AS tbs ON branch.branch_setting_id = tbs.id
                JOIN tw_account_setting AS tas ON tbs.account_setting_id = tas.id
                JOIN tw_dealer_sale_order_line_invoice_rel tdsolir ON tdsolir.order_line_id = tdsol.id
                JOIN account_move_line invl ON tdsolir.invoice_line_id = invl.id AND invl.product_id = tdsol.product_id 
                JOIN account_move am ON invl.move_id = am.id AND tas.journal_dso_settlement_id = am.journal_id 
                JOIN account_move_line aml ON aml.move_id = am.id AND aml.display_type ='payment_term'
                JOIN account_account aa ON aml.account_id = aa.id
            WHERE 1=1
            AND aml.partner_id = {self.partner_id.id}
            AND aml.full_reconcile_id IS NULL
            AND lot.name IN {str(tuple(lot_excel.keys())).replace(',)', ')')}
            ORDER BY am.name ASC
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()

        lot_sl = []
        branches = {}
        paid_amount = 0
        for res in ress:
            no_mesin = res.get('no_mesin') 
            if no_mesin not in lot_sl:
                lot_sl.append(no_mesin)
            
            aml_id = res.get('aml_id')
            aml_obj = self.env['account.move.line'].sudo().browse(aml_id)

            company_id = res.get('company_id')
            account_id = res.get('account_id')
            debit = aml_obj.amount_residual_currency
            aml_date = res.get('aml_date')
            date_maturity = res.get('date_maturity')
            no_so = res.get('no_so')
            no_sl = res.get('no_sl')
            code_cabang = res.get('code_cabang')
            nama_cabang = res.get('nama_cabang')

            nilai_lot = lot_excel.get(no_mesin).get('nilai', 0)
            selisih = (debit - nilai_lot) * -1
            alokasi = debit
            reconcile = True
            if nilai_lot > debit:
                alokasi = debit
                reconcile = True

                worksheet1.write(f'A{row_1}', no_mesin, wbf['content'])
                worksheet1.write(f'B{row_1}', no_so, wbf['content'])
                worksheet1.write(f'C{row_1}', debit, wbf['content_float'])
                worksheet1.write(f'D{row_1}', nilai_lot, wbf['content_float'])
                worksheet1.write(f'E{row_1}', selisih, wbf['content_float'])
                row_1 += 1
                
            elif nilai_lot < debit:
                reconcile = False
                alokasi = nilai_lot

                worksheet1.write(f'A{row_1}', no_mesin, wbf['content'])
                worksheet1.write(f'B{row_1}', no_so, wbf['content'])
                worksheet1.write(f'C{row_1}', debit, wbf['content_float'])
                worksheet1.write(f'D{row_1}', nilai_lot, wbf['content_float'])
                worksheet1.write(f'E{row_1}', selisih, wbf['content_float'])
                row_1 += 1

            if not branches.get(company_id):
                branches[company_id] = {
                    'line_cr_ids': [
                        [0, False, {
                                'name': no_so,
                                'type': 'cr',
                                'reconciled': reconcile,
                                'move_line_id': aml_id,
                                'account_id': account_id,
                                'amount_original': debit,
                                'amount_unreconciled': debit,
                                'date_original': aml_date,
                                'date_due': date_maturity,
                                'amount': alokasi
                            }
                        ]
                    ],
                    'amount_reconcile': alokasi,
                    'code_cabang': code_cabang,
                    'nama_cabang': nama_cabang,
                    'row': row_3
                }
            else:
                branches[company_id]['line_cr_ids'].append([0, False, {
                    'name': no_so,
                    'type': 'cr',    
                    'reconciled': reconcile,
                    'move_line_id': aml_id,
                    'account_id': account_id,
                    'amount_original': debit,
                    'amount_unreconciled': debit,
                    'date_original': aml_date,
                    'date_due': date_maturity,
                    'amount': alokasi
                }])
                branches[company_id]['amount_reconcile'] += alokasi
                
            paid_amount += alokasi

            worksheet3.write(f'B{row_3}', '', wbf['content'])
            worksheet3.write(f'C{row_3}', '', wbf['content'])
            worksheet3.write(f'D{row_3}', no_sl, wbf['content'])
            worksheet3.write(f'E{row_3}', no_so, wbf['content'])
            worksheet3.write(f'F{row_3}', alokasi, wbf['content_float'])
            row_3 += 1

        if paid_amount > self.amount_unreconcile:
            raise Warning(f'Total Amount Pembayaran lebih besar dari Amount Balance !\nAmount Pembayaran {paid_amount}, Amount Balance {self.amount_unreconcile}')
        
        company_id = self.company_id.id
        currency_id = False
        if self.journal_id.currency_id:
            currency_id = self.journal_id.currency_id.id
        else:
            currency_id = self.journal_id.company_id.currency_id.id
        
        account_id = self.journal_id.default_credit_account_id.id or self.journal_id.default_debit_account_id.id

        lot_difrent = list(set(lot_excel) - set(lot_sl))
        for lot_d in lot_difrent:
            lot = self.env['stock.lot'].sudo().search([('name','=',lot_d)], limit=1)
            nama_customer = ''
            if lot.dealer_sale_order_id:
                dso = lot.dealer_sale_order_id
                nama_customer = dso.partner_id.name if dso.partner_id else ''

            chassis = lot_excel.get(lot_d).get('chassis_no')
            worksheet2.write(f'A{row_2}', lot_d, wbf['content'])
            worksheet2.write(f'B{row_2}', chassis, wbf['content'])
            worksheet2.write(f'C{row_2}', nama_customer, wbf['content'])
            row_2 += 1

        tgl = ((self._get_default_datetime() - timedelta(days=1)).date()).strftime('%d%m%y')
        for key, value in branches.items():
            memo = f"ADV DISBURSE {self.partner_id.code.upper()} {tgl} {value.get('code_cabang')}"
            vals_payment =  {
                'name': memo,
                'division': self.division,
                'beneficiary_company_id': key,
                'partner_type': 'finance_company',
                'partner_id': self.partner_id.id,
                'journal_id': self.journal_id.id,
                'company_id': company_id,
                'currency_id': currency_id,
                'account_id': account_id,
                'date': date.today(),
                'type': 'customer_payment',
                'payment_type': 'inbound',
                'line_cr_ids': value.get('line_cr_ids'),
                'line_dr_ids': [[0, False, {
                    'name': self.move_line_id.name,
                    'type': 'dr',            
                    'move_line_id': self.move_line_id.id,
                    'account_id': self.move_line_id.account_id.id,
                    'amount_original': self.move_line_id.amount_currency,
                    'amount_unreconciled': self.move_line_id.amount_residual_currency,
                    'date_original': self.move_line_id.date,
                    'date_due': self.move_line_id.date_maturity,
                    'amount': value.get('amount_reconcile')
                }]]
            }
            create_ar = self.env['tw.account.payment'].create(vals_payment)

            # AR Replace Disini
            worksheet3.write(f"A{value.get('row')}", create_ar.number, wbf['content'])
            worksheet3.write(f"B{value.get('row')}", value.get('code_cabang'), wbf['content'])
            worksheet3.write(f"C{value.get('row')}", value.get('nama_cabang'), wbf['content'])

        workbook.close()
        out = base64.encodebytes(fp.getvalue())
        datetime = (self._get_default_datetime() + timedelta(hours=7)).strftime('%d-%m-%Y %H:%M:%S')
        filename = f'Data Advance {datetime}.xlsx'
        self.write({
            'state_x': 'get',
            'file_export': out,
            'name': filename
        })
        fp.close()

        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': f'/web/content/tw.advance.finco.import/{self.id}/file_export/{filename}?download=true'
        }

    # 14: private methods