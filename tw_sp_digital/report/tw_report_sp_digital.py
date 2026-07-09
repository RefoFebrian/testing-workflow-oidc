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


def _get_range_of_month_or_year(type='month'):
    if type == 'year':
        return [(str(num), str(num)) for num in range(2010, (datetime.now().year)+1)]
    return [(str(idx), str(calendar.month_name[idx])) for idx in range(1, 13)]

class EmployeeReportSpDigital(models.TransientModel):
    _name = "tw.report.sp.digital"
    _description = 'Report SP Digital'

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    wbf = {}

    # 8: fields
    name = fields.Char('Filename', readonly=True)
    state_x = fields.Selection((
        ('choose', 'choose'),
        ('get', 'get')
    ), default=lambda *a: 'choose')
    tipe = fields.Selection(string='Tipe', selection=[
        ('summary', 'Summary'),
        ('detail', 'Detail')
    ], default='summary')
    
    start_month = fields.Selection(
        _get_range_of_month_or_year(),
        string='Start Month',
        default=str(datetime.now().month)
    )
    start_year = fields.Selection(
        _get_range_of_month_or_year(type='year'),
        string='Start Year',
        default=str(datetime.now().year)
    )
    end_month = fields.Selection(
        _get_range_of_month_or_year(),
        string='End Month',
        default=str(datetime.now().month)
    )
    end_year = fields.Selection(
        _get_range_of_month_or_year(type='year'),
        string='End Year',
        default=str(datetime.now().year)
    )

    data_x = fields.Binary('File', readonly=True)

    # 9: relation fields
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee')
    company_ids = fields.Many2many('res.company', 'report_sp_digital_company_rel', 'report_sp_digital_wizard_id', 'company_id', "Branch", copy=False, domain=[('parent_id','!=',False)])

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_report_sp_digital_tree(self):
        domain = []
        name = 'Laporan SP Digital'
        path = 'laporan-sp-digital'
        form_view_id = self.env.ref('tw_sp_digital.tw_report_sp_digital_wizard_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'tw.report.sp.digital',
            'domain': domain,
            'views': [(form_view_id, 'form')],
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1
            },
        }
    
    def add_workbook_format(self, workbook):
        self.wbf['header'] = workbook.add_format({'bold': 1, 'align': 'center', 'bg_color': '#d9d9d9', 'font_color': '#000000', 'valign': 'center'})
        self.wbf['header'].set_border()
        self.wbf['header'].set_align('center')
        self.wbf['header'].set_align('vcenter')

        self.wbf['header_no'] = workbook.add_format({'bold': 1, 'align': 'center', 'bg_color': '#FFFFDB', 'font_color': '#000000'})
        self.wbf['header_no'].set_border()
        self.wbf['header_no'].set_align('vcenter')
                
        self.wbf['footer'] = workbook.add_format({'align': 'left'})
        
        self.wbf['content_datetime'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
        self.wbf['content_datetime'].set_left()
        self.wbf['content_datetime'].set_right()
        
        self.wbf['content_datetime_12_hr'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm AM/PM'})
        self.wbf['content_datetime_12_hr'].set_left()
        self.wbf['content_datetime_12_hr'].set_right()        
                
        self.wbf['content_date'] = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        self.wbf['content_date'].set_left()
        self.wbf['content_date'].set_right() 
        
        self.wbf['title_doc'] = workbook.add_format({'bold': 1, 'align': 'center'})
        self.wbf['title_doc'].set_font_size(12)

        self.wbf['title_doc_unsuplied'] = workbook.add_format({'bold': 1})
        self.wbf['title_doc_unsuplied'].set_font_size(12)
        self.wbf['title_doc_unsuplied'].set_top()
        self.wbf['title_doc_unsuplied'].set_bottom()            
        self.wbf['title_doc_unsuplied'].set_left()
        self.wbf['title_doc_unsuplied'].set_right()    

        self.wbf['title_doc_blue'] = workbook.add_format({'bold': 1, 'align': 'center', 'bg_color':'#00ffff'})
        self.wbf['title_doc_blue'].set_font_size(12)
        
        self.wbf['company'] = workbook.add_format({'align': 'left'})
        self.wbf['company'].set_font_size(11)
        
        self.wbf['content'] = workbook.add_format()
        self.wbf['content'].set_left()
        self.wbf['content'].set_right() 

        self.wbf['content_absen'] = workbook.add_format({'bg_color': '33ff66'})
        self.wbf['content_absen'].set_left()
        self.wbf['content_absen'].set_right() 
        
        self.wbf['content_float'] = workbook.add_format({'align': 'right', 'num_format': '#,##0.00'})
        self.wbf['content_float'].set_right() 
        self.wbf['content_float'].set_left()

        self.wbf['content_center'] = workbook.add_format({'align': 'centre'})
        
        self.wbf['content_number'] = workbook.add_format({'align': 'right'})
        self.wbf['content_number'].set_right() 
        self.wbf['content_number'].set_left() 
                
        self.wbf['content_percent'] = workbook.add_format({'align': 'right', 'num_format': '0.00%'})
        self.wbf['content_percent'].set_right() 
        self.wbf['content_percent'].set_left() 
                
        self.wbf['total_float'] = workbook.add_format({'bold': 1, 'bg_color': '#ffff00', 'align': 'right', 'num_format': '#,##0.00'})
        self.wbf['total_float'].set_top()
        self.wbf['total_float'].set_bottom()            
        self.wbf['total_float'].set_left()
        self.wbf['total_float'].set_right()         
        
        self.wbf['total_number'] = workbook.add_format({'align': 'right', 'bg_color': '#FFFFDB', 'bold': 1})
        self.wbf['total_number'].set_top()
        self.wbf['total_number'].set_bottom()            
        self.wbf['total_number'].set_left()
        self.wbf['total_number'].set_right()
        
        self.wbf['foot'] = workbook.add_format({'align': 'right', 'bold': 1})
        self.wbf['foot'].set_top()            
        
        self.wbf['total'] = workbook.add_format({'bold': 1, 'bg_color': '#FFFFDB', 'align': 'center'})
        self.wbf['total'].set_left()
        self.wbf['total'].set_right()
        self.wbf['total'].set_top()
        self.wbf['total'].set_bottom()
        
        return workbook

    def action_export(self):
        additional_where = ''
        if self.company_ids:
            company_ids = [c.id for c in self.company_ids]
            additional_where += ' AND company.id IN {company_ids}'.format(company_ids=str(tuple(company_ids)).replace(',)', ')'))
        else:
            company = self.env.user._get_company_ids()
            additional_where += f" AND company.id IN {str(tuple(company)).replace(',)', ')')}"

        if self.employee_id:
            additional_where += f" AND emp.id = '{str(self.employee_id.id)}'"
        
        start_date = f'{self.start_year}-{self.start_month}-01'
        end_date_1 = f'{self.end_year}-{self.end_month}-01'
        end_date = (datetime.strptime(end_date_1, '%Y-%m-%d') + relativedelta(months=1) - relativedelta(days=1)).strftime('%Y-%m-%d')
        query = f"""
            SELECT 
                sp.name AS sp
                , company.name AS company
                , company.code AS company_code
                , emp.name AS employee_name
                , emp.registry_number AS employee_nip
                , job.name AS job
                , sp.sp_level AS sp_level 
                , INITCAP(sp.state) AS state
                , sp.date::VARCHAR AS date
                , sp.amount_denda::VARCHAR AS denda
                , TO_CHAR(TO_DATE (sp.month::text, 'MM'), 'Month') AS month
                , sp.year AS year
                , sp.alasan_reject AS alasan_reject
                , JSON_AGG(JSON_BUILD_OBJECT(
                    'name', spl.name,
                    'tipe', spl.type,
                    'sp_level', spl.sp_level,
                    'keterangan', spl.keterangan
                )::JSONB) AS sp_line
            FROM tw_sp_digital AS sp
            LEFT JOIN res_company AS company ON company.id = sp.company_id
            LEFT JOIN hr_employee emp ON emp.id = sp.employee_id
            LEFT JOIN hr_job AS job ON job.id = emp.job_id
            LEFT JOIN tw_sp_digital_line spl ON spl.sp_digital_id = sp.id
            WHERE 1=1
            AND sp.date BETWEEN '{start_date}' AND '{end_date}'
            {additional_where}
            GROUP BY sp.id, company.id, emp.id, job.id
            ORDER BY company.id, emp.id
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        if not ress:
            raise Warning('Data tidak ada!')
        
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)        
        workbook = self.add_workbook_format(workbook)
        wbf = self.wbf
        
        worksheet = workbook.add_worksheet('Sp Digital Monitoring Report')
        worksheet.set_column('B1:B1', 25)
        worksheet.set_column('C1:C1', 25)
        worksheet.set_column('D1:D1', 10)
        worksheet.set_column('E1:E1', 25)
        worksheet.set_column('F1:F1', 12)
        worksheet.set_column('G1:G1', 25)
        worksheet.set_column('H1:H1', 8)
        worksheet.set_column('I1:I1', 20)
        worksheet.set_column('J1:J1', 20)
        worksheet.set_column('K1:K1', 10)
        worksheet.set_column('L1:L1', 20)
        worksheet.set_column('M1:M1', 20)
        worksheet.set_column('N1:N1', 20)
        worksheet.set_column('O1:O1', 30)
        worksheet.set_column('P1:P1', 70)
        worksheet.set_column('Q1:Q1', 20)
        worksheet.set_column('R1:R1', 20)
        worksheet.set_column('S1:S1', 30)
                        
        raw_date = self._get_default_date()
        if isinstance(raw_date, str):
            date = raw_date
        else:
            date = raw_date.strftime("%Y-%m-%d %H:%M:%S")
        user = self.env['res.users'].sudo().browse([self._uid]).name
        
        filename = 'Sp Digital Report' + ' ' + str(date) + '.xlsx'
        worksheet.merge_range('A2:L2', 'DATA SUMMARY SP ' + str(start_date) + ' - ' + str(end_date), wbf['title_doc'])
        worksheet.merge_range('A3:L3', 'TUNAS HONDA' , wbf['title_doc'])
        row = 4

        worksheet.write('A%s' % (row+1), 'No' , wbf['header'])
        worksheet.write('B%s' % (row+1), 'SP' , wbf['header'])
        worksheet.write('C%s' % (row+1), 'Branch' , wbf['header'])
        worksheet.write('D%s' % (row+1), 'Branch code' , wbf['header'])
        worksheet.write('E%s' % (row+1), 'Nama' , wbf['header'])
        worksheet.write('F%s' % (row+1), 'NIP' , wbf['header'])
        worksheet.write('G%s' % (row+1), 'Job' , wbf['header'])
        worksheet.write('H%s' % (row+1), 'SP level ' , wbf['header'])
        worksheet.write('I%s' % (row+1), 'Date' , wbf['header'])
        worksheet.write('J%s' % (row+1), 'Month/Year' , wbf['header'])
        worksheet.write('K%s' % (row+1), 'Status' , wbf['header'])
        if self.tipe == 'detail':
            worksheet.write('L%s' % (row+1), 'Tipe' , wbf['header'])
            worksheet.write('M%s' % (row+1), 'Level detail' , wbf['header'])
            worksheet.write('N%s' % (row+1), 'Potongan Incentive' , wbf['header'])
            worksheet.write('O%s' % (row+1), 'Alasan Reject Deviasi' , wbf['header'])
            worksheet.write('P%s' % (row+1), 'Keterangan' , wbf['header'])
        no = 1
        row += 2
        for res in ress:
            sp = str(res['sp'].encode('ascii','ignore').decode('ascii')) if res['sp'] != None else ''
            branch = str(res['branch'].encode('ascii','ignore').decode('ascii')) if res['branch'] != None else ''
            branch_code = str(res['branch_code'].encode('ascii','ignore').decode('ascii')) if res['branch_code'] != None else ''
            employee_name = str(res['employee_name'].encode('ascii','ignore').decode('ascii')) if res['employee_name'] != None else ''
            employee_nip = str(res['employee_nip'].encode('ascii','ignore').decode('ascii')) if res['employee_nip'] != None else ''
            job = str(res['job'].encode('ascii','ignore').decode('ascii')) if res['job'] != None else ''
            sp_level = str(res['sp_level'].encode('ascii','ignore').decode('ascii')) if res['sp_level'] != None else ''
            date = str(res['date'].encode('ascii','ignore').decode('ascii')) if res['date'] != None else ''
            month = str(res['month'].encode('ascii','ignore').decode('ascii')) if res['month'] != None else ''
            year = str(res['year'].encode('ascii','ignore').decode('ascii')) if res['year'] != None else ''
            alasan_reject  = str(res['alasan_reject'].encode('ascii','ignore').decode('ascii')) if res['alasan_reject'] != None else ''
            denda = str(res['denda'].encode('ascii','ignore').decode('ascii')) if res['denda'] != None else ''
            state = str(res['state'].encode('ascii','ignore').decode('ascii')) if res['state'] != None else ''
            month_year = month + ' ' +year
            sp_line = res['sp_line']
            
            if self.tipe == 'summary':
                worksheet.write('A%s' % (row), no , wbf['content'])
                worksheet.write('B%s' % (row), sp , wbf['content'])
                worksheet.write('C%s' % (row), branch , wbf['content'])
                worksheet.write('D%s' % (row), branch_code , wbf['content'])
                worksheet.write('E%s' % (row), employee_name , wbf['content'])
                worksheet.write('F%s' % (row), employee_nip , wbf['content'])
                worksheet.write('G%s' % (row), job , wbf['content'])
                worksheet.write('H%s' % (row), sp_level , wbf['content'])
                worksheet.write('I%s' % (row), date , wbf['content'])
                worksheet.write('J%s' % (row), month_year , wbf['content'])
                worksheet.write('K%s' % (row), state , wbf['content'])
                worksheet.write('L%s' % (row), alasan_reject , wbf['content'])
                worksheet.write('M%s' % (row), denda , wbf['content'])
                row += 1
                no += 1
            
            if self.tipe == 'detail':
                for line in sp_line:
                    tipe = str(line['tipe'].encode('ascii','ignore').decode('ascii')) if line['tipe'] != None else ''
                    sp_level = str(line['sp_level'].encode('ascii','ignore').decode('ascii')) if line['sp_level'] != None else ''
                    keterangan = str(line['keterangan'].encode('ascii','ignore').decode('ascii')) if line['keterangan'] != None else ''
                    
                    worksheet.write('A%s' % (row), no , wbf['content'])
                    worksheet.write('B%s' % (row), sp , wbf['content'])
                    worksheet.write('C%s' % (row), branch , wbf['content'])
                    worksheet.write('D%s' % (row), branch_code , wbf['content'])
                    worksheet.write('E%s' % (row), employee_name , wbf['content'])
                    worksheet.write('F%s' % (row), employee_nip , wbf['content'])
                    worksheet.write('G%s' % (row), job , wbf['content'])
                    worksheet.write('H%s' % (row), sp_level , wbf['content'])
                    worksheet.write('I%s' % (row), date , wbf['content'])
                    worksheet.write('J%s' % (row), month_year , wbf['content'])
                    worksheet.write('K%s' % (row), state , wbf['content'])
                    worksheet.write('L%s' % (row), tipe , wbf['content'])
                    worksheet.write('M%s' % (row), sp_level , wbf['content'])
                    worksheet.write('N%s' % (row), denda , wbf['content'])
                    worksheet.write('O%s' % (row), alasan_reject , wbf['content'])
                    worksheet.write('P%s' % (row), keterangan , wbf['content'])
                    row += 1
                    no += 1

        worksheet.conditional_format('A6:P%s' %(row-1), {'type': 'blanks', 'format': wbf['content']})

        worksheet.merge_range('A%s:P%s' % (row,row), '', wbf['foot'])
        worksheet.write('A%s'%(row+2), '%s %s' % (str(date), user) , wbf['footer'])
        worksheet.autofilter('A5:P%s' % (row))
        workbook.close()
        out = base64.encodebytes(fp.getvalue())
        self.write({'data_x': out, 'name': filename})
        fp.close()

        return {
            'type': 'ir.actions.act_url',
            'name': 'contract',
            'url': '/web/content/tw.report.sp.digital/%s/data_x/%s?download=true' % (self.id, filename)
        }

    # 14: private methods