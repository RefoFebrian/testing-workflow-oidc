import base64
import calendar
import logging
from datetime import datetime, timedelta, date
from io import BytesIO

import xlsxwriter
from odoo import _, api, fields, models
from odoo.exceptions import UserError as Warning
from odoo.tools import SQL

_logger = logging.getLogger(__name__)

class SummaryForecastReport(models.TransientModel):
    _name = "tw.summary.forecast.report"
    _description = "Summary Forecast Report"
    _rec_name = "file"
    
    def _get_first_date_of_the_month(self):
        return date.today().replace(day=1)

    def _get_last_date_of_the_month(self):
        now = date.today()
        month = now.month
        year = now.year
        last_date = calendar.monthrange(year, month)[1]
        return datetime(year, month, last_date)
    
    file = fields.Char('File Name')
    data_x = fields.Binary('File', readonly=True)
    state_x = fields.Selection([('choose','choose'),('get','get')], default='choose')
    start_date = fields.Date('Start Date', default=_get_first_date_of_the_month)
    end_date = fields.Date('End Date', default=_get_last_date_of_the_month)

    wbf = {}
    
    def add_workbook_format(self, workbook):
        self.wbf['company'] = workbook.add_format({'bold':1,'align': 'left','font_color':'#000000','num_format': 'dd-mm-yyyy'})
        self.wbf['company'].set_font_size(12)

        self.wbf['footer'] = workbook.add_format({'align':'left'})

        self.wbf['header'] = workbook.add_format({'bg_color':'#FFFF00','bold': 1,'align': 'center','font_color': '#000000'})
        self.wbf['header'].set_top(2)
        self.wbf['header'].set_bottom()
        self.wbf['header'].set_left()
        self.wbf['header'].set_right()
        self.wbf['header'].set_font_size(11)
        self.wbf['header'].set_align('vcenter')

        self.wbf['header_left'] = workbook.add_format({'bg_color':'#FFFF00','bold': 1,'align': 'center','font_color': '#000000'})
        self.wbf['header_left'].set_top(2)
        self.wbf['header_left'].set_bottom()
        self.wbf['header_left'].set_left(2)
        self.wbf['header_left'].set_right()
        self.wbf['header_left'].set_font_size(11)
        self.wbf['header_left'].set_align('vcenter')
        
        self.wbf['header_right'] = workbook.add_format({'bg_color':'#FFFF00','bold': 1,'align': 'center','font_color': '#000000'})
        self.wbf['header_right'].set_top(2)
        self.wbf['header_right'].set_bottom()
        self.wbf['header_right'].set_left()
        self.wbf['header_right'].set_right(2)
        self.wbf['header_right'].set_font_size(11)
        self.wbf['header_right'].set_align('vcenter')


        self.wbf['content'] = workbook.add_format({'align': 'left','font_color': '#000000'})
        self.wbf['content'].set_left()
        self.wbf['content'].set_right()
        self.wbf['content'].set_top()
        self.wbf['content'].set_bottom()
        self.wbf['content'].set_font_size(10)                

        self.wbf['content_float'] = workbook.add_format({'align': 'right','num_format': '#,##0'})
        self.wbf['content_float'].set_right() 
        self.wbf['content_float'].set_left()
        self.wbf['content_float'].set_top()
        self.wbf['content_float'].set_bottom()
        self.wbf['content_float'].set_font_size(10)     

        self.wbf['content_bg'] = workbook.add_format({'bg_color': '#81DAF5','align': 'center','font_color': '#000000'})
        self.wbf['content_bg'].set_left()
        self.wbf['content_bg'].set_right()
        self.wbf['content_bg'].set_top()
        self.wbf['content_bg'].set_bottom()
        self.wbf['content_bg'].set_font_size(10)                
      
        self.wbf['content_center'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_center'].set_left()
        self.wbf['content_center'].set_right()
        self.wbf['content_center'].set_top()
        self.wbf['content_center'].set_bottom()
        self.wbf['content_center'].set_font_size(10)
        
        self.wbf['content_left'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_left'].set_left(2)
        self.wbf['content_left'].set_right()
        self.wbf['content_left'].set_top()
        self.wbf['content_left'].set_bottom()
        self.wbf['content_left'].set_font_size(10)
        
        self.wbf['content_right'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_right'].set_left()
        self.wbf['content_right'].set_right(2)
        self.wbf['content_right'].set_top()
        self.wbf['content_right'].set_bottom()
        self.wbf['content_right'].set_font_size(10)

        self.wbf['content_bottom'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_bottom'].set_left()
        self.wbf['content_bottom'].set_right()
        self.wbf['content_bottom'].set_top()
        self.wbf['content_bottom'].set_bottom(2)
        self.wbf['content_bottom'].set_font_size(10)

        self.wbf['content_left_bottom'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_left_bottom'].set_left(2)
        self.wbf['content_left_bottom'].set_right()
        self.wbf['content_left_bottom'].set_top()
        self.wbf['content_left_bottom'].set_bottom(2)
        self.wbf['content_left_bottom'].set_font_size(10)
        
        self.wbf['content_right_bottom'] = workbook.add_format({'align': 'center','font_color': '#000000'})
        self.wbf['content_right_bottom'].set_left()
        self.wbf['content_right_bottom'].set_right(2)
        self.wbf['content_right_bottom'].set_top()
        self.wbf['content_right_bottom'].set_bottom(2)
        self.wbf['content_right_bottom'].set_font_size(10)

        self.wbf['content_center_bg'] = workbook.add_format({'bg_color':'#85C1E9', 'align': 'center','font_color': '#000000'})
        self.wbf['content_center_bg'].set_left()
        self.wbf['content_center_bg'].set_right()
        self.wbf['content_center_bg'].set_top()
        self.wbf['content_center_bg'].set_bottom()
        self.wbf['content_center_bg'].set_font_size(10)                
        
        self.wbf['content_center_bg_bottom'] = workbook.add_format({'bg_color':'#85C1E9', 'align': 'center','font_color': '#000000'})
        self.wbf['content_center_bg_bottom'].set_left()
        self.wbf['content_center_bg_bottom'].set_right()
        self.wbf['content_center_bg_bottom'].set_top()
        self.wbf['content_center_bg_bottom'].set_bottom(2)
        self.wbf['content_center_bg_bottom'].set_font_size(10)                
        
        return workbook   
    
    def excel_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)
        return self._download_report()

    def _download_report(self):
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)       
        workbook = self.add_workbook_format(workbook)
        wbf = self.wbf
        worksheet = workbook.add_worksheet('Report Summary Forecast Unit & PBT')

        worksheet.set_column('B1:B1', 15)
        worksheet.set_column('C1:C1', 20)
        worksheet.set_column('D1:D1', 20)
        worksheet.set_column('E1:E1', 15)
        worksheet.set_column('F1:F1', 15)
        worksheet.set_column('G1:G1', 15)
        worksheet.set_column('H1:H1', 25)
        worksheet.set_column('I1:I1', 25)
        worksheet.set_column('J1:J1', 25)
        worksheet.set_column('K1:K1', 25)
        worksheet.set_column('L1:L1', 25)
        
        user_id = self.env['res.users'].search([('id','=',self._uid)])
        user = user_id.name 
        company = user_id.company_id.name
        filename = 'Report Summary Forecast Unit & PBT' + str(self.start_date)+'.xlsx'

        # branch = self.company_ids or self.env.user.company_ids
        # branch_list = str(tuple([b.id for b in branch])).replace(',)', ')')

        query = SQL("""
                SELECT branch.code as code_branch
                        , branch.name as branch_name
                        , am.name as am
                        , margin_line.unit_cash as unit_cash
                        , margin_line.unit_credit as unit_credit
                        , margin_line.unit_cash + margin_line.unit_credit as total_unit
                        , margin.total_all_net_margin_cash as net_margin_cash 
                        , margin.total_all_net_margin_credit as net_margin_credit
                        , margin.total_all_net_margin_cash + margin.total_all_net_margin_credit as total_net_margin
                        , margin.pbt_propose as pbt_m
                        , margin.pbt_propose_lm as pbt_lm
                FROM tw_profit_before_tax margin
                LEFT JOIN (
                            SELECT net_margin_id
                            , SUM(amount_unit_cash) as unit_cash
                            , SUM(amount_unit_credit) as unit_credit
                            FROM tw_profit_before_tax_line
                            GROUP BY net_margin_id) margin_line ON margin.id = margin_line.net_margin_id
                LEFT JOIN res_company branch ON branch.id = margin.company_id
                LEFT JOIN hr_employee am ON am.id = margin.area_manager_id
                WHERE margin.start_date >= %s
                AND margin.end_date <= %s
            """, self.start_date, self.end_date)
        
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
        if not ress:
            raise Warning(_("No Data Found!"))
        
        worksheet.merge_range('A1:D1', company , wbf['company'])
        worksheet.merge_range('A2:D2', 'Report Summary Forecast Unit & PBT' , wbf['company'])
        worksheet.merge_range('A3:D3', f'Tanggal {self.start_date} s/d {self.end_date}' , wbf['company'])
        
        row=5
        worksheet.set_row(row+1, 25)
        worksheet.merge_range(f'A{row+1}:A{row+2}', 'No' , wbf['header_left'])
        worksheet.merge_range(f'B{row+1}:B{row+2}', 'Kode Cabang' , wbf['header'])
        worksheet.merge_range(f'C{row+1}:C{row+2}', 'Nama Cabang' , wbf['header'])
        worksheet.merge_range(f'D{row+1}:D{row+2}', 'AM' , wbf['header'])
        worksheet.merge_range(f'E{row+1}:G{row+1}', 'Unit' , wbf['header'])
        worksheet.write(f'E{row+2}', 'Cash' , wbf['header'])
        worksheet.write(f'F{row+2}', 'Credit' , wbf['header'])
        worksheet.write(f'G{row+2}', 'Total' , wbf['header'])
        worksheet.merge_range(f'H{row+1}:J{row+1}', 'Sisa Marjin' , wbf['header'])
        worksheet.write(f'H{row+2}', 'Cash' , wbf['header'])
        worksheet.write(f'I{row+2}', 'Credit' , wbf['header'])
        worksheet.write(f'J{row+2}', 'Total' , wbf['header'])
        worksheet.merge_range(f'K{row+1}:L{row+1}', 'PBT' , wbf['header'])
        worksheet.write(f'K{row+2}', 'M' , wbf['header'])
        worksheet.write(f'L{row+2}', 'LM' , wbf['header'])
        

        row += 3
        no = 1
       
        if ress == []:
            worksheet.merge_range(f'A{row}:H{row}', 'Data tidak ada !' , wbf['content'])
            
        for res in ress:
            branch = res.get('branch_name')
            branch_code = res.get('code_branch')
            area_manager = res.get('am')
            unit_cash = res.get('unit_cash')
            unit_credit = res.get('unit_credit')
            total_unit = res.get('total_unit')
            net_margin_cash = res.get('net_margin_cash')
            net_margin_credit = res.get('net_margin_credit')
            total_net_margin = res.get('total_net_margin')
            pbt_m = res.get('pbt_m')
            pbt_lm = res.get('pbt_lm')
            
            worksheet.write('A%s' % row, no , wbf['content_left']) 
            worksheet.write('B%s' % row, branch_code , wbf['content']) 
            worksheet.write('C%s' % row, branch , wbf['content'])
            worksheet.write('D%s' % row, area_manager , wbf['content'])
            worksheet.write('E%s' % row, unit_cash, wbf['content'])
            worksheet.write('F%s' % row, unit_credit, wbf['content'])
            worksheet.write('G%s' % row, total_unit, wbf['content_float'])
            worksheet.write('H%s' % row, net_margin_cash, wbf['content_float'])
            worksheet.write('I%s' % row, net_margin_credit, wbf['content_float'])
            worksheet.write('J%s' % row, total_net_margin, wbf['content_float'])
            worksheet.write('K%s' % row, pbt_m , wbf['content'])
            worksheet.write('L%s' % row, pbt_lm , wbf['content'])
            no += 1 
            row += 1     

        # worksheet.autofilter('A5:D%s' % (row)) 
        worksheet.autofilter(f'B6:L{row}') 
        worksheet.freeze_panes(6, 4)
        worksheet.merge_range(f'A{row+2}:E{row+2}', f'{(datetime.now() + timedelta(hours=7)).isoformat()}, {user}' , wbf['footer'])  
        
        workbook.close()
        out=base64.b64encode(fp.getvalue())
        self.data_x = out
        self.file = filename
        
        fp.close()
        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': '/web/content/tw.summary.forecast.report/%s/data_x/%s?download=true' % (self.id, filename)
        }  
    