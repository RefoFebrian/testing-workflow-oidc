# -*- coding: utf-8 -*-

# 1: imports of python lib
import base64
import xlsxwriter
from io import StringIO,BytesIO
from datetime import date, datetime, time, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWB2BFilePSLReport(models.TransientModel):
    _name = "tw.b2b.file.psl.report"
    _description = "Laporan B2B File PSL"

    def _get_default_date(self): 
        return self.env['res.company'].get_default_date()

    name = fields.Char('Nama File', readonly=True)
    start_date = fields.Date('Start date', default=_get_default_date)
    end_date = fields.Date('End date', default=_get_default_date)
    
    def action_generate_report(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        query = f"""
            SELECT
            data.*,
            CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM tw_b2b_file tbf_psl
                    JOIN tw_b2b_file_content tbfc_psl ON tbfc_psl.file_id = tbf_psl.id
                    JOIN tw_b2b_file_content_line tbfcl_psl ON tbfcl_psl.file_content_id = tbfc_psl.id
                    WHERE tbf_psl.ext = 'PSL'
                    AND tbfcl_psl.name = 'kode_ps'
                    AND TRIM(tbfcl_psl.value) = data.kode_ps
                ) THEN 'on intransit'
                WHEN EXISTS (
                    SELECT 1
                    FROM stock_picking sp
                    WHERE sp.mft_reference = data.kode_ps
                    AND sp.state = 'done'
                ) THEN 'received by md'
                ELSE 'packed at ahm'
            END AS status
        FROM (
            SELECT
                tbf.name AS file_name,
                MAX(CASE WHEN tbfcl.name = 'kode_ps' THEN TRIM(tbfcl.value) END) AS kode_ps,
                MAX(CASE WHEN tbfcl.name = 'kode_dus' THEN TRIM(tbfcl.value) END) AS kode_dus,
                MAX(CASE WHEN tbfcl.name = 'kode_sparepart' THEN TRIM(tbfcl.value) END) AS kode_sparepart,
                MAX(CASE WHEN tbfcl.name = 'qty_po' THEN TRIM(tbfcl.value) END) AS qty_po,
                MAX(CASE WHEN tbfcl.name = 'qty_ps' THEN TRIM(tbfcl.value) END) AS qty_ps,
                MAX(CASE WHEN tbfcl.name = 'kode_po_md' THEN TRIM(tbfcl.value) END) AS kode_po_md
            FROM tw_b2b_file tbf
            JOIN tw_b2b_file_content tbfc ON tbfc.file_id = tbf.id
            JOIN tw_b2b_file_content_line tbfcl ON tbfcl.file_content_id = tbfc.id
            WHERE tbf.ext = 'PS'
            AND tbf.upload_date >= '{self.start_date}'
            AND tbf.upload_date <= '{self.end_date}'
            GROUP BY tbf.name
        ) data
        """
        self._cr.execute(query)
        ress = self._cr.dictfetchall()
        file_name = f"report_file_psl_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        if ress:
            self.suspend_security().write({'name': file_name})
        return self.env['web.report'].sudo().generate_report(file_name, ress)
    
