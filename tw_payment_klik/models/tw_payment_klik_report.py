import xlsxwriter
from io import BytesIO
import base64
import os
import tempfile
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
import calendar
import ast

class PaymentKlikReportWizard(models.TransientModel):
    _name = "tw.payment.klik.report.wizard"
    _description = "Report Payment Klik"

    wbf = {}
    
    @api.model
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    def _domain_journal_id(self):
        branches = self.env['res.company'].search([('branch_type_id.value','in',('MD','HO'))])
        return ['|',('company_id','in',[b.id for b in branches]),('company_id', '=', False)]

    def _get_default_company(self):
        return self.env.company.id

    name = fields.Char('Filename', readonly=True)
    report_type = fields.Selection([
        ('standard', 'Standard'),
        ('bank', 'Bank'),
    ], string='Report Type', default='standard')
    options = fields.Selection([
      ('All','All'),
      ('Supplier Payment','Supplier Payment'),
      ('Advance Payment','Advance Payment'),
      ('Settlement Advance Payment','Settlement Advance Payment'),
      ('Bank Transfer','Bank Transfer')], default='All')
    category = fields.Selection(string='Category', selection=[('new', 'New'), ('all', 'All'),],default='new')
    start_date = fields.Date('Start Date',default=_get_default_date)
    end_date = fields.Date('End Date',default=_get_default_date)
    division = fields.Selection(selection=lambda self: self.env['tw.selection'].get_division_options())
    file = fields.Binary('File')
    finance_email = fields.Char('Finance Email', compute='_compute_company_id', inverse="_inverse_finance_email")
    is_show_configuration = fields.Boolean('Show Configuration', default=False)

    bank_id = fields.Many2one('res.bank', string='Bank')
    user_id = fields.Many2one('res.users',string='Payment Klik by')
    company_id = fields.Many2one('res.company',string="Branch", default=_get_default_company)
    city_id = fields.Many2one(comodel_name='res.city',  string="Kabupaten", compute='_compute_company_id', inverse="_inverse_city_id")
    district_id = fields.Many2one(comodel_name='res.district',  string="Kecamatan", compute='_compute_company_id', inverse="_inverse_district_id")
    company_ids = fields.Many2many('res.company',string="Branch")
    journal_id = fields.Many2one('account.journal',string='Journal',domain=_domain_journal_id)

    @api.depends('company_id')
    def _compute_company_id(self):
        for record in self:
            record.city_id = record.company_id.city_id
            record.district_id = record.company_id.district_id
            record.finance_email = record.company_id.finance_email

    def _inverse_finance_email(self):
        for record in self:
            record.suspend_security().company_id.finance_email = record.finance_email

    def _inverse_city_id(self):
        for record in self:
            record.suspend_security().company_id.city_id = record.city_id

    def _inverse_district_id(self):
        for record in self:
            record.suspend_security().company_id.district_id = record.district_id

    def action_download(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        if self.report_type == 'bank':
            return self.action_download_report_bank()
        elif self.report_type == 'standard':
            return self.action_download_report_standard()
        else:
            raise Warning('Report Type not found')
    
    def action_download_report_standard(self):
        data = self.get_report_data()
        final_data = self.generate_final_data(data)
        return self.env['web.report'].sudo().generate_report('Report Payment Klik', final_data)
    
    def action_download_report_bank(self):
        if not self.city_id or not self.district_id or not self.finance_email:
            raise Warning("Finance Email, City dan District wajib terisi, silahkah lengkapi setting email dan alamat Company di Branch Setting")

        fp = BytesIO()
        date = datetime.now()
        date = date.strftime("%d%m%Y_%H%M%S")

        filename = 'Laporan_payment_klik_%s %s.xlsx'%(self.options,str(date))

        row_number=1
        if self.bank_id.code == 'BCA':
            workbook = xlsxwriter.Workbook(fp)        
            workbook = self.add_workbook_format(workbook)
            wbf=self.wbf
            
            worksheet_supplier_payment = workbook.add_worksheet('Data')
            worksheet_supplier_payment.set_column('A1:A1', 5)
            worksheet_supplier_payment.set_column('B1:B1', 23)
            worksheet_supplier_payment.set_column('C1:C1', 15)
            worksheet_supplier_payment.set_column('D1:D1', 20)
            worksheet_supplier_payment.set_column('E1:E1', 15)
            worksheet_supplier_payment.set_column('F1:F1', 20)
            worksheet_supplier_payment.set_column('G1:G1', 23)
            worksheet_supplier_payment.set_column('H1:H1', 23)
            worksheet_supplier_payment.set_column('I1:I1', 20)
            worksheet_supplier_payment.set_column('J1:J1', 20)
            worksheet_supplier_payment.set_column('K1:K1', 20)
            worksheet_supplier_payment.set_column('L1:L1', 20)
            worksheet_supplier_payment.set_column('M1:M1', 20)
            worksheet_supplier_payment.set_column('N1:N1', 20)
            worksheet_supplier_payment.set_column('O1:O1', 20)
            worksheet_supplier_payment.set_column('P1:P1', 20)
            worksheet_supplier_payment.set_column('Q1:Q1', 20)
            worksheet_supplier_payment.set_column('R1:R1', 20)
            worksheet_supplier_payment.set_column('S1:S1', 20)
            worksheet_supplier_payment.set_column('T1:T1', 20)
            worksheet_supplier_payment.set_column('U1:U1', 20)
            worksheet_supplier_payment.set_column('V1:V1', 20)
            
            worksheet_supplier_payment.write('A1', 'No', wbf['header'])
            worksheet_supplier_payment.write('B1', 'Transaction ID', wbf['header'])
            worksheet_supplier_payment.write('C1', 'Transfer Type', wbf['header'])
            worksheet_supplier_payment.write('D1', 'Debited Acc.', wbf['header'])
            worksheet_supplier_payment.write('E1', 'Beneficiary ID', wbf['header'])
            worksheet_supplier_payment.write('F1', 'Credited Acc.', wbf['header'])
            worksheet_supplier_payment.write('G1', 'Amount', wbf['header'])
            worksheet_supplier_payment.write('H1', 'Eff. Date', wbf['header'])
            worksheet_supplier_payment.write('I1', 'Transaction Purpose', wbf['header'])
            worksheet_supplier_payment.write('J1', 'Currency', wbf['header'])
            worksheet_supplier_payment.write('K1', 'Charges Type', wbf['header'])
            worksheet_supplier_payment.write('L1', 'Charges Acc.', wbf['header'])
            worksheet_supplier_payment.write('M1', 'Remark 1', wbf['header'])
            worksheet_supplier_payment.write('N1', 'Remark 2', wbf['header'])
            worksheet_supplier_payment.write('O1', 'Receiver Bank Cd', wbf['header'])
            worksheet_supplier_payment.write('P1', 'Receiver Bank Name', wbf['header'])
            worksheet_supplier_payment.write('Q1', 'Receiver Name', wbf['header'])
            worksheet_supplier_payment.write('R1', 'Receiver Cust. Type', wbf['header'])
            worksheet_supplier_payment.write('S1', 'Receiver Cust. Residen', wbf['header'])
            worksheet_supplier_payment.write('T1', 'Transaction Cd', wbf['header'])
            worksheet_supplier_payment.write('U1', 'Beneficiary Email', wbf['header'])
            worksheet_supplier_payment.write('V1', 'Partner Email', wbf['header'])
            
            row_number=2
        

        elif self.bank_id.code == 'BRI':
            filename = filename.replace('xlsx','csv')
        
        elif self.bank_id.code == 'MANDIRI':
            row_number=2
            filename = filename.replace('xlsx','csv')

        data = self.get_report_data()
        if data:
            line_ids = []
            if self.bank_id.code == 'BCA':
                no = 1
                for res in data:
                    line_ids.append(self.insert_report_payment_klik_line(res))
                    
                    name = res.get('name')
                    desc = res.get('description')
                    bank_tujuan = res.get('bank_tujuan_code')
                    bank_bic = res.get('bank_tujuan_bic')
                    transfer_type = 'LLG' if bank_tujuan != 'BCA' else 'BCA'
                    rek_asal = str(res.get('rek_asal').encode('ascii', 'ignore').decode('ascii')) if res.get('rek_asal') else ''
                    rek_tujuan = str(res.get('rek_tujuan').encode('ascii', 'ignore').decode('ascii')) if res.get('rek_tujuan') else ''
                    penerima = res.get('penerima')
                    amount = res.get('paid_amount')
                    email = res.get('email') if res.get('email') else ''
                    
                    if rek_asal and rek_tujuan.isdigit():
                        worksheet_supplier_payment.write('A%s' % row_number, str(no), wbf['content'])
                        worksheet_supplier_payment.write('B%s' % row_number, name.replace("/","") , wbf['content'])
                        worksheet_supplier_payment.write('C%s' % row_number, transfer_type , wbf['content'])
                        worksheet_supplier_payment.write('D%s' % row_number, rek_asal , wbf['content'])
                        worksheet_supplier_payment.write('E%s' % row_number, '', wbf['content'])
                        worksheet_supplier_payment.write('F%s' % row_number, rek_tujuan , wbf['content'])
                        worksheet_supplier_payment.write('G%s' % row_number, amount , wbf['content_float'])
                        worksheet_supplier_payment.write('H%s' % row_number, res.get('date') , wbf['content'])
                        worksheet_supplier_payment.write('I%s' % row_number, '' , wbf['content'])
                        worksheet_supplier_payment.write('J%s' % row_number, 'IDR' , wbf['content'])
                        worksheet_supplier_payment.write('K%s' % row_number, 'OUR' , wbf['content'])
                        worksheet_supplier_payment.write('L%s' % row_number, rek_asal , wbf['content'])
                        worksheet_supplier_payment.write('M%s' % row_number, desc , wbf['content'])
                        worksheet_supplier_payment.write('N%s' % row_number, name , wbf['content'])
                        worksheet_supplier_payment.write('O%s' % row_number, bank_bic , wbf['content'])
                        worksheet_supplier_payment.write('P%s' % row_number, 'Bank '+bank_tujuan , wbf['content'])
                        worksheet_supplier_payment.write('Q%s' % row_number, penerima , wbf['content'])
                        worksheet_supplier_payment.write('R%s' % row_number, '2' , wbf['content'])
                        worksheet_supplier_payment.write('S%s' % row_number, '1' , wbf['content'])
                        worksheet_supplier_payment.write('T%s' % row_number, '88' , wbf['content'])
                        worksheet_supplier_payment.write('U%s' % row_number, '' , wbf['content'])
                        worksheet_supplier_payment.write('V%s' % row_number, email , wbf['content'])
                        
                        row_number+=1
                        no += 1
                
                workbook.close()
                out=base64.encodebytes(fp.getvalue())

            elif self.bank_id.code == 'BRI':
                no = 1
                text = ''
                sorted_data = sorted(data, key=lambda x: x.get('paid_amount', 0), reverse=True)
                for res in sorted_data:
                    line_ids.append(self.insert_report_payment_klik_line(res))

                    email = str(res.get('email')) if res.get('email') else ''
                    bank_tujuan_transfer_code = res.get('bank_tujuan_transfer_code')
                    bank_code = res.get('bank_tujuan_code')
                    beneficial_category = 'E0' if res.get('supplier_type') == 'perusahaan' else 'A0'
                    rek_asal = str(res.get('rek_asal').encode('ascii', 'ignore').decode('ascii')) if res.get('rek_asal') else ''
                    rek_tujuan = str(res.get('rek_tujuan').encode('ascii', 'ignore').decode('ascii') if res.get('rek_tujuan') else '')
                    penerima = res.get('penerima') if res.get('penerima') else ''
                    kode_bank_tujuan_bri = self.check_kode_bank_bri(bank_tujuan_transfer_code) or '002'
                    amount = str(res.get('paid_amount')).replace('.0','')
                    text += str(no)+'|'+res.get('name')
                    text += '|IFT|ID|'+res.get('date_format')+'0000'
                    text += '|IDR|'+amount
                    text += '|'+res.get('name','') + ' ' + res.get('description','')
                    text += '||OUR'
                    text += '|'+rek_asal
                    text += '|'+self.company_id.name
                    text += '|'+self.district_id.name.upper()
                    text += ';'+self.city_id.state_id.name+'|ID'
                    text += '|'+rek_tujuan
                    text += '|'+penerima
                    text += '|'+self.city_id.state_id.name+'|ID|||||'+self.finance_email
                    text += '|'+beneficial_category
                    text += '|011'
                    text += '|'+kode_bank_tujuan_bri
                    text += '\r\n'

                    row_number+=1
                    no+=1
                
                out = base64.encodebytes(text.encode('utf-8'))

            elif self.bank_id.code in ('MANDIRI','MDR'):
                no = 1
                jumlah_bayar = 0
                text_content = ''
                for res in data:
                    
                    line_ids.append(self.insert_report_payment_klik_line(res))

                    email = str(res.get('email')) if res.get('email') else ''
                    transfer_type = 'OUR' 
                    imidiate_payment = '1'
                    
                    if 'MANDIRI' in res.get('bank_tujuan') or 'MATJKT' in res.get('bank_tujuan'):
                        transfer_type = ''
                    
                    no += 1

                    rek_asal = str(res.get('rek_asal').encode('ascii', 'ignore').decode('ascii')) if res.get('rek_asal') else ''
                    rek_tujuan = str(res.get('rek_tujuan').encode('ascii', 'ignore').decode('ascii')) if res.get('rek_tujuan') else ''
                    penerima = res.get('penerima') if res.get('penerima') else ''
                    amount = str(res.get('paid_amount')).replace('.0','')
                    text_content += rek_tujuan
                    text_content += ','+penerima.upper().strip()
                    text_content += ',,,,IDR,'+amount
                    text_content += ','+res.get('description','')
                    text_content += ','+res.get('name').replace("/","") 
                    text_content += ',IBU,,PT. BANK MANDIRI (PERSERO) TBK,,,,,Y,'+self.finance_email+',,,,Y,Y,,,,,,,,,,,,,,,,'
                    text_content += ','+transfer_type
                    text_content += ','+imidiate_payment
                    text_content += ','+email
                    text_content += ',,,,E' # +end_of_file
                    text_content += '\r\n'
                    jumlah_bayar += res.get('paid_amount')

                text_header = 'P'
                text_header += ','+res.get('date_format')
                text_header += ','+rek_asal
                text_header += ','+str(len(data))
                text_header += ','+str(jumlah_bayar)
                text_header += ',,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,\r\n'
                
                text = text_header + text_content
                out = base64.encodebytes(text.encode('utf-8'))
            else:
                raise Warning('Format hanya tersedia untuk bank dengan code BCA, BRI, dan MANDIRI')
        else:
            raise Warning("Tidak ada data")


        if self.category == 'new':
            self.env['tw.payment.klik'].suspend_security().create({
                'line_ids':line_ids
            })

        self.write({'file':out, 'name': filename})
        fp.close()
        return {
            'type': 'ir.actions.act_url',
            "target": "new",
            'url': '/web/content/tw.payment.klik.report.wizard/%s/file/%s?download=true' % (self.id, filename)
        }
    

    def get_report_data(self):
        query_where_bank = ""
        if self.bank_id:
            query_where_bank = " AND bank_asal.id = %d "%self.bank_id.id

        query_where = " "
        if self.company_ids:
            query_where += f" AND payment.company_id IN {str(tuple([b.id for b in self.company_ids])).replace(',)', ')')}"
        else:
            branch = self.env.user._get_company_ids()
            query_where += f" AND payment.company_id IN {str(tuple(branch)).replace(',)', ')')}"

        if self.start_date:
            query_where += " AND (payment.payment_klik_date + INTERVAL '7 hours')::date >= '%s'" %self.start_date
        if self.end_date:
            query_where += " AND (payment.payment_klik_date + INTERVAL '7 hours')::date <= '%s'" %self.end_date
        if self.division:
            query_where += " AND payment.division = '%s'" %self.division
        if self.journal_id:
            query_where += " AND payment.journal_id = %s" %self.journal_id.id
        if self.user_id:
            query_where += " AND payment.payment_klik_uid = %s" %self.user_id.id
        if self.category == 'new':
            query_where += " AND pkl.id is null"

        data = []
        if self.options in ('Supplier Payment','All'):
            query = """
                SELECT
                    COALESCE(payment.name,'') as name
                    , COALESCE(payment.memo,'') as memo
                    , payment.amount as paid_amount
                    , payment.journal_id as journal_id
                    , aj.name->>brp.lang as journal_name
                    , rek_asal.id as rek_asal_id
                    , rek_asal.acc_number as rek_asal
                    , COALESCE(payment.account_number,rek_tujuan.acc_number) as rek_tujuan
                    , rek_tujuan.id as rek_tujuan_id
                    , COALESCE(bank_tujuan.name,'') as bank_tujuan
                    , COALESCE(bank_tujuan.code,'') as bank_tujuan_code
                    , COALESCE(bank_tujuan.transfer_code,'') as bank_tujuan_transfer_code
                    , COALESCE(bank_tujuan.bic,'') as bank_tujuan_bic
                    , COALESCE(payment.account_holder, rek_tujuan.acc_holder_name) as penerima
                    , payment.transfer_note as payment_click_info
                    , to_char((payment.payment_klik_date + interval '7 hours')::date , 'DD-MM-YYYY') as date
                    , to_char((payment.payment_klik_date + interval '7 hours')::date , 'YYYYMMDD') as date_format
                    , to_char((now())::date , 'YYYYMMDD') as today_format
                    , to_char((now())::date , 'DD-MM-YYYY') as today
                    , 'tw.account.payment' as model_name
                    , payment.id as transaction_id
                    , payment.payment_klik_uid
                    , COALESCE(rpu.name,'') as payment_klik_by
                    , COALESCE(branch.code, '') as branch_code
                    , COALESCE(beneficiary_branch.name, '') as beneficiary_branch
                    , COALESCE(rp.name,'') as partner_name
                    , COALESCE(rp.email,'') as email
                    , rp.is_company
                FROM tw_account_payment payment
                    JOIN res_company branch ON branch.id = payment.company_id
                    JOIN res_company beneficiary_branch ON beneficiary_branch.id = payment.beneficiary_company_id
                    JOIN res_partner brp on brp.id = branch.partner_id
                    JOIN account_journal aj ON aj.id = payment.journal_id
                    JOIN res_partner rp ON rp.id = payment.partner_id
                    LEFT JOIN res_partner_bank as rek_asal ON rek_asal.id = aj.bank_account_id
                    LEFT JOIN res_bank as bank_asal ON bank_asal.id = rek_asal.bank_id
                    LEFT JOIN res_partner_bank as rek_tujuan ON rek_tujuan.id = payment.partner_bank_id
                    LEFT JOIN res_bank as bank_tujuan ON bank_tujuan.id = COALESCE(payment.bank_id,rek_tujuan.bank_id)
                    LEFT JOIN res_users ru ON ru.id = payment.payment_klik_uid
                    LEFT JOIN res_partner rpu ON rpu.id = ru.partner_id
                    LEFT JOIN tw_payment_klik_line as pkl ON pkl.transaction_id = payment.id AND pkl.model_name = 'tw.account.payment'
                WHERE 1=1 
                    AND payment.is_payment_klik = True  
                    AND aj.bank_account_id is not null
                    AND (payment.partner_bank_id is not null or payment.account_number is not null)
                    AND payment.type = 'supplier_payment' 
                    AND payment.state != 'cancel'
                    %s
                    %s
            """ % (query_where_bank,query_where)

            self.env.cr.execute(query)
            ress = self.env.cr.dictfetchall() 
            data += ress
        
        if self.options in ('Bank Transfer','All'):
            query = """
                SELECT
                    COALESCE(payment.name,'') as name
                    , payment.description as description
                    , payment.amount as paid_amount
                    , rek_asal.id as rek_asal_id
                    , rek_asal.acc_number as rek_asal
                    , COALESCE(payment.account_number,rek_tujuan.acc_number) as rek_tujuan
                    , rek_tujuan.id as rek_tujuan_id
                    , COALESCE(bank_tujuan.name,'') as bank_tujuan
                    , COALESCE(bank_tujuan.code,'') as bank_tujuan_code
                    , COALESCE(bank_tujuan.transfer_code,'') as bank_tujuan_transfer_code
                    , COALESCE(bank_tujuan.bic,'') as bank_tujuan_bic
                    , COALESCE(payment.account_holder, rek_tujuan.acc_holder_name) as penerima
                    , COALESCE(payment.transfer_note, rek_tujuan.acc_holder_name) as payment_click_info
                    , to_char((payment.payment_klik_date + interval '7 hours')::date , 'DD-MM-YYYY') as date
                    , to_char((payment.payment_klik_date + interval '7 hours')::date , 'YYYYMMDD') as date_format
                    , to_char((now())::date , 'YYYYMMDD') as today_format
                    , to_char((now())::date , 'DD-MM-YYYY') as today
                    , 'tw.bank.transfer' as model_name
                    , payment.id as transaction_id
                    , payment.payment_klik_uid
                    , COALESCE(rpu.name,'') as payment_klik_by
                    , COALESCE(branch.code, '') as branch_code
                    , COALESCE(beneficiary_branch.name, '') as beneficiary_branch
                    , COALESCE(rp.name,'') as partner_name
                    , COALESCE(rp.email,'') as email
                    , rp.is_company
                FROM tw_bank_transfer payment
                    JOIN (
                        SELECT
                        bank_transfer_id
                        , payment_to_id
                        , branch_destination_id
                        , description 
                        FROM tw_bank_transfer_line 
                        GROUP BY bank_transfer_id,branch_destination_id,payment_to_id,description 
                    ) btl ON payment.id = btl.bank_transfer_id
                    JOIN res_company branch ON branch.id = payment.company_id
                    JOIN res_company beneficiary_branch ON beneficiary_branch.id = btl.branch_destination_id
                    JOIN account_journal aj ON aj.id = payment.journal_id
                    JOIN res_partner rp ON rp.id = payment.partner_id
                    LEFT JOIN res_partner_bank as rek_asal ON rek_asal.id = aj.bank_account_id
                    LEFT JOIN res_bank as bank_asal ON bank_asal.id = rek_asal.bank_id
                    LEFT JOIN res_partner_bank as rek_tujuan ON rek_tujuan.id = payment.partner_bank_id
                    LEFT JOIN res_bank as bank_tujuan ON bank_tujuan.id = COALESCE(payment.bank_id,rek_tujuan.bank_id)		
                    LEFT JOIN res_users u ON u.id = payment.payment_klik_uid
                    LEFT JOIN res_partner rpu ON rpu.id = u.partner_id
                    LEFT JOIN tw_payment_klik_line as pkl on pkl.transaction_id = payment.id AND pkl.model_name = 'tw.bank.transfer'
                WHERE 1=1 
                    AND payment.is_payment_klik = True 
                    AND payment.state != 'cancel'
                    AND aj.bank_account_id is not null
                    AND (payment.partner_bank_id is not null or payment.account_number is not null)
                %s
                %s
            """ % (query_where_bank,query_where)
            self.env.cr.execute(query)
            ress = self.env.cr.dictfetchall() 
            data += ress
        
        if self.options in ('Advance Payment','All'):
            query = """
                SELECT
                    COALESCE(payment.name,'') as name
                    , COALESCE(payment.description,'') as memo
                    , payment.amount as paid_amount
                    , payment.journal_id as journal_id
                    , aj.name->>brp.lang as journal_name
                    , rek_asal.id as rek_asal_id
                    , rek_asal.acc_number as rek_asal
                    , COALESCE(rek_tujuan.acc_number,'') as rek_tujuan
                    , rek_tujuan.id as rek_tujuan_id
                    , COALESCE(bank_tujuan.name,'') as bank_tujuan
                    , COALESCE(bank_tujuan.code,'') as bank_tujuan_code
                    , COALESCE(bank_tujuan.transfer_code,'') as bank_tujuan_transfer_code
                    , COALESCE(bank_tujuan.bic,'') as bank_tujuan_bic
                    , COALESCE(rek_tujuan.acc_holder_name,'') as penerima
                    , COALESCE(rek_tujuan.acc_holder_name,'') as payment_click_info
                    , to_char((payment.payment_klik_date + interval '7 hours')::date , 'DD-MM-YYYY') as date
                    , to_char((payment.payment_klik_date + interval '7 hours')::date , 'YYYYMMDD') as date_format
                    , to_char((now())::date , 'YYYYMMDD') as today_format
                    , to_char((now())::date , 'DD-MM-YYYY') as today
                    , 'tw.advance.payment' as model_name
                    , payment.id as transaction_id
                    , payment.payment_klik_uid
                    , COALESCE(rpu.name,'') as payment_klik_by
                    , COALESCE(branch.code, '') as branch_code
                    , COALESCE(branch.name, '') as beneficiary_branch
                    , COALESCE(he.name,'') as partner_name
                    , COALESCE(he.work_email,'') as email
                    , 'perorangan' as supplier_type
                FROM tw_advance_payment payment
                    JOIN res_company branch ON branch.id = payment.company_id
                    JOIN res_partner brp on brp.id = branch.partner_id
                    JOIN account_journal aj ON aj.id = payment.journal_id
                    LEFT JOIN res_partner_bank as rek_asal ON rek_asal.id = aj.bank_account_id
                    LEFT JOIN res_bank as bank_asal ON bank_asal.id = rek_asal.bank_id
                    LEFT JOIN res_partner_bank as rek_tujuan ON rek_tujuan.id = payment.partner_bank_id
                    LEFT JOIN res_bank as bank_tujuan ON bank_tujuan.id = rek_tujuan.bank_id
                    LEFT JOIN hr_employee he ON he.id = payment.employee_id
                    LEFT JOIN res_users ru ON ru.id = payment.payment_klik_uid
                    LEFT JOIN res_partner rpu ON rpu.id = ru.partner_id
                    LEFT JOIN tw_payment_klik_line as pkl on pkl.transaction_id = payment.id AND pkl.model_name = 'tw.advance.payment'
                WHERE 1=1
                    AND payment.is_payment_klik = True
                    AND payment.partner_bank_id is not null
                    %s
                    %s
            """ % (query_where_bank,query_where)
            self.env.cr.execute(query)
            ress = self.env.cr.dictfetchall() 
            data += ress

        if self.options in ('Settlement Advance Payment','All'):
            query = """
                SELECT
                    COALESCE(payment.name,'') as name
                    , COALESCE(payment.description,'') as memo
                    , payment.amount_gap as paid_amount
                    , payment.journal_id as journal_id
                    , aj.name->>brp.lang as journal_name
                    , rek_asal.id as rek_asal_id
                    , rek_asal.acc_number as rek_asal
                    , COALESCE(rek_tujuan.acc_number,'') as rek_tujuan
                    , rek_tujuan.id as rek_tujuan_id
                    , COALESCE(bank_tujuan.name,'') as bank_tujuan
                    , COALESCE(bank_tujuan.code,'') as bank_tujuan_code
                    , COALESCE(bank_tujuan.transfer_code,'') as bank_tujuan_transfer_code
                    , COALESCE(bank_tujuan.bic,'') as bank_tujuan_bic
                    , COALESCE(rek_tujuan.acc_holder_name,'') as penerima
                    , COALESCE(rek_tujuan.acc_holder_name,'') as payment_click_info
                    , to_char((payment.payment_klik_date + interval '7 hours')::date , 'DD-MM-YYYY') as date
                    , to_char((payment.payment_klik_date + interval '7 hours')::date , 'YYYYMMDD') as date_format
                    , to_char((now())::date , 'YYYYMMDD') as today_format
                    , to_char((now())::date , 'DD-MM-YYYY') as today
                    , 'tw.settlement' as model_name
                    , payment.id as transaction_id
                    , payment.payment_klik_uid
                    , COALESCE(rpu.name,'') as payment_klik_by
                    , COALESCE(branch.code, '') as branch_code
                    , COALESCE(branch.name, '') as beneficiary_branch
                    , COALESCE(he.name,'') as partner_name
                    , COALESCE(payment.email,'') as email
                    , 'perorangan' as supplier_type
                FROM tw_settlement payment
                    JOIN tw_advance_payment as avp on avp.id = payment.account_avp_id
                    JOIN res_company branch ON branch.id = payment.company_id
                    JOIN res_partner brp on brp.id = branch.partner_id
                    JOIN account_journal aj ON aj.id = payment.journal_id
                    LEFT JOIN res_partner_bank as rek_asal ON rek_asal.id = aj.bank_account_id
                    LEFT JOIN res_bank as bank_asal ON bank_asal.id = rek_asal.bank_id
                    LEFT JOIN res_partner_bank as rek_tujuan ON rek_tujuan.id = avp.partner_bank_id
                    LEFT JOIN res_bank as bank_tujuan ON bank_tujuan.id = rek_tujuan.bank_id
                    LEFT JOIN hr_employee he ON he.id = payment.employee_id
                    LEFT JOIN res_users ru ON ru.id = payment.payment_klik_uid
                    LEFT JOIN res_partner rpu ON rpu.id = ru.partner_id
                    LEFT JOIN tw_payment_klik_line as pkl on pkl.transaction_id = payment.id AND pkl.model_name = 'tw.settlement'
                WHERE 1=1
                    AND payment.state != 'cancel'
                    AND payment.is_payment_klik = True
                    AND avp.partner_bank_id is not null
                    %s
                    %s
            """ % (query_where_bank,query_where)
            self.env.cr.execute(query)
            ress = self.env.cr.dictfetchall() 
            data += ress
        return data
    
    def generate_final_data(self,data):
        final_data = []
        for payment in data:
            final_data.append(
                {
                    'nama_partner':payment.get('partner_name'),
                    'email':payment.get('email'),
                    'cabang':payment.get('branch_code'),
                    'cabang_untuk':payment.get('beneficiary_branch'),
                    'number':payment.get('name'),
                    'payment_method':payment.get('journal_name'),
                    'amount_total':payment.get('paid_amount'),
                    'payment_klik_by':payment.get('payment_klik_by'),
                    'no_rekening_tujuan':payment.get('payment_click_info'),
                    'description':payment.get('description'),
                }
            )
        return final_data
    
    def insert_report_payment_klik_line(self,data):
        return [0,False,{
            'name': data.get('name'),
            'bank_id':self.bank_id.id,
            'model_name':data.get('model_name'),
            'transaction_id':data.get('transaction_id'),
            'paid_amount':data.get('paid_amount'),
            'payment_klik_uid':data.get('payment_klik_uid'),
            'rek_tujuan':data.get('rek_tujuan').encode('ascii', 'ignore').decode('ascii') if data.get('rek_tujuan') else '',
            'bank_tujuan':self.check_bank_tujuan(data.get('bank_tujuan')),
            'bank_account_id':data.get('bank_account_id'),
            'bank_account_dest_id':data.get('bank_account_dest_id'),
            'journal_id':data.get('journal_id'),
        }]
        
    def check_bank_tujuan(self,bank_tujuan):
        if 'MDR' in bank_tujuan:
            bank_tujuan = 'MANDIRI'
        return bank_tujuan

    def check_kode_bank_bri(self,code):
        bank_code_params = self.env['ir.config_parameter'].get_param('tw_payment_klik.bri_bank_code')
        mapping = ast.literal_eval((bank_code_params or '{}').strip())
        return mapping.get(code)
        
    def add_workbook_format(self, workbook):      
        self.wbf['header'] = workbook.add_format({'bold': 1,'align': 'center','bg_color': '#000000','font_color': '#FFFFFF'})
        self.wbf['header'].set_border()

        self.wbf['header_no'] = workbook.add_format({'bold': 1,'align': 'center','bg_color': '#FFFFDB','font_color': '#000000'})
        self.wbf['header_no'].set_border()
        self.wbf['header_no'].set_align('vcenter')
                
        self.wbf['footer'] = workbook.add_format({'align':'left'})
                    
        self.wbf['title_doc'] = workbook.add_format({'bold': 1,'align': 'left'})
        self.wbf['title_doc'].set_font_size(12)
        
        self.wbf['company'] = workbook.add_format({'align': 'left'})
        self.wbf['company'].set_font_size(11)
        
        self.wbf['content'] = workbook.add_format()
        self.wbf['content'].set_left()
        self.wbf['content'].set_right()
        
        self.wbf['content_float'] = workbook.add_format({'align': 'right','num_format': '#,##0.0'})
        self.wbf['content_float'].set_right() 
        self.wbf['content_float'].set_left()

        self.wbf['content_number'] = workbook.add_format({'align': 'center'})
        self.wbf['content_number'].set_right() 
        self.wbf['content_number'].set_left() 
        
        self.wbf['total'] = workbook.add_format({'bold':1,'bg_color': '#FFFFDB','align':'center'})
        self.wbf['total'].set_left()
        self.wbf['total'].set_right()
        self.wbf['total'].set_top()
        self.wbf['total'].set_bottom()
        
        self.wbf['merge'] = workbook.add_format({'valign': 'vcenter'})
        self.wbf['merge'].set_left()
        self.wbf['merge'].set_right()
        
        return workbook
    
