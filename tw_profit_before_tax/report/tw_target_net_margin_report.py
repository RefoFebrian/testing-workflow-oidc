import base64
import calendar
import logging
import xlsxwriter
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from io import BytesIO

from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
from odoo.tools import SQL

_logger = logging.getLogger(__name__)

class TargetNetMarginReport(models.TransientModel):
    _name = "tw.target.net.margin.report"
    _rec_name = "file"
    _description = "Report Target Margin"
    
    def _get_first_date_of_the_month(self):
        return date.today().replace(day=1)

    def _get_last_date_of_the_month(self):
        now = date.today()
        month = now.month
        year = now.year
        last_date = calendar.monthrange(year, month)[1]
        return datetime(year, month, last_date)

    def _get_default_branch(self):
        return self.env.user.company_ids.ids if self.env.user.company_ids else False
    
    file = fields.Char('File Name')
    data_x = fields.Binary('File', readonly=True)
    state_x = fields.Selection([('choose','choose'),('get','get')], default='choose')
    company_id = fields.Many2one('res.company',"Branch", default=_get_default_branch)
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

        self.wbf['header_left'] = workbook.add_format({'bg_color':'#FFFF00','bold': 1,'align': 'left','font_color': '#000000'})
        self.wbf['header_left'].set_top(2)
        self.wbf['header_left'].set_bottom()
        self.wbf['header_left'].set_left(2)
        self.wbf['header_left'].set_right()
        self.wbf['header_left'].set_font_size(11)
        self.wbf['header_left'].set_align('vcenter')
        
        self.wbf['header_right'] = workbook.add_format({'bg_color':'#FFFF00','bold': 1,'align': 'right','font_color': '#000000'})
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
        
        self.wbf['content_left'] = workbook.add_format({'align': 'left','font_color': '#000000'})
        self.wbf['content_left'].set_left(2)
        self.wbf['content_left'].set_right()
        self.wbf['content_left'].set_top()
        self.wbf['content_left'].set_bottom()
        self.wbf['content_left'].set_font_size(10)
        
        self.wbf['content_right'] = workbook.add_format({'align': 'right','font_color': '#000000'})
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

        fomonth = self.start_date
        month = self.end_date
        lomonth = self.end_date - relativedelta(days=1)
        folmonth = lomonth.replace(day=1)

        worksheet.set_column('A1:A1', 20)
        worksheet.set_column('B1:B1', 15)
        worksheet.set_column('C1:C1', 15)
        worksheet.set_column('D1:D1', 15)
        worksheet.set_column('E1:E1', 15)
        worksheet.set_column('F1:F1', 15)
        worksheet.set_column('G1:G1', 15)
        worksheet.set_column('H1:H1', 15)
        worksheet.set_column('I1:I1', 15)
        worksheet.set_column('J1:J1', 15)
        worksheet.set_column('K1:K1', 15)
        worksheet.set_column('L1:L1', 15)
        worksheet.set_column('M1:M1', 15)
        worksheet.set_column('N1:N1', 10)
        worksheet.set_column('O1:O1', 10)
        
        user_id = self.env['res.users'].search([('id','=',self._uid)])
        user = user_id.name 
        company = user_id.company_id.name
        filename = f'Report Target Net Margin {self.start_date.isoformat()}.xlsx'

        segment = self.env['product.category'].search([('parent_id.name', '=', 'Unit')])
        subsegment_ids = self.env['product.category'].search([('parent_id', 'in', segment.ids)]).ids
        year = str(datetime.now().year)

        query = SQL("""
                SELECT series.name AS series,
                    m.*,
                    lm.*
                FROM product_category series
                    LEFT JOIN (
                        SELECT b.series_id AS series_id,
                            COALESCE(b.year, %(year)s) AS year,
                            COALESCE(b.net_margin_sco_cash, 0) AS m_sco_cash,
                            COALESCE(b.net_margin_sco_credit, 0) AS m_sco_credit,
                            COALESCE(b.net_margin_salesman_cash, 0) AS m_salesman_cash,
                            COALESCE(b.net_margin_salesman_credit, 0) AS m_salesman_credit,
                            COALESCE(b.net_margin_counter_cash, 0) AS m_counter_cash,
                            COALESCE(b.net_margin_counter_credit, 0) AS m_counter_credit,
                            b.description,
                            b.state
                        FROM (
                            select * 
                            from tw_profit_before_tax a
                            WHERE 1 = 1
                                AND start_date = %(fomonth)s
                                AND end_date = %(month)s
                                AND company_id = %(company_id)s
                            order by id desc
                            limit 1
                            ) a
                            LEFT JOIN tw_profit_before_tax_line b ON a.id = b.net_margin_id
                            LEFT JOIN product_series c ON c.id = b.series_id
                    ) m ON m.series_id = series.id
                    LEFT JOIN (
                        SELECT b.series_id AS series_id,
                            COALESCE(b.year, %(year)s) AS year,
                            COALESCE(b.net_margin_sco_cash, 0) AS lm_sco_cash,
                            COALESCE(b.net_margin_sco_credit, 0) AS lm_sco_credit,
                            COALESCE(b.net_margin_salesman_cash, 0) AS lm_salesman_cash,
                            COALESCE(b.net_margin_salesman_credit, 0) AS lm_salesman_credit,
                            COALESCE(b.net_margin_counter_cash, 0) AS lm_counter_cash,
                            COALESCE(b.net_margin_counter_credit, 0) AS lm_counter_credit
                        FROM (
                            select *
                            from tw_profit_before_tax
                            WHERE 1 = 1
                                AND start_date = %(folmonth)s
                                AND end_date = %(lomonth)s
                                AND company_id = %(company_id)s
                            order by id desc
                            limit 1
                            ) a
                            LEFT JOIN tw_profit_before_tax_line b ON a.id = b.net_margin_id
                            LEFT JOIN product_series c ON c.id = b.series_id
                    ) lm ON lm.series_id = series.id
                WHERE series.parent_id = ANY(%(subsegments)s)
            """, year=year, fomonth=fomonth , month=month , folmonth=folmonth , lomonth=lomonth , company_id=self.company_id.id, subsegments=subsegment_ids)
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
        if not ress:
            raise Warning("Tidak ada data.")
        
        worksheet.merge_range('A1:D1', company , wbf['company'])
        worksheet.merge_range('A2:D2', 'Report Target Net Margin' , wbf['company'])
        worksheet.merge_range('A3:D3', f'{self.company_id.name}' , wbf['company'])
        worksheet.merge_range('A4:D4', f'Tanggal {self.start_date} s/d {self.end_date}' , wbf['company'])
        
        row = 5
        worksheet.set_row(row + 1, 25)
        worksheet.merge_range(f'A{row}:A{row + 2}', 'Series', wbf['header'])
        worksheet.merge_range(f'B{row}:B{row + 2}', 'Manufacture Year', wbf['header'])
        
        worksheet.merge_range(f'C{row}:H{row}', 'Net Margin (M)' , wbf['header'])
        worksheet.merge_range(f'C{row + 1}:D{row + 1}', 'Salesman (Partner, SC)' , wbf['header'])
        worksheet.write(f'C{row + 2}', 'Cash', wbf['header'])
        worksheet.write(f'D{row + 2}', 'Credit', wbf['header'])
        
        worksheet.merge_range(f'e{row + 1}:F{row + 1}', 'SC' , wbf['header'])
        worksheet.write(f'E{row + 2}', 'Cash', wbf['header'])
        worksheet.write(f'F{row + 2}', 'Credit', wbf['header'])
        
        worksheet.merge_range(f'G{row + 1}:H{row + 1}', 'SCO' , wbf['header'])
        worksheet.write(f'G{row + 2}', 'Cash', wbf['header'])
        worksheet.write(f'H{row + 2}', 'Credit', wbf['header'])
        
        worksheet.merge_range(f'I{row}:N{row}', 'Net Margin (LM)' , wbf['header'])
        worksheet.merge_range(f'I{row + 1}:J{row + 1}', 'Salesman (Partner, SC)' , wbf['header'])
        worksheet.write(f'I{row + 2}', 'Cash', wbf['header'])
        worksheet.write(f'J{row + 2}', 'Credit', wbf['header'])
        
        worksheet.merge_range(f'K{row + 1}:L{row + 1}', 'SC' , wbf['header'])
        worksheet.write(f'K{row + 2}', 'Cash', wbf['header'])
        worksheet.write(f'L{row + 2}', 'Credit', wbf['header'])
        
        worksheet.merge_range(f'M{row + 1}:N{row + 1}', 'SCO' , wbf['header'])
        worksheet.write(f'M{row + 2}', 'Cash', wbf['header'])
        worksheet.write(f'N{row + 2}', 'Credit', wbf['header'])
        
        worksheet.merge_range(f'O{row}:O{row + 2}', 'Description', wbf['header'])
        worksheet.merge_range(f'P{row}:P{row + 2}', 'Approval', wbf['header'])

        row += 3
        no = 1
       
        if ress == []:
            worksheet.merge_range(f'A{row}:H{row}', 'Data tidak ada !' , wbf['content'])
            
        for res in ress:
            worksheet.write('A%s' % row, res.get('series', ''), wbf['content_left']) 
            worksheet.write('B%s' % row, res.get('year', 0.0), wbf['content_float'])
            worksheet.write('C%s' % row, res.get('m_salesman_cash', 0.0), wbf['content_float'])
            worksheet.write('D%s' % row, res.get('m_salesman_credit', 0.0), wbf['content_float'])
            worksheet.write('E%s' % row, res.get('m_counter_cash', 0.0), wbf['content_float'])
            worksheet.write('F%s' % row, res.get('m_counter_credit', 0.0), wbf['content_float'])
            worksheet.write('G%s' % row, res.get('m_sco_cash', 0.0), wbf['content_float']) 
            worksheet.write('H%s' % row, res.get('m_sco_credit', 0.0), wbf['content_float'])
            worksheet.write('I%s' % row, res.get('lm_salesman_cash', 0.0), wbf['content_float'])
            worksheet.write('J%s' % row, res.get('lm_salesman_credit', 0.0), wbf['content_float'])
            worksheet.write('K%s' % row, res.get('lm_counter_cash', 0.0), wbf['content_float'])
            worksheet.write('L%s' % row, res.get('lm_counter_credit', 0.0), wbf['content_float'])
            worksheet.write('M%s' % row, res.get('lm_sco_cash', 0.0), wbf['content_float'])
            worksheet.write('N%s' % row, res.get('lm_sco_credit', 0.0), wbf['content_float'])
            worksheet.write('O%s' % row, res.get('description', ''), wbf['content_center'])
            worksheet.write('P%s' % row, res.get('state', ''), wbf['content_center'])
            no += 1 
            row += 1     

        # worksheet.autofilter('A5:D%s' % (row))
        worksheet.autofilter(f'A7:P{row}') 
        worksheet.freeze_panes(7, 1)
        worksheet.merge_range(f'A{row+2}:F{row+2}', f'{(datetime.now() + timedelta(hours=7)).isoformat()}, {user}' , wbf['footer'])  
        
        workbook.close()
        out=base64.b64encode(fp.getvalue())
        self.data_x = out
        self.file = filename
        
        fp.close()
        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': '/web/content/tw.target.net.margin.report/%s/data_x/%s?download=true' % (self.id, filename)
        }  
    