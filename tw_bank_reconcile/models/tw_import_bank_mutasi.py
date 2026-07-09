# 1: imports of python lib
from datetime import datetime, date
import base64
import xlrd
import csv
import os

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.tools.misc import formatLang, file_path as file_path_util
from odoo.tools import float_compare

# 5: local imports
import logging
_logger = logging.getLogger(__name__)

# 6: Import of unknown third party lib
def convert_to_time(value):
    if not value:
        return datetime.now().strftime('%H:%M:%S')
    elif isinstance(value, str):
        to_time = datetime.strptime(value, '%H:%M:%S')
        return to_time.strftime('%H:%M:%S')
    
def convert_to_date(value):
    if not value:
        return date.today().strftime('%Y-%m-%d')
    elif isinstance(value, (int, float)):
        seconds = (value - 25569) * 86400.0
        to_date = datetime.utcfromtimestamp(seconds)
        return to_date.strftime('%Y-%m-%d')
    elif isinstance(value, str):
        to_date = datetime.strptime(value, '%Y-%m-%d')
        return to_date.strftime('%Y-%m-%d')

def convert_to_number(value):
    if isinstance(value, (int, float)):
        return value
    elif isinstance(value, str):
        return float(value.replace(',',''))
    else:
        return 0
    
def convert_to_string(value):
    if isinstance(value, (float)):
        return str(int(value))
    elif not value:
        return ''
    return value

