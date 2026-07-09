import xlsxwriter
from io import StringIO,BytesIO
import base64
import os
from odoo import models, fields, api
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
import calendar
from odoo.exceptions import UserError as Warning

class ReportRegisterKwitansi(models.TransientModel):
    _name = "tw.report.register.kwitansi"
    _description = "TW Report Register Kwitansi"

    def _get_tahun(self):
        return datetime.today().date().year
 
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
    company_ids = fields.Many2many('res.company', string='Branch')


    def excel_report(self):
        bulan = int(self.bulan)
        tahun = int(self.tahun)
        nama_bln = calendar.month_name[bulan]

        filename = 'Report_Register_Kwitansi_' + str(bulan) + '_' + str(tahun) + '.xlsx'

        start_date = date(tahun, bulan, 1)
        end_date = start_date + relativedelta(months=1) - relativedelta(days=1)
        
        query = f"""
            SELECT
            rc.name as branch
            ,rkl.name
            ,rkl.state
            ,rkl.type
            ,rkl.reason
            FROM tw_register_kwitansi_line rkl
            LEFT JOIN res_company rc on rc.id = rkl.company_id
            WHERE (rkl.create_date + INTERVAL '7 hours')::DATE BETWEEN %s and %s
            AND rkl.company_id IN %s
        """
        self._cr.execute(query,(start_date,end_date,tuple(self.company_ids.ids),))

        ress = self._cr.dictfetchall()
        if not ress:
            raise Warning("Data Register Kwitansi tidak ada pada Periode %s %s" % (self.bulan,self.tahun))

        return self.env['web.report'].sudo().generate_report('Report Register Kwitansi',ress)
