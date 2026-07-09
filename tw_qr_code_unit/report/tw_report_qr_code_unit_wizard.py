# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
import pytz
import base64
import csv
import xlsxwriter
import calendar
from io import StringIO,BytesIO
from datetime import date, datetime, time, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib
class TedsReportQrCodeUnitWizard(models.TransientModel):
    _name = "tw.report.qr.code.unit"
    _description = "Report QR Code Unit"

    def _get_default_date(self): 
        return datetime.now()
    
    name = fields.Char('File Name')
    start_date = fields.Date('Start Date', default=_get_default_date)
    end_date = fields.Date('End Date', default=_get_default_date)
    options = fields.Selection([
        ('printed_date','Printed Date'), 
        ('generate_date','Generated Date')], string="Based On", default='generate_date', help="Based on which date you want to filter the report")
    state = fields.Selection([
        ('New', 'New'),
        ('Printed', 'Printed'),
        ('Linked', 'Linked'),
        ('ALL', 'ALL'),
    ], string='Status', default='New')
    
    def generate_data(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query_where = "WHERE 1=1"
        if self.state == 'ALL':
            query_where += " AND qr.state IN ('New', 'Printed', 'Linked')"
        else:
            query_where += f" AND qr.state = '{self.state}'"

        if self.options == 'printed_date':
            query_where += f" AND qr.printed_date BETWEEN '{self.start_date} 00:00:00' AND '{self.end_date} 23:59:59'"
        else:
            query_where += f" AND qr.date BETWEEN '{self.start_date}' AND '{self.end_date}'"
            
        query = f"""
            SELECT qr.name as kode_unik
                , lot.name as serial_number
                , qr.date as tanggal_generate
                , qr.printed_date as tanggal_cetak
                , qr.state as status
            FROM tw_qr_code_unit qr
            LEFT JOIN stock_lot lot ON lot.id = qr.lot_id
            {query_where}
        """
        
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        filename = f"Report QR Code Unit_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.xlsx"
        self.suspend_security().write({'name' : filename})
        return self.env['web.report'].sudo().generate_report('Report QR Code Unit',ress)
    