class ImportBankMutasi(models.TransientModel):
    _name = "tw.import.bank.mutasi"
    _description = 'Import Bank Mutasi'

    # 7: defaults methods
    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()
    
    def _get_default_branch(self):
        return self.env.user.company_ids[0].id if self.env.user.company_ids else False
    
    # 8: fields
    name = fields.Char(string='Name')
    remark = fields.Char(string='Remark')
    saldo_akhir = fields.Float(string='Saldo Akhir')
    format = fields.Selection([
        ('bca', 'BCA'),
        ('bri', 'BRI'),
        ('bni', 'BNI'),
        ('mandiri', 'Mandiri'),
        ('update', 'Update Bank Mutasi'),
        ('other', 'Other')
    ], string='Format')
    data_file = fields.Binary(string='File')

    # 9: relation fields
    company_id = fields.Many2one(comodel_name='res.company', string='Branch', default=_get_default_branch)
    account_id = fields.Many2one(comodel_name='account.account', string='Account')
    journal_id = fields.Many2one(comodel_name='account.journal', string='Journal', domain="[('company_id','parent_of',company_id), ('type','=','bank')]")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_import_bank_mutasi_tree(self, type='create'):
        context = {
            'search_default_fieldname': 1,
            'readonly_by_pass': 1
        }
        domain = []
        name = 'Import Bank Mutasi'
        path = 'import-bank-mutasi'
        if type == 'update':
            name = 'Import Bank Mutasi (Update)'
            path = 'import-bank-mutasi-update'
            context.update({'default_format': 'update'})
        form_view_id = self.env.ref('tw_bank_reconcile.tw_import_bank_mutasi_wizard_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'tw.import.bank.mutasi',
            'domain': domain,
            'views': [(form_view_id, 'form')],
            'context': context,
        }
    
    def get_saldo_akhir(self, account_id, date_max):
        total_debit = 0
        total_credit = 0
        saldo_akhir_mutasi = 0
        bank_mutasi_objs = self.env['tw.bank.mutasi'].search([
            ('account_id','=',account_id),
            ('date','=',date_max)
        ])
        if bank_mutasi_objs:
            for line in bank_mutasi_objs:
                total_credit += line.credit
                total_debit += line.debit
            saldo_akhir_mutasi = total_debit - total_credit

        return saldo_akhir_mutasi
    
    def get_saldo_akhir_all_date(self, account_id):
        query = f"""
            SELECT
                COALESCE(SUM(COALESCE(credit, 0)) - SUM(COALESCE(debit, 0)), 0) AS saldo
            FROM tw_bank_mutasi bm
            WHERE bm.account_id = {account_id}
        """
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchone()
        saldo = ress.get('saldo', 0)
        
        return saldo
        
    def check_file(self):
        var = []
        from_file = {}
        if self.format in ('bri', 'mandiri', 'other', 'update'):
            data = base64.decodebytes(self.data_file)
            excel = xlrd.open_workbook(file_contents=data)
            sh = excel.sheet_by_index(0)

        total_credit_file = 0
        total_debit_file = 0

        time = False
        name = False
        no_sistem = False
        tanggal = False
        teller = False
        saldo = False
        credit = False
        debit = False
        remark = False
        coa = False
        res_max = False
        date_max = False
        bank_obj = False
        total_saldo_from_excel = False

        if self.format == 'bri':
            coa_number = False
            for row in range(1, sh.nrows):
                if 'Account No' in sh.row_values(row):
                    coa_number = sh.cell(row, 4).value
                if 'DATE' in sh.row_values(row):
                    start_row = row
                if 'OPENING BALANCE' in sh.row_values(row):
                    end_row = row
                    break
            coa_number = str(coa_number).replace(' ','')
            bank_obj = self.env['res.partner.bank'].sudo().search([('acc_number','=',coa_number)], limit=1)
            if not bank_obj:
                raise Warning(f'Bank Account {coa_number} belum tersedia di Master Bank Accounts !')
            
            for rx in range(start_row+3, end_row-2):
                cols = [sh.cell(rx, ry).value for ry in range(sh.ncols)]
                tanggal = cols[0]
                time = cols[1]
                remark = cols[2]
                debit = cols[6] if cols[6] else 0
                credit = cols[9] if cols[9] else 0
                saldo = cols[11]
                teller = cols[14]
                coa = coa_number
                credit = credit.split('.')[0].replace(',','')
                debit = debit.split('.')[0].replace(',','')
                saldo = saldo.split('.')[0].replace(',','')
                
                total_credit_file += int(credit)
                total_debit_file += int(debit)
                tanggal = datetime.strptime(tanggal, '%d/%m/%y') if tanggal else ''
                
                var.append({
                    'name': name,
                    'remark': remark,
                    'time': time,
                    'debit': debit,
                    'account_id': bank_obj.account_id.id,
                    'format': self.format,
                    'credit': credit,
                    'saldo': int(saldo),
                    'date': tanggal,
                    'teller': teller,
                    'coa': coa,
                    'no_sistem': ''
                })
        elif self.format == 'bca':
            Reader = base64.b64decode(self.data_file).decode('utf-8')
            if '\r' in Reader:
                Reader = Reader.split('\r\n')
            else:
                Reader = Reader.split('\n')

            reader = csv.reader(Reader)
            saldo_awal = ''
            for i, row in enumerate(reader):
                for x in range(len(row)):
                    # Hapus ';' jika ada
                    row[x] = row[x].replace(';;;;', '')
                
                if i == 0:
                    continue
                if i == 2:
                    coa_number = row[0].split(' : ')[1]
                    bank_obj = self.env['res.partner.bank'].sudo().search([('acc_number','=',coa_number)], limit=1)
                    if not bank_obj:
                        raise Warning(f'Bank Account {coa_number} belum tersedia di Master Bank Accounts !')
                if i == 4:
                    tahun = row[0].split(' : ')[1].split(' - ')[0].split('/')[2]
                if row:
                    saldo_awal = row[0].split(' : ')[0] if ' : ' in row[0] else ''
                if saldo_awal == 'Saldo Awal':
                    break
                if i >= 7: #? Jika template berubah maka rubah juga value berikut ini
                    tanggal = row[0] + f'/{tahun}'
                    if len(row) < 3:
                        raise Warning('Template tidak sesuai, silahkan cek kembali template ! \n Pastikan sudah dilakukan Delimiter dari Row Tanggal Transaksi sampai sebelum Row Saldo Awal.')
                    remark = row[1]
                    cr_db = row[3].split(' ')[1]
                    time = datetime.now().time()
                    if cr_db == 'CR':
                        credit = float(row[3].split(' ')[0].replace(',', ''))
                        debit = 0.0
                    elif cr_db == 'DB':
                        credit = 0.0
                        debit = float(row[3].split(' ')[0].replace(',', ''))
                    saldo = float(row[4].split(' ')[0].replace(',', ''))
                    total_credit_file += credit
                    total_debit_file += debit
                    
                    var.append({
                        'name': name,
                        'remark': remark,
                        'time': time,
                        'debit': debit,
                        'account_id': bank_obj.account_id.id,
                        'format': self.format,
                        'credit': credit,
                        'saldo': saldo,
                        'date': datetime.strptime(tanggal, '%d/%m/%Y') if tanggal else False,
                        'teller': False,
                        'coa': coa_number,
                        'no_sistem': ''
                    })
        elif self.format == 'mandiri':
            coa_number = False
            for row in range(0, sh.nrows):
                if 'Account No.' in sh.row_values(row):
                    coa_number = sh.cell(row+1, 0).value
                    break

            coa_number = str(coa_number).replace(' ', '')
            bank_obj = self.env['res.partner.bank'].sudo().search([('acc_number','=',coa_number)], limit=1)
            if not bank_obj:
                raise Warning(f'Bank Account {coa_number} belum tersedia di Master Bank Accounts !')
            
            for rx in range(1, sh.nrows):
                cols = [sh.cell(rx, ry).value for ry in range(sh.ncols)]
                get_datetime = datetime.strptime(str(cols[1]), '%d/%m/%Y %H.%M.%S')
                date = datetime.strptime(datetime.strftime(get_datetime, '%Y-%m-%d'), '%Y-%m-%d')
                time = datetime.strftime(get_datetime, '%H:%M:%S')
                remark = cols[4]
                debit = cols[6] if cols[6] else 0
                credit = cols[7] if cols[7] else 0
                saldo = cols[8] if cols[8] else 0

                coa = coa_number
                credit = convert_to_number(credit)
                debit = convert_to_number(debit)
                saldo = convert_to_number(saldo)
                total_credit_file += int(credit)
                total_debit_file += int(debit)
                
                var.append({
                    'name': name,
                    'remark': remark,
                    'time': time,
                    'debit': debit,
                    'account_id': bank_obj.account_id.id,
                    'format': self.format,
                    'credit': credit,
                    'saldo': int(saldo),
                    'date': date,
                    'teller': False,
                    'coa': coa,
                    'no_sistem': ''
                })
        elif self.format == 'other':
            for rx in range(1, sh.nrows):
                cols = [sh.cell(rx, ry).value for ry in range(sh.ncols)]
                remark = cols[0]
                branch = cols[1]
                date = convert_to_date(cols[2])
                time = convert_to_time(cols[2])
                account_id = cols[3]
                debit = convert_to_number(cols[4])
                credit = convert_to_number(cols[5])
                saldo = convert_to_number(cols[6])
                coa = convert_to_string(cols[7])

                total_credit_file += int(credit)
                total_debit_file += int(debit)

                bank_obj = self.env['res.partner.bank'].sudo().search([('acc_number','=',coa)], limit=1)
                if not bank_obj:
                    raise Warning(f'COA {coa} tidak ditemukan pada Master Bank Accounts ! (baris. {rx})')
                else:
                    if self.company_id != bank_obj.company_id:
                        raise Warning(f'Branch pada baris {rx} tidak sama dengan branch yang diinput pada wizard !')
                    if branch and bank_obj.company_id.name != branch:
                        raise Warning(f'Branch tidak sesuai dengan Master Bank Accounts {coa} ! (baris. {rx})')
                    elif account_id and bank_obj.account_id.display_name != account_id:
                        raise Warning(f'Account tidak sesuai dengan Master Bank Accounts {coa} ! (baris. {rx})')
                    if bank_obj.bank_id.name.lower() not in ('bca', 'bri', 'bni', 'mandiri'):
                        raise Warning(f'Format bank {bank_obj.bank_id.name} pada Account tidak sesuai format yang tersedia !')

                var.append({
                    'name': name,
                    'time': time,
                    'saldo': saldo,
                    'date': date,
                    'remark': remark,
                    'branch': branch,
                    'account_id': bank_obj.account_id.id,
                    'debit': debit,
                    'credit': credit,
                    'coa': coa,
                    'format': bank_obj.bank_id.name.lower(),
                    'teller': False,
                    'no_sistem': ''
                })
        elif self.format == 'update':
            for rx in range(1, sh.nrows):
                cols = [sh.cell(rx, ry).value for ry in range(sh.ncols)]
                name = cols[0]
                no_sistem = cols[8]
                var.append({
                    'name': name,
                    'no_sistem': no_sistem
                })

        if self.format != 'update':
            if not bank_obj:
                raise Warning('Bank not found !')
            total_saldo_from_excel = total_debit_file - total_credit_file
            query_date= f"""
                SELECT
                    MAX(date)
                FROM tw_bank_mutasi
                WHERE account_id = {bank_obj.account_id.id}
            """
            self._cr.execute(query_date)
            res_max = self._cr.fetchone()
            date_max = res_max[0]

        from_file.update({
            'var_file': var,
            'total_saldo_from_excel': total_saldo_from_excel,
            'date_max': date_max,
            'bank_obj': bank_obj
        })

        return from_file
    
    def action_download_format_file(self):
        """
            Download the Import Bank Mutasi upload template.
            Priority: tw.format.upload record → data/template_import_bank_mutasi.xlsx
        """
        format_name = 'import bank mutasi '
        if self.format == 'bri':
            format_name += 'bri'
        elif self.format == 'bca':
            format_name += 'bca'
        elif self.format == 'mandiri':
            format_name += 'mandiri'
        elif self.format == 'bni':
            format_name += 'bni'
        elif self.format == 'other':
            format_name += 'other'
        elif self.format == 'update':
            format_name += 'update'

        format_obj = self.env['tw.format.upload'].sudo().search([
            ('name','ilike',format_name),
            ('active','=',True),
        ], limit=1)
        if format_obj and format_obj.file_format_show and format_obj.filename_upload_format:
            return {
                'type': 'ir.actions.act_url',
                'name': f'import_bank_mutasi_{self.format}_template',
                'url': (
                    f'/web/content/tw.format.upload/{format_obj.id}'
                    f'/file_format_show/{format_obj.filename_upload_format}?download=true'
                ),
            }

        # Fallback: serve from module data/ folder
        filename = f'template_import_bank_mutasi_{self.format}.xlsx'
        file_path = file_path_util(f'tw_bank_reconcile/data/{filename}')
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
        bank_mutasi_model = self.env['tw.bank.mutasi']
        saldo_akhir_mutasi = 0
        saldo_all = 0
        saldo_akhir = 0
        if self.format == 'update':
            saldo_file_excel = self.check_file()
            for x in saldo_file_excel['var_file']:
                name = x['name'].strip()
                no_sistem = x['no_sistem'].strip()
                query = f"""
                    UPDATE tw_bank_mutasi
                    SET no_sistem = '{no_sistem}', checked = FALSE
                    WHERE name = '{name}' AND state = 'Outstanding'
                """
                self.env.cr.execute(query)
        else:
            saldo_file_excel = self.check_file()
            date_max = saldo_file_excel['date_max']
            if date_max:
                saldo_akhir_mutasi = self.get_saldo_akhir_all_date(saldo_file_excel['bank_obj'].account_id.id)
                saldo_all = saldo_akhir_mutasi + saldo_file_excel['total_saldo_from_excel']
            else:
                saldo_all = self.saldo_akhir
            saldo_all = round(saldo_all, 2)
            saldo_akhir = round(self.saldo_akhir, 2)
            if float_compare(saldo_all, saldo_akhir, precision_digits=2) != 0:
                text_warning_tanggal = 'based on mutasi ' + str(date_max) if date_max else ''
                raise Warning('Saldo akhir yang di input di form (Rp. {:,.2f})\n'.format(saldo_akhir) +
                              'Tidak sesuai dengan total saldo seharusnya (Rp. {:,.2f})\n'.format(saldo_all) +
                              'Silakan periksa kembali data anda. \n\n' +
                              'Saldo sistem {} (Rp. {:,.2f}) \n'.format(text_warning_tanggal, saldo_akhir_mutasi) +
                              'Mutasi di excel (Rp. {:,.2f})'.format(saldo_file_excel['total_saldo_from_excel'])
                            )
            
            for x in saldo_file_excel['var_file']:
                remark = x['remark']
                coa = x['coa']
                is_posted = False
                if (remark[0:17] == 'TRSF E-BANKING DB') and coa[0:6] == '111205':
                    is_posted = True
                vals_mutasi = {
                    'remark': remark,
                    'time': x['time'],
                    'debit': int(x['debit']),
                    'account_id': x['account_id'],
                    'format': x['format'],
                    'credit': int(x['credit']),
                    'saldo': x['saldo'],
                    'date': x['date'],
                    'teller': x['teller'],
                    'coa': coa,
                    'is_posted': is_posted,
                    'no_sistem': x['no_sistem'].strip(),
                    'journal_id': self.journal_id.id,
                    'company_id': self.company_id.id
                }
                bank_mutasi_obj = bank_mutasi_model.suspend_security().create(vals_mutasi)

    # 14: private methods