# 1: imports of python lib
from datetime import date, datetime, timedelta,time
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning, RedirectWarning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

import xlsxwriter
from io import StringIO,BytesIO
import base64
import os
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
import calendar

class ReportMekanikMitraWizard(models.TransientModel):
    _name = "tw.report.mekanik.mitra.wizard"
    _description = "TW Report Mekanik Mitra Wizard"

    wbf = {}

    # 7: defaults methods
    def _get_tahun(self):
        return datetime.today().date().year

    # 8: fields
    name = fields.Char('Filename', readonly=True)
    data_x = fields.Binary('File', readonly=True)
    bulan = fields.Selection([('1','Januari'),
                              ('2','Februari'),
                              ('3','Maret'),
                              ('4','April'),
                              ('5','Mei'),
                              ('6','Juni'),
                              ('7','Juli'),
                              ('8','Agustus'),
                              ('9','September'),
                              ('10','Oktober'),
                              ('11','November'),
                              ('12','Desember')], 'Bulan', required=True)
    tahun = fields.Char('Tahun', default=_get_tahun,required=True)
    company_ids = fields.Many2many('res.company', 'tw_report_mekanik_mitra_rel', 'mitra_id','company_id', string='Branch')

    def add_workbook_format(self, workbook):
        self.wbf['company'] = workbook.add_format({'bold':1,'align': 'center'})
        self.wbf['company'].set_font_size(12)
        
        self.wbf['title'] = workbook.add_format({'bold':1,'align': 'left'})
        self.wbf['title'].set_font_size(11)

        self.wbf['footer'] = workbook.add_format({'align':'left'})

        self.wbf['header'] = workbook.add_format({'bg_color':'#FFFFDB','bold': 1,'align': 'center','font_color': '#000000'})
        self.wbf['header'].set_top(2)
        self.wbf['header'].set_bottom()
        self.wbf['header'].set_left()
        self.wbf['header'].set_right()
        self.wbf['header'].set_font_size(11)
        self.wbf['header'].set_align('vcenter')

        
        self.wbf['content'] = workbook.add_format({'align': 'left','font_color': '#000000'})
        self.wbf['content'].set_left()
        self.wbf['content'].set_right()
        self.wbf['content'].set_top()
        self.wbf['content'].set_bottom()
        self.wbf['content'].set_font_size(10)                

        self.wbf['content_isi_left'] = workbook.add_format({'align': 'center'})
        self.wbf['content_isi_left'].set_left()
        self.wbf['content_isi_left'].set_font_size(10)                
        
        self.wbf['content_isi_right'] = workbook.add_format({'align': 'center'})
        self.wbf['content_isi_right'].set_right()
        self.wbf['content_isi_right'].set_font_size(10)                
        
        self.wbf['content_isi'] = workbook.add_format({'align': 'center'})
        self.wbf['content_isi'].set_font_size(10)                
        
        self.wbf['content_ttd'] = workbook.add_format({'bold':1,'align': 'center'})
        self.wbf['content_ttd'].set_left()
        self.wbf['content_ttd'].set_right()
        self.wbf['content_ttd'].set_top()
        self.wbf['content_ttd'].set_bottom()
        self.wbf['content_ttd'].set_font_size(10)                

        self.wbf['content_right'] = workbook.add_format({'align': 'right','font_color': '#000000'})
        self.wbf['content_right'].set_left()
        self.wbf['content_right'].set_right(2)
        self.wbf['content_right'].set_top()
        self.wbf['content_right'].set_bottom()
        self.wbf['content_right'].set_font_size(10)

        self.wbf['total'] = workbook.add_format({'bold':1,'bg_color': '#FFFFDB','align':'center'})
        self.wbf['total'].set_left()
        self.wbf['total'].set_right()
        self.wbf['total'].set_top()
        self.wbf['total'].set_bottom()
        
        self.wbf['content_float'] = workbook.add_format({'align': 'right','num_format': '#,##0.00'})
        self.wbf['content_float'].set_top()
        self.wbf['content_float'].set_bottom()            
        self.wbf['content_float'].set_left()
        self.wbf['content_float'].set_right()   
        self.wbf['content_float'].set_font_size(10)       

        self.wbf['total_number'] = workbook.add_format({'align':'right','bg_color': '#FFFFDB','bold':1,'num_format': '#,##0.00'})
        self.wbf['total_number'].set_top()
        self.wbf['total_number'].set_bottom()            
        self.wbf['total_number'].set_left()
        self.wbf['total_number'].set_right()
       
        self.wbf['total_number_float'] = workbook.add_format({'align':'right','bg_color': '#FFFFDB','bold':1})
        self.wbf['total_number_float'].set_top()
        self.wbf['total_number_float'].set_bottom()            
        self.wbf['total_number_float'].set_left()
        self.wbf['total_number_float'].set_right()
       
        return workbook

    def excel_report(self):
        bulan = int(self.bulan)
        tahun = int(self.tahun)
        nama_bln = calendar.month_name[bulan]

        filename = 'Report_Mekanik_Mitra_' + str(bulan) + '_' + str(tahun) + '.xlsx'

        start_date = date(tahun, bulan, 1)
        end_date = start_date + relativedelta(months=1) - relativedelta(days=1)
        
        if self.company_ids:
            branch = [b.id for b in self.company_ids]
        else:
            branch = self.env.user._get_company_ids()

        query = f"""
            SELECT b.id as company_id
                , b.code as branch_code
                , b.name as branch_name
                , hr.id as employee_id
                , mekanik.id as user_id
                , hr.name as mekanik
                , COALESCE(cnt_unit.cnt_unit,0) as total_ue
                , COALESCE(jasa.amt_jasa,0) as total_jasa
                , COALESCE(jasa.amt_part,0) as total_part
                , mm.id as mm_id
                , bank.name as bank
                , mm.acc_number as no_rekening
                , mx.id as mx_id
                FROM tw_work_order mekanik
                INNER JOIN res_company b ON b.id = mekanik.company_id
                LEFT JOIN (
                    SELECT COALESCE(wo.mechanic_id,0) as mekanik_id
                    , SUM(CASE WHEN wol.division = 'Service' THEN COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100)  * COALESCE(wol.product_uom_qty,0) END) amt_jasa
                    , SUM(CASE WHEN wol.division = 'Sparepart' AND pc.name NOT IN ( 'OLI','OIL') THEN COALESCE(wol.price_unit,0) * (1 - COALESCE(NULLIF(wol.discount,0),0) / 100)  * wol.qty_delivered END) amt_part
                FROM tw_work_order wo
                INNER JOIN account_move ai ON wo.name = ai.invoice_origin
                INNER JOIN tw_work_order_line wol ON wo.id = wol.order_id
                LEFT JOIN product_product p ON wol.product_id = p.id
                LEFT JOIN product_template pt ON p.product_tmpl_id = pt.id
                LEFT JOIN product_category pc ON pt.categ_id = pc.id
                WHERE wo.state IN ('sale', 'done')
                AND wo.company_id IN {str(tuple(branch)).replace(',)', ')')}
                AND wo.open_date BETWEEN '{start_date}' AND '{end_date}'
                GROUP BY wo.mechanic_id
                ) jasa ON COALESCE(jasa.mekanik_id,0) = COALESCE(mekanik.mechanic_id,0)
                LEFT JOIN (
                    SELECT unit.mekanik_id,sum(unit.cnt_per_date) cnt_unit 
                    FROM (
                        SELECT wo.company_id
                            , wo.open_date
                            ,COALESCE(wo.mechanic_id,0) mekanik_id
                            , COUNT(DISTINCT wo.lot_id) cnt_per_date
                        FROM tw_work_order wo
                        INNER JOIN account_move ai ON wo.name = ai.invoice_origin
                        WHERE wo.state IN ('sale', 'done')
                        AND wo.type <> 'WAR' AND wo.type <> 'SLS'
                        AND wo.open_date BETWEEN '{start_date}' AND '{end_date}'
                        GROUP BY wo.company_id, wo.open_date,COALESCE(wo.mechanic_id,0)
                    ) unit GROUP BY unit.mekanik_id
                ) cnt_unit ON cnt_unit.mekanik_id = mekanik.mechanic_id
                INNER JOIN hr_employee hr ON hr.id = mekanik.mechanic_id
                INNER JOIN hr_employee mm ON mm.id = hr.id and mm.company_id = mekanik.company_id
                INNER JOIN tw_matrix_mekanik_mitra mx ON mx.company_id = b.id
                LEFT JOIN res_bank bank ON bank.id = mm.bank_id
                WHERE mekanik.open_date BETWEEN '{start_date}' AND '{end_date}'
                AND mekanik.company_id IN {str(tuple(branch)).replace(',)', ')')}
                GROUP BY b.id,jasa.amt_jasa,jasa.amt_part,hr.id,mekanik.id,cnt_unit.cnt_unit,mm.id,mx.id,bank.id
            """
        self._cr.execute(query)

        ress = self._cr.dictfetchall()

        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)       
        workbook = self.add_workbook_format(workbook)
        wbf = self.wbf
        worksheet = workbook.add_worksheet('Report Mekanik Mitra')

        worksheet.set_column('A1:A1', 3)
        worksheet.set_column('B1:B1', 12)
        worksheet.set_column('C1:C1', 18)
        worksheet.set_column('D1:D1', 25)
        worksheet.set_column('E1:E1', 7)
        worksheet.set_column('F1:F1', 15)
        worksheet.set_column('G1:G1', 15)
        worksheet.set_column('H1:H1', 10)
        worksheet.set_column('I1:I1', 15)
        worksheet.set_column('J1:J1', 15)
        worksheet.set_column('K1:K1', 15)
        worksheet.set_column('L1:L1', 15)
        worksheet.set_column('M1:M1', 10)
        worksheet.set_column('N1:N1', 19)
        
        filename = 'Report Mekanik Mitra %s %s.xlsx' %(nama_bln,tahun)

        worksheet.merge_range('A1:N1', 'Rekap Bagi Hasil Mekanik Mitra Periode %s %s'%(nama_bln,tahun), wbf['company'])    
        worksheet.merge_range('A2:N2', '', wbf['company'])    
        
        worksheet.merge_range('B3:G3', 'Berikut kami ajukan bagi hasil mekanik mitra usaha Periode %s %s:'%(nama_bln,tahun), wbf['title'])    

        row=4
        worksheet.write('A%s' % (row+1), 'No' , wbf['header'])
        worksheet.write('B%s' % (row+1), 'Code Cabang' , wbf['header'])
        worksheet.write('C%s' % (row+1), 'Nama Cabang' , wbf['header'])
        worksheet.write('D%s' % (row+1), 'Nama Karyawan' , wbf['header'])
        worksheet.write('E%s' % (row+1), 'UE' , wbf['header'])
        worksheet.write('F%s' % (row+1), 'Jasa' , wbf['header'])
        worksheet.write('G%s' % (row+1), 'Part' , wbf['header'])
        worksheet.write('H%s' % (row+1), 'Hari Kerja' , wbf['header'])
        worksheet.write('I%s' % (row+1), 'Hasil Hari Kerja' , wbf['header'])
        worksheet.write('J%s' % (row+1), 'Hasil Jasa' , wbf['header'])
        worksheet.write('K%s' % (row+1), 'Hasil Part' , wbf['header'])
        worksheet.write('L%s' % (row+1), 'Total' , wbf['header'])
        worksheet.write('M%s' % (row+1), 'Bank' , wbf['header'])
        worksheet.write('N%s' % (row+1), 'No Rekening' , wbf['header'])

        row+=2       
        row1 = row
        no = 1

        sum_total_ue = 0
        sum_total_part = 0 
        sum_total_jasa = 0
        sum_total_hari_kerja = 0
        sum_x_hari_kerja = 0
        sum_x_jasa = 0
        sum_x_part = 0
        sum_total = 0

        for res in ress:
            master_mekanik = self.env['tw.matrix.mekanik.mitra'].sudo().browse(res['mx_id'])

            company_id = res.get('company_id')
            branch_name = res.get('branch_name')
            branch_code = res.get('branch_code')
            total_ue = res.get('total_ue')
            total_part = res.get('total_part')
            total_jasa = res.get('total_jasa')
            employee_id = res.get('employee_id')
            user_id = res.get('user_id')
            mekanik = res.get('mekanik')
            bank = res.get('bank')
            no_rekening = res.get('no_rekening')
            mm_id = res.get('mm_id')
            
            hari_kerja = 0
            hari_kerja = self.get_hari_kerja(user_id,company_id,start_date,end_date)
            x_hari_kerja = 0
            x_jasa = 0
            x_part = 0

            for master in master_mekanik.detail_ids:
                if total_ue in range(int(master.min_ue),int(master.max_ue)):
                    x_hari_kerja = hari_kerja * master.hari_kerja
                    x_jasa = total_jasa * (master.jasa / 100)
                    x_part = total_part * (master.part / 100)

            total = x_hari_kerja + x_jasa + x_part
           
            sum_total_ue += total_ue
            sum_total_part += total_part
            sum_total_jasa += total_jasa
            sum_total_hari_kerja += hari_kerja
            sum_x_hari_kerja += x_hari_kerja
            sum_x_jasa += x_jasa
            sum_x_part += x_part
            sum_total = total

            worksheet.write('A%s' % row, no , wbf['content']) 
            worksheet.write('B%s' % row, branch_code , wbf['content']) 
            worksheet.write('C%s' % row, branch_name , wbf['content']) 
            worksheet.write('D%s' % row, mekanik , wbf['content'])
            worksheet.write('E%s' % row, total_ue , wbf['content_right'])
            worksheet.write('F%s' % row, total_jasa , wbf['content_float'])
            worksheet.write('G%s' % row, total_part , wbf['content_float'])
            worksheet.write('H%s' % row, hari_kerja , wbf['content_right'])
            worksheet.write('I%s' % row, x_hari_kerja , wbf['content_float'])
            worksheet.write('J%s' % row, x_jasa , wbf['content_float'])
            worksheet.write('K%s' % row, x_part , wbf['content_float'])
            worksheet.write('L%s' % row, total , wbf['content_float'])
            worksheet.write('M%s' % row, bank , wbf['content'])
            worksheet.write('N%s' % row, no_rekening , wbf['content'])

            no += 1 
            row += 1    

        formula_total_ue = '{=subtotal(9,E%s:E%s)}' % (row1, row-1)
        formula_total_jasa = '{=subtotal(9,F%s:F%s)}' % (row1, row-1)
        formula_total_part = '{=subtotal(9,G%s:G%s)}' % (row1, row-1)
        formula_total_hari_kerja = '{=subtotal(9,H%s:H%s)}' % (row1, row-1)
        formula_total_x_hari_kerja = '{=subtotal(9,I%s:I%s)}' % (row1, row-1)
        formula_total_x_jasa = '{=subtotal(9,J%s:J%s)}' % (row1, row-1)
        formula_total_x_part = '{=subtotal(9,K%s:K%s)}' % (row1, row-1)
        formula_total = '{=subtotal(9,L%s:L%s)}' % (row1, row-1)
        
        #TOTAL
        worksheet.merge_range('A%s:D%s' % (row,row), 'Total', wbf['total'])    
        worksheet.merge_range('M%s:N%s' % (row,row), '', wbf['total'])    

        worksheet.write_formula(row-1,4,formula_total_ue, wbf['total_number_float'], sum_total_ue)
        worksheet.write_formula(row-1,5,formula_total_jasa, wbf['total_number'], sum_total_jasa)
        worksheet.write_formula(row-1,6,formula_total_part, wbf['total_number'], sum_total_part)
        worksheet.write_formula(row-1,7,formula_total_hari_kerja, wbf['total_number_float'], sum_total_hari_kerja)
        worksheet.write_formula(row-1,8,formula_total_x_hari_kerja, wbf['total_number'], sum_x_hari_kerja)
        worksheet.write_formula(row-1,9,formula_total_x_jasa, wbf['total_number'], sum_x_jasa)
        worksheet.write_formula(row-1,10,formula_total_x_part, wbf['total_number'], sum_x_part)
        worksheet.write_formula(row-1,11,formula_total, wbf['total_number'], sum_total)        

        cetak_uid = self.env['res.users'].sudo().browse(self._uid).name

        row += 2
        worksheet.write('A%s' % row, 'No' , wbf['header'])
        worksheet.merge_range('B%s:C%s' %(row,row), 'NC' , wbf['header'])
        row += 1
        worksheet.write('A%s' % row, '1' , wbf['content'])
        worksheet.merge_range('B%s:C%s' %(row,row), '' , wbf['content'])
        row += 1
        worksheet.write('A%s' % row, '2' , wbf['content'])
        worksheet.merge_range('B%s:C%s' %(row,row), '' , wbf['content'])
        row += 1
        worksheet.write('A%s' % row, '2' , wbf['content'])
        worksheet.merge_range('B%s:C%s' %(row,row), '' , wbf['content'])

        row += 2
        row_x = row+1
        
        worksheet.merge_range('A%s:B%s' %(row,row), 'Dibuat' , wbf['header'])
        worksheet.write('C%s' %(row), 'Diperiksa' , wbf['header'])
        worksheet.write('D%s' %(row), 'Diketahui' , wbf['header'])
        worksheet.merge_range('E%s:N%s' %(row,row), 'Disetujui' , wbf['header'])
        
        worksheet.merge_range('A%s:A%s' %(row_x,row_x+3), '' , wbf['content_isi_left'])
        worksheet.merge_range('B%s:B%s' %(row_x,row_x+3), '' , wbf['content_isi_right'])
        worksheet.merge_range('C%s:C%s' %(row_x,row_x+3), '' , wbf['content_isi_right'])
        worksheet.merge_range('D%s:D%s' %(row_x,row_x+3), '' , wbf['content_isi_right'])
        worksheet.merge_range('E%s:E%s' %(row_x,row_x+3), '' , wbf['content_isi'])
        worksheet.merge_range('F%s:F%s' %(row_x,row_x+3), '' , wbf['content_isi_right'])
        worksheet.merge_range('G%s:G%s' %(row_x,row_x+3), '' , wbf['content_isi'])
        worksheet.merge_range('H%s:H%s' %(row_x,row_x+3), '' , wbf['content_isi_right'])
        worksheet.merge_range('I%s:I%s' %(row_x,row_x+3), '' , wbf['content_isi'])
        worksheet.merge_range('J%s:J%s' %(row_x,row_x+3), '' , wbf['content_isi_right'])
        worksheet.merge_range('K%s:K%s' %(row_x,row_x+3), '' , wbf['content_isi'])
        worksheet.merge_range('L%s:L%s' %(row_x,row_x+3), '' , wbf['content_isi_right'])
        worksheet.merge_range('M%s:M%s' %(row_x,row_x+3), '' , wbf['content_isi'])
        worksheet.merge_range('N%s:N%s' %(row_x,row_x+3), '' , wbf['content_isi_right'])
                         
        row += 5

        worksheet.merge_range('A%s:B%s' %(row,row), cetak_uid , wbf['content_ttd'])
        worksheet.write('C%s' %(row), '' , wbf['content_ttd'])
        worksheet.write('D%s' %(row), '' , wbf['content_ttd'])
        worksheet.merge_range('E%s:F%s' %(row,row), '' , wbf['content_ttd'])
        worksheet.merge_range('G%s:H%s' %(row,row), '' , wbf['content_ttd'])
        worksheet.merge_range('I%s:J%s' %(row,row), '' , wbf['content_ttd'])
        worksheet.merge_range('K%s:L%s' %(row,row), '' , wbf['content_ttd'])
        worksheet.merge_range('M%s:N%s' %(row,row), '' , wbf['content_ttd'])

        row += 1
        worksheet.merge_range('A%s:B%s' %(row,row), 'Workshop Spv' , wbf['content_ttd'])
        worksheet.write('C%s' %(row), 'A.S.S. Manager' , wbf['content_ttd'])
        worksheet.write('D%s' %(row), 'Area Manager' , wbf['content_ttd'])
        worksheet.merge_range('E%s:F%s' %(row,row), 'Admin G.M' , wbf['content_ttd'])
        worksheet.merge_range('G%s:H%s' %(row,row), 'Operation G.M' , wbf['content_ttd'])
        worksheet.merge_range('I%s:J%s' %(row,row), 'C.O.O' , wbf['content_ttd'])
        worksheet.merge_range('K%s:L%s' %(row,row), 'Director' , wbf['content_ttd'])
        worksheet.merge_range('M%s:N%s' %(row,row), 'Pres. Director' , wbf['content_ttd'])


        workbook.close()
        out=base64.encodebytes(fp.getvalue())
        self.suspend_security().write({'name': filename,'data_x':out})
        fp.close()
        return {
            'type': 'ir.actions.act_url',
            'name': ('Download File'),
            'url': '/web/content/tw.report.mekanik.mitra.wizard/%s/data_x/%s?download=true' % (self.id, filename)
        }   

    def get_hari_kerja(self,user_id,company_id,start_date,end_date):
        query = f"""
            SELECT COALESCE(count(DISTINCT(date)),0) as jml
            FROM tw_work_order
            WHERE company_id = {company_id}
            AND mechanic_id = {user_id}
            AND open_date BETWEEN '{start_date}' AND '{end_date}' 
        """
        self._cr.execute(query)
        res = self._cr.fetchone()

        return res[0]

