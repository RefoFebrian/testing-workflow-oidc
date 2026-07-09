import base64
import calendar
import xlsxwriter
from datetime import datetime, timedelta, date
from io import BytesIO

from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
from odoo.tools import SQL


class ProgressPbt(models.TransientModel):
    _name = "tw.progress.pbt.report"
    _description = "Progress PBT Report"
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
        worksheet = workbook.add_worksheet('Report Summary Progress Unit & PBT')

        worksheet.set_column('B1:B1', 15)
        worksheet.set_column('C1:C1', 20)
        worksheet.set_column('D1:D1', 20)
        worksheet.set_column('E1:E1', 20)
        worksheet.set_column('F1:F1', 20)
        worksheet.set_column('G1:G1', 20)
        worksheet.set_column('H1:H1', 20)

        
        user_id = self.env['res.users'].search([('id','=',self._uid)])
        user = user_id.name 
        company = user_id.company_id.name
        filename = 'Report Summary Progress Unit & PBT' + str(self.start_date)+'.xlsx'

        # branch = self.company_ids or self.env.user.company_ids
        # branch_list = str(tuple([b.id for b in branch])).replace(',)', ')')

        query = SQL("""
                SELECT branch.code AS code_branch
                        , branch.name AS branch_name
                        , am.name AS am
                        , (CASE 
                            WHEN margin.state ISNULL and margin_line.am_state ISNULL THEN 'Not Done'
                            ELSE 'Done'
                        END) AS submit_kacab
                        , INITCAP(margin.state) AS gm_state
                        , INITCAP((CASE
                            WHEN margin_line.am_state like '%%draft%' THEN 'Draft'
                            ELSE 'Approve'
                        END)) AS am_state
                        , (CASE 
                            WHEN master_margin.company_id ISNULL THEN 'Not Go Live'
                            ELSE 'Go Live'
                        END) AS master_margin
                FROM res_company branch
                LEFT JOIN tw_profit_before_tax margin ON branch.id = margin.company_id
                LEFT JOIN hr_employee am ON am.id = margin.area_manager_id
                LEFT JOIN (
                    SELECT net_margin_id
                        , STRING_AGG(state, ', ') AS am_state
                    FROM tw_profit_before_tax_line
                    GROUP BY net_margin_id
                ) AS margin_line ON margin.id = margin_line.net_margin_id
                LEFT JOIN (
                    SELECT company_id
                    FROM tw_master_target_margin
                    WHERE state = 'active'
                    AND job = 'sales'
                    AND date BETWEEN %(start_date)s AND %(end_date)s
                ) AS master_margin ON master_margin.company_id = branch.id
                WHERE branch.is_tdm is TRUE
                AND margin.start_date >= %(start_date)s
                AND margin.end_date <=  %(end_date)s
            """, start_date=self.start_date, end_date=self.end_date)
        
        self.env.cr.execute(query)
        ress = self.env.cr.dictfetchall()
        if not ress:
            raise Warning("Tidak ada data.")
        
        worksheet.merge_range('A1:D1', company , wbf['company'])
        worksheet.merge_range('A2:D2', 'Report Summary Progress Unit & PBT' , wbf['company'])
        worksheet.merge_range('A3:D3', f'Tanggal {self.start_date} s/d {self.end_date}' , wbf['company'])
        
        row = 5
        worksheet.set_row(row + 1, 25)
        worksheet.merge_range('A%s:A%s' % (row+1, row+2), 'No' , wbf['header_left'])
        worksheet.merge_range('B%s:B%s' % (row+1, row+2), 'Kode Cabang' , wbf['header'])
        worksheet.merge_range('C%s:C%s' % (row+1, row+2), 'Nama Cabang' , wbf['header'])
        worksheet.merge_range('D%s:D%s' % (row+1, row+2), 'Area Manager' , wbf['header'])
        worksheet.merge_range('E%s:E%s' % (row+1, row+2), 'Submit Kacab' , wbf['header'])
        worksheet.merge_range('F%s:G%s' % (row+1, row+1), 'Approval' , wbf['header'])
        worksheet.write('F%s' % (row+2), 'AM' , wbf['header'])
        worksheet.write('G%s' % (row+2), 'GM' , wbf['header'])
        worksheet.merge_range('H%s:H%s' % (row+1, row+2), 'Status' , wbf['header'])

        row+=3       
        no = 1
       
        if ress == []:
            worksheet.merge_range('A%s:H%s' % (row,row), 'Data tidak ada !' , wbf['content'])
            
        for res in ress:
            branch = res.get('branch_name')
            branch_code = res.get('code_branch')
            area_manager = res.get('am')
            submit_kacab = res.get('submit_kacab')
            am_state = res.get('am_state')
            gm_state = res.get('gm_state')
            status = res.get('master_margin')
            
            worksheet.write(f'A{row}', no , wbf['content_left']) 
            worksheet.write(f'B{row}', branch_code , wbf['content']) 
            worksheet.write(f'C{row}', branch , wbf['content'])
            worksheet.write(f'D{row}', area_manager , wbf['content'])
            worksheet.write(f'E{row}', submit_kacab, wbf['content'])
            worksheet.write(f'F{row}', am_state, wbf['content'])
            worksheet.write(f'G{row}', gm_state, wbf['content'])
            worksheet.write(f'H{row}', status, wbf['content_float'])
            no += 1 
            row += 1     

        worksheet.autofilter(f'B6:H{row}') 
        worksheet.freeze_panes(6, 3)
        worksheet.merge_range(f'A{row+2}:E{row+2}', f'{(datetime.now() + timedelta(hours=7)).isoformat()}, {user}' , wbf['footer']) 
        
        workbook.close()
        out=base64.encodestring(fp.getvalue())
        self.data_x = out
        self.file = filename
        
        fp.close()
        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': '/web/content/tw.progress.pbt.report/%s/data_x/%s?download=true' % (self.id, filename)
        } 
    