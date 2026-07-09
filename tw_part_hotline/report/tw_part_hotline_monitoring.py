import time 
import xlsxwriter
from io import StringIO
import base64
import tempfile
import os
from odoo import models, fields, api
from odoo.tools.translate import _
from datetime import datetime, timedelta,date
from dateutil.relativedelta import relativedelta
from xlsxwriter.utility import xl_rowcol_to_cell
import logging
import re
import pytz
import csv
import io
_logger = logging.getLogger(__name__)
from lxml import etree
from pytz import timezone
from odoo.exceptions import UserError as Warning

class MonitoringHotlineWizard(models.TransientModel):
    _name = "tw.part.hotline.monitoring.wizard"
    _description = "TW Part Hotline Monitoring Wizard"

    def _get_default_branch(self):
        company_ids = False
        company_ids = self.env.companies
        if company_ids and len(company_ids) == 1 :
            return [company_ids[0].id]
        return False
   
    def _get_default_date(self):
        return date.today()

    @api.depends('detail_ids')
    def cek_is_report(self):
        for record in self:
            if record.detail_ids:
                if len(record.detail_ids) > 0:
                    record.is_report = True
                else:
                    record.is_report = False
            else:
                record.is_report = False

    company_ids = fields.Many2many('res.company','tw_part_hotline_monitoring_rel', 'monitorind_id', 'company_id', 'Branch',default=_get_default_branch)
    is_report = fields.Boolean('Is Report',compute='cek_is_report')
    options = fields.Selection([
        ('periode','Periode'),
        ('hotline','No Hotline')])
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    no_hotline = fields.Char('No Hotline')

    file_data = fields.Binary('File Data')
    filename = fields.Char('Filename')

    detail_ids = fields.One2many('tw.part.hotline.monitoring.detail.wizard','monitoring_id')
    
    @api.onchange('no_hotline')
    def onchange_no_hotline(self):
        if self.no_hotline:
            self.no_hotline = self.no_hotline.strip().upper()
    
    @api.onchange('options')
    def onchange_optios(self):
        self.start_date = False
        self.end_date = False
        self.no_hotline = False
        if self.options == 'hotline':
            self.start_date = False
            self.end_date = False
        elif self.options == 'periode':
            self.no_hotline = False

    def action_search(self):
        self.env['web.report']._check_date_range_limit(self.start_date, self.end_date)

        self.detail_ids = False
        start_date = self.start_date
        end_date = self.end_date
        company_ids = self.company_ids
        no_hotline = self.no_hotline

        WHERE = " WHERE (hd.no_po IS NULL OR hd.no_wo IS NULL OR hd.no_ps IS NULL) AND h.state != 'cancel'"
        if self.options == 'periode':
            WHERE += " AND h.date >= '%s' AND h.date <= '%s'"%(start_date,end_date)
        elif self.options == 'hotline':            
            WHERE += " AND h.name = '%s'" %str(no_hotline)
        
        if company_ids:
            WHERE += " AND h.company_id in %s"%str(tuple([b.id for b in company_ids])).replace(',)', ')')

        query = """
            SELECT h.name as hotline
            , h.lot_id as lot_id
            , h.customer_id as customer_id
            , h.customer_name as customer_name
            , h.mobile as mobile
            , hd.product_id as product_id
            , hd.qty as hotline_qty
            , hd.no_po as po
            , hd.qty_available as po_qty
            , hd.no_wo as wo
            , hd.no_ps as ps
            , hd.qty_reserved as qty_reserved
            , CASE WHEN hd.no_po is not null THEN True ELSE False END as is_po
            , CASE WHEN hd.no_wo is not null THEN True ELSE False END as is_wo
            , CASE WHEN hd.no_ps is not null THEN True ELSE False END as is_ps
            , am.name || '(' ||hl.name|| ')' as hl
            , dp.amount_hl_allocation as amount
            , to_char(po.date_order,'YYYY-MM-DD') as po_date
            , h.date as tgl_hotline
            , COALESCE(date_part('days',now() - COALESCE(po.date_order,hd.po_date)),0) as umur
            FROM tw_part_hotline h
            INNER JOIN tw_part_hotline_detail hd ON hd.hotline_id = h.id
            LEFT JOIN tw_part_hotline_alocation_dp dp ON dp.hotline_id = h.id
            LEFT JOIN account_move_line hl ON hl.id = dp.hl_id
            LEFT JOIN account_move am ON am.id = hl.move_id
            LEFT JOIN purchase_order po ON po.part_hotline_id = h.id
            %s
            ORDER BY h.name,hd.no_po,hd.no_wo,hd.no_ps asc
        """ %(WHERE)
        self._cr.execute (query)
        ress =  self._cr.dictfetchall()

        datas = {}
        for res in ress:
            hotline = res.get('hotline')
            if not datas.get(hotline):
                datas[hotline] = {
                    'name': hotline,
                    'lot_id': res['lot_id'],
                    'customer_id': res['customer_id'],
                    'customer_name': res['customer_name'],
                    'mobile': res['mobile'],
                    'is_wo': res['is_wo'],
                    'is_po': res['is_po'],
                    'po_date':res['po_date'],
                    'tgl_hotline':res['tgl_hotline'],
                    'umur':int(res['umur']),
                    'line_ids': [
                        [0,False,{
                            'product_id':res['product_id'],
                            'qty':res['hotline_qty'],
                            'qty_reserved':res['qty_reserved'],
                            'qty_po':res['po_qty'],
                            'no_wo':res['wo'],
                            'no_ps':res['ps'],
                            'no_po':res['po'],
                  
                        }]
                    ]
                }
                if res.get('hl'):
                    datas[hotline]['dp_ids'] = [
                        [0,False,{
                            'name':res['hl'],
                            'amount_alokasi':res['amount']
                        }]
                    ]
                    datas[hotline]['hl_ids'] = [res['hl']]

                datas[hotline]['product_ids'] = [res['product_id']]
            else:
                if res['product_id'] not in datas[hotline]['product_ids']:
                    datas[hotline]['line_ids'].append([0,False,{
                        'product_id':res['product_id'],
                        'qty':res['hotline_qty'],
                        'qty_reserved':res['qty_reserved'],
                        'qty_po':res['po_qty'],                   
                        'no_wo':res['wo'],
                        'no_ps':res['ps'],
                        'no_po':res['po'],
                    }])
                    datas[hotline]['product_ids'].append(res['product_id'])
                
                if res.get('hl'):
                    if res['hl'] not in datas[hotline]['hl_ids']:
                        datas[hotline]['dp_ids'].append([0,False,{
                            'name':res['hl'],
                            'amount_alokasi':res['amount']    
                        }])
                        datas[hotline]['hl_ids'].append(res['hl'])
        ids = []
        for data in datas.values():
            # Hapus key helper yang bukan field model
            data.pop('product_ids', None)
            data.pop('hl_ids', None)
            ids.append([0,False,data])

        self.detail_ids = ids
    
    def action_xls(self):
        if not self.detail_ids:
            raise Warning('Silahkan Tekan Tombol Search Terlebih Dahulu.')
        
        result = []
        for detail in self.detail_ids:
            result.append({
                'No Hotline': detail.name,
                'No Engine': detail.lot_id.name or '',
                'No Chassis': detail.chassis_number or '',
                'No Polisi': detail.no_pol or '',
                'Customer': detail.customer_id.name or '',
                'customer_name': detail.customer_name or '',
                'No Telp': detail.mobile or '',
                'Sudah PO ?': 'Yes' if detail.is_po else 'No',
                'Sudah WO ?': 'Yes' if detail.is_wo else 'No',
                'Tgl Hotline': detail.tgl_hotline.strftime('%Y-%m-%d') if detail.tgl_hotline else '',
                'Tgl PO': detail.po_date.strftime('%Y-%m-%d') if detail.po_date else '',
                'Umur': detail.umur or '',
            })
        return self.env['web.report'].sudo().generate_report('Monitoring Part Hotline', result)
    
    def action_csv(self):
        if not self.detail_ids:
            raise Warning('Silahkan Tekan Tombol Search Terlebih Dahulu.')

        output = io.StringIO()
        writer = csv.writer(output, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow([
            'No Hotline', 'No Engine', 'No Chassis', 'No Polisi', 'Customer',
            'customer_name', 'No Telp', 'Sudah PO ?', 'Sudah WO ?',
            'Tgl Hotline', 'Tgl PO', 'Umur'
        ])

        # Isi CSV
        for detail in self.detail_ids:
            writer.writerow([
                detail.name,
                detail.lot_id.name or '',
                detail.chassis_number or '',
                detail.no_pol or '',
                detail.customer_id.name or '',
                detail.customer_name or '',
                detail.mobile or '',
                'Yes' if detail.is_po else 'No',
                'Yes' if detail.is_wo else 'No',
                detail.tgl_hotline.strftime('%Y-%m-%d') if detail.tgl_hotline else '',
                detail.po_date.strftime('%Y-%m-%d') if detail.po_date else '',
                detail.umur or '',
            ])

        # Encode CSV ke base64
        file_data = base64.b64encode(output.getvalue().encode('utf-8'))
        self.write({ 'file_data': file_data , 'filename': f'Report_Part_Hotline_{self.start_date}_sd_{self.end_date}.csv' })

        output.close()
        return {
            'type': 'ir.actions.act_url',
            'name': ('Download File'),
            'url': '/web/content/tw.part.hotline.monitoring.wizard/%s/file_data/%s?download=true' % (self.id, self.filename)
        }
    

class MonitoringHotlineDetailWizard(models.TransientModel):
    _name = "tw.part.hotline.monitoring.detail.wizard"
    _description = "TW Part Hotline Monitoring Detail Wizard"

    monitoring_id = fields.Many2one('tw.part.hotline.monitoring.wizard',ondelete='cascade')
    name = fields.Char('No Hotline')
    lot_id = fields.Many2one('stock.lot', 'No Engine')
    chassis_number = fields.Char('No Chassis',related='lot_id.chassis_number',readonly=True)
    no_pol = fields.Char('No Polisi',related='lot_id.plate_number',readonly=True)
    customer_id = fields.Many2one('res.partner','Customer')
    customer_name = fields.Char('customer_name')
    mobile = fields.Char('No Telp')
    line_ids = fields.One2many('tw.part.hotline.monitoring.detail.line.wizard','detail_id')
    dp_ids = fields.One2many('tw.part.hotline.monitoring.dp.wizard','detail_id')
    is_po = fields.Boolean('Sudah PO ?')
    is_wo = fields.Boolean('Sudah WO ?')
    tgl_hotline = fields.Date('Tgl Hotline')
    po_date = fields.Date('Tgl PO')
    umur = fields.Char('Umur')

class MonitoringHotlineDPWizard(models.TransientModel):
    _name = "tw.part.hotline.monitoring.dp.wizard"
    _description = "TW Part Hotline Monitoring DP Wizard"

    detail_id = fields.Many2one('tw.part.hotline.monitoring.detail.wizard',ondelete='cascade')
    name = fields.Char('Hutang Lain')
    amount_alokasi = fields.Float('Alokasi')

class MonitoringHotlineDetailLineWizard(models.TransientModel):
    _name = "tw.part.hotline.monitoring.detail.line.wizard"
    _description = "TW Part Hotline Monitoring Detail Line Wizard"

    detail_id = fields.Many2one('tw.part.hotline.monitoring.detail.wizard',ondelete='cascade')
    product_id = fields.Many2one('product.product','Product')
    name = fields.Char('Description',related="product_id.default_code",readonly=True)
    qty = fields.Float('Qty')
    qty_po = fields.Float('Qty PO')
    qty_reserved = fields.Float('Qty Reserved')
    no_wo = fields.Char('No WO')
    no_ps = fields.Char('No PS')
    no_po = fields.Char('No PO')
    





        
