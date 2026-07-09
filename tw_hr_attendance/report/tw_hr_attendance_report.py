 # -*- coding: utf-8 -*-

# 1: imports of python lib
from io import StringIO,BytesIO
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from xlsxwriter.utility import xl_rowcol_to_cell
from lxml import etree
from pytz import timezone
import logging
import re
import pytz
import time
import xlsxwriter
import base64
import tempfile
import os

# 2: import of known third party lib

# 3: import of odoo
from odoo import models, fields, api, _

# 4: import from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwHrAttendanceReport(models.TransientModel):
    _name = "tw.hr.attendance.report"
    _description = "TW Report HR Attendance"

    # 7: defaults methods
    def _get_default_date(self):
        return datetime.now()
        
    def _get_default_start_date(self):
        return date.today().replace(day=1)

    # 8: fields
    wbf = {}
    name = fields.Char('Filename', readonly=True)
    state_x = fields.Selection( ( ('choose','choose'),('get','get')),default=lambda *a: 'choose')
    data_x = fields.Binary('File', readonly=True)
    start_date = fields.Date('Start Date',default=_get_default_start_date)
    end_date = fields.Date('End Date',default=_get_default_date)

    # 9: relation fields
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee',domain=[('id','!=','1')])
    department_ids = fields.Many2many('hr.department', 'dms_report_attendance_department_rel', 'dms_report_attendance_wizard_id', 'department_id', 'Department', copy=False)

    # 10: compute/depends & on change methods
    @api.onchange('department_ids')
    def _onchange_department_ids(self):
        self.employee_id =False
        domain = {'employee_id':[('id','!=','1')]}
        if self.department_ids:
            domain = {'employee_id':[('department_id','in',[d.id for d in self.department_ids])]}
        return {'domain':domain}

	# 12: override methods
    
	# 13: action methods
    def action_export(self):
        query_where = " WHERE 1=1 AND he.id != 1"
        if self.department_ids:
            department = [d.id for d in self.department_ids]
            query_where +=" AND dept.id in %s" % (str(tuple(department)).replace(',)', ')'))
        if self.employee_id:
            query_where += " AND he.id = '%s'" % str(self.employee_id.id)

        query = """
            SELECT 
                att.*
            FROM (
                    SELECT
                    date_trunc('day', dd)::date AS tanggal
                    FROM generate_series
                    ( '%s'::timestamp
                    , '%s'::timestamp
                    , '1 day'::interval) dd
                    ) series
            LEFT JOIN LATERAL 
                            (
                                SELECT
                                    he.identification_id AS nik
                                    , he.name AS nama_karyawan
                                    , dept.name->>'en_US' AS department
                                    , CASE
                                        WHEN EXTRACT(ISODOW FROM series.tanggal) = 1
                                            THEN 'Senin'
                                        WHEN EXTRACT(ISODOW FROM series.tanggal) = 2
                                            THEN 'Selasa'
                                        WHEN EXTRACT(ISODOW FROM series.tanggal) = 3
                                            THEN 'Rabu'
                                        WHEN EXTRACT(ISODOW FROM series.tanggal) = 4
                                            THEN 'Kamis'
                                        WHEN EXTRACT(ISODOW FROM series.tanggal) = 5
                                            THEN 'Jumat'
                                        WHEN EXTRACT(ISODOW FROM series.tanggal) = 6
                                            THEN 'Sabtu'
                                        WHEN EXTRACT(ISODOW FROM series.tanggal) = 7
                                            THEN 'Minggu'
                                        END AS hari
                                    , series.tanggal::varchar
                                    , default_company.name AS default_location
                                    , wp_in.name AS location_in
                                    , TO_CHAR(attendance.check_in + INTERVAL '7 hours','HH24:MI:SS') AS check_in
                                    , attendance.check_in + INTERVAL '7 hours' AS check_in_date
                                    , CASE WHEN EXTRACT(ISODOW FROM series.tanggal) = 7
                                         THEN 'Tidak'
                                         ELSE
                                            CASE WHEN (CAST((TO_CHAR(attendance.check_in ,'HH24MI')) AS INTEGER) > 0800) OR attendance.check_in IS NULL
                                                 THEN 'Timekeeping'
                                                 ELSE 'Tidak'
                                                 END
                                         END AS status_in
                                    , wp_out.name AS location_out
                                    , TO_CHAR(attendance.check_out + INTERVAL '7 hours','HH24:MI:SS') AS check_out
                                    , attendance.check_out + INTERVAL '7 hours' AS check_out_date
                                    , CASE WHEN EXTRACT(ISODOW FROM series.tanggal) = 7
                                         THEN 'Tidak'
                                         ELSE    
                                            CASE WHEN EXTRACT(ISODOW FROM series.tanggal) = 6
                                            THEN
                                              CASE WHEN (CAST((TO_CHAR(attendance.check_out,'HH24')) AS INTEGER) < 14) OR attendance.check_out IS NULL
                                              THEN 'Timekeeping'
                                              ELSE 'Tidak'
                                              END
                                            ELSE
                                              CASE WHEN (CAST((TO_CHAR(attendance.check_out,'HH24')) AS INTEGER) < 16) OR attendance.check_out IS NULL
                                              THEN 'Timekeeping'
                                              ELSE 'Tidak'
                                              END
                                            END
                                         END AS status_out
                                FROM hr_employee he
                                LEFT JOIN hr_department AS dept ON dept.id = he.department_id
                                LEFT JOIN tw_attendance attendance ON attendance.employee_id = he.id
                                    AND date_trunc('day', attendance.check_in + INTERVAL '7 hours')::date = series.tanggal
                                LEFT JOIN res_company AS wp_in ON wp_in.id = attendance.workplace_in_id
                                LEFT JOIN res_company AS wp_out ON wp_out.id = attendance.workplace_out_id
                                LEFT JOIN res_company AS default_company ON default_company.id = he.company_id
                                %s
                                AND he.active 
                                AND he.working_end_date IS NULL
                                ORDER BY attendance.id ASC
                            ) att ON TRUE
            WHERE 1=1
            """ %(self.start_date, self.end_date, query_where)
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        if not ress:
            raise Warning('Data tidak ada!')
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp)        
        workbook = self.add_workbook_format(workbook)
        wbf = self.wbf
        
        worksheet = workbook.add_worksheet('Attendance Report')
        worksheet.set_column('B1:B1', 25)
        worksheet.set_column('C1:C1', 25)
        worksheet.set_column('D1:D1', 25)
        worksheet.set_column('E1:E1', 10)
        worksheet.set_column('F1:F1', 12)
        worksheet.set_column('G1:G1', 20)
        worksheet.set_column('H1:H1', 10)
        worksheet.set_column('I1:I1', 20)
        worksheet.set_column('J1:J1', 20)
        worksheet.set_column('K1:K1', 10)
        worksheet.set_column('L1:L1', 20)
                        
        date = self._get_default_date()
        date = date.strftime("%Y-%m-%d %H:%M:%S")
        user = self.env['res.users'].sudo().browse([self._uid]).name
        
        filename = 'Attendance Report'+' '+str(date)+'.xlsx'
        worksheet.merge_range('A2:L2', 'DATA SUMMARY ABSENSI '+str(self.start_date)+' - '+str(self.end_date), wbf['title_doc'])
        worksheet.merge_range('A3:L3', 'HONDA MAIN DEALER (PUSAT)' , wbf['title_doc'])
        row=4

        worksheet.write('A%s' % (row+1), 'No' , wbf['header'])
        worksheet.write('B%s' % (row+1), 'NIK' , wbf['header'])
        worksheet.write('C%s' % (row+1), 'NAMA KARYAWAN' , wbf['header'])
        worksheet.write('D%s' % (row+1), 'DEPARTMENT' , wbf['header'])
        worksheet.write('E%s' % (row+1), 'HARI' , wbf['header'])
        worksheet.write('F%s' % (row+1), 'DATE' , wbf['header'])
        worksheet.write('G%s' % (row+1), 'LOCATION IN' , wbf['header'])
        worksheet.write('H%s' % (row+1), 'IN' , wbf['header'])
        worksheet.write('I%s' % (row+1), 'STATUS' , wbf['header'])
        worksheet.write('J%s' % (row+1), 'LOCATION OUT' , wbf['header'])
        worksheet.write('K%s' % (row+1), 'OUT' , wbf['header'])
        worksheet.write('L%s' % (row+1), 'STATUS' , wbf['header'])
        no = 1
        row += 2
        for res in ress:
            nik = str(res['nik']) if res.get('nik') else ''
            nama_karyawan = str(res['nama_karyawan']) if res.get('nama_karyawan') else ''
            department = str(res['department']) if res.get('department') else ''
            hari = str(res['hari']) if res.get('hari') else ''
            tanggal = str(res['tanggal']) if res.get('tanggal') else ''
            default_location = str(res['default_location']) if res.get('default_location') else ''
            location_in = str(res['location_in']) if res.get('location_in') else default_location
            check_in = str(res['check_in']) if res.get('check_in') else ''
            status_in = str(res['status_in']) if res.get('status_in') else ''
            location_out = str(res['location_out']) if res.get('location_out') else default_location
            check_out = str(res['check_out']) if res.get('check_out') else ''
            status_out = str(res['status_out']) if res.get('status_out') else ''

            worksheet.write('A%s' % row, no , wbf['content_number'])      
            worksheet.write('B%s' % row, nik , wbf['content'])
            worksheet.write('C%s' % row, nama_karyawan , wbf['content'])
            worksheet.write('D%s' % row, department , wbf['content'])
            worksheet.write('E%s' % row, hari , wbf['content'])
            worksheet.write('F%s' % row, tanggal , wbf['content'])
            worksheet.write('G%s' % row, location_in , wbf['content'])
            worksheet.write('H%s' % row, check_in , wbf['content_absen'])
            worksheet.write('I%s' % row, status_in , wbf['content'])
            worksheet.write('J%s' % row, location_out , wbf['content'])
            worksheet.write('K%s' % row, check_out , wbf['content_absen'])
            worksheet.write('L%s' % row, status_out , wbf['content'])
            no+=1
            row+=1

        format1 = workbook.add_format({'bg_color': '#ffa500',
                                    'font_color': '#ffa500'})
        worksheet.conditional_format('H6:H%s' %row, {'type':     'text',
                                       'criteria': 'containing',
                                       'value':    'minggu',
                                       'format':   format1})
        worksheet.conditional_format('K6:K%s' %row, {'type':     'text',
                                       'criteria': 'containing',
                                       'value':    'minggu',
                                       'format':   format1})

        worksheet.merge_range('A%s:L%s' % (row,row), '', wbf['foot'])
        worksheet.write('A%s'%(row+2), '%s %s' % (str(date),user) , wbf['footer'])  
        workbook.close()
        out=base64.encodebytes(fp.getvalue())
        self.write({ 'data_x':out, 'name': filename})
        fp.close()

        return {
            'type': 'ir.actions.act_url',
            'name': 'Attendance Report',
            'url': '/web/content/tw.hr.attendance.report/%s/data_x/%s?download=true' % (self.id, filename),
        }

	# 14: private methods

    def add_workbook_format(self,workbook):
        self.wbf['header'] = workbook.add_format({'bold': 1,'align': 'center','bg_color': '#d9d9d9','font_color': '#000000','valign': 'center'})
        self.wbf['header'].set_border()
        self.wbf['header'].set_align('center')
        self.wbf['header'].set_align('vcenter')

        self.wbf['header_no'] = workbook.add_format({'bold': 1,'align': 'center','bg_color': '#FFFFDB','font_color': '#000000'})
        self.wbf['header_no'].set_border()
        self.wbf['header_no'].set_align('vcenter')
                
        self.wbf['footer'] = workbook.add_format({'align':'left'})
        
        self.wbf['content_datetime'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm:ss'})
        self.wbf['content_datetime'].set_left()
        self.wbf['content_datetime'].set_right()
        
        self.wbf['content_datetime_12_hr'] = workbook.add_format({'num_format': 'yyyy-mm-dd hh:mm AM/PM'})
        self.wbf['content_datetime_12_hr'].set_left()
        self.wbf['content_datetime_12_hr'].set_right()        
                
        self.wbf['content_date'] = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        self.wbf['content_date'].set_left()
        self.wbf['content_date'].set_right() 
        
        self.wbf['title_doc'] = workbook.add_format({'bold': 1,'align': 'center'})
        self.wbf['title_doc'].set_font_size(12)

        self.wbf['title_doc_unsuplied'] = workbook.add_format({'bold': 1})
        self.wbf['title_doc_unsuplied'].set_font_size(12)
        self.wbf['title_doc_unsuplied'].set_top()
        self.wbf['title_doc_unsuplied'].set_bottom()            
        self.wbf['title_doc_unsuplied'].set_left()
        self.wbf['title_doc_unsuplied'].set_right()    

        self.wbf['title_doc_blue'] = workbook.add_format({'bold': 1,'align': 'center','bg_color':'#00ffff'})
        self.wbf['title_doc_blue'].set_font_size(12)
        
        self.wbf['company'] = workbook.add_format({'align': 'left'})
        self.wbf['company'].set_font_size(11)
        
        self.wbf['content'] = workbook.add_format()
        self.wbf['content'].set_left()
        self.wbf['content'].set_right() 

        self.wbf['content_absen'] = workbook.add_format({'bg_color':'33ff66'})
        self.wbf['content_absen'].set_left()
        self.wbf['content_absen'].set_right() 
        
        self.wbf['content_float'] = workbook.add_format({'align': 'right','num_format': '#,##0.00'})
        self.wbf['content_float'].set_right() 
        self.wbf['content_float'].set_left()

        self.wbf['content_center'] = workbook.add_format({'align': 'centre'})
        
        self.wbf['content_number'] = workbook.add_format({'align': 'right'})
        self.wbf['content_number'].set_right() 
        self.wbf['content_number'].set_left() 
                
        self.wbf['content_percent'] = workbook.add_format({'align': 'right','num_format': '0.00%'})
        self.wbf['content_percent'].set_right() 
        self.wbf['content_percent'].set_left() 
                
        self.wbf['total_float'] = workbook.add_format({'bold':1,'bg_color': '#ffff00','align': 'right','num_format': '#,##0.00'})
        self.wbf['total_float'].set_top()
        self.wbf['total_float'].set_bottom()            
        self.wbf['total_float'].set_left()
        self.wbf['total_float'].set_right()         
        
        self.wbf['total_number'] = workbook.add_format({'align':'right','bg_color': '#FFFFDB','bold':1})
        self.wbf['total_number'].set_top()
        self.wbf['total_number'].set_bottom()            
        self.wbf['total_number'].set_left()
        self.wbf['total_number'].set_right()
        
        self.wbf['foot'] = workbook.add_format({'align':'right','bold':1})
        self.wbf['foot'].set_top()            
        
        self.wbf['total'] = workbook.add_format({'bold':1,'bg_color': '#FFFFDB','align':'center'})
        self.wbf['total'].set_left()
        self.wbf['total'].set_right()
        self.wbf['total'].set_top()
        self.wbf['total'].set_bottom()
        
        return workbook
