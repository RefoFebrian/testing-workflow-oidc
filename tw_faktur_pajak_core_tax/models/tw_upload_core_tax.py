from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
import base64
import xlrd
from datetime import date,datetime,timedelta
from dateutil.relativedelta import relativedelta
import logging
_logger = logging.getLogger(__name__)


class UploadCoreTax(models.TransientModel):
    _name = "tw.upload.core.tax"
    _description = "Upload Core Tax"

    
    
    file = fields.Binary('file')
    filename = fields.Char('Filename')
    upload_date = fields.Date(string='Tanggal Upload', default=date.today())
    state_x = fields.Selection([
        ('choose','choose'),
        ('get','get')
    ], default='choose')
    message = fields.Text(string='Message')

    
    def action_import(self):
        if not self.file:
            raise Warning('Silahkan input file terlebih dahulu.')
        self.action_import_xlsx()

        self.state_x = 'get'
        form_id = self.env.ref('tw_faktur_pajak_core_tax.tw_upload_core_tax_wizard').id
        return {
            'name': ('Upload eFaktur Coretax Wizard'),
            'res_model': 'tw.upload.core.tax',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_id': False,
            'views': [(form_id, 'form')],
            'target': 'current',
            'res_id': self.ids[0],
        }

    
    
    def action_import_xlsx(self):
        ext = self.filename.split('.')
        ext = ext[len(ext)-1].lower()
        if self.file:
            wb = xlrd.open_workbook(file_contents=base64.decodebytes(self.file))
        else:
            raise Warning("Pilih file untuk di upload terlebih dahulu!")
        
        if ext not in ('xls', 'xlsx'):
            raise Warning('Format %s tidak dikenal. Mohon gunakan format file yang sudah disediakan!\nKlik Download Contoh di sebelah kanan wizard untuk mengunduh.' % ext.upper())
        sheet = wb.sheet_by_index(0)
        
        success = 0
        pesan = ''
        msg = ''
        pesan_error = ''
        pesan_berhasil = ''
        for rx in range(3,sheet.nrows):
            values = [sheet.cell(rx, ry).value for ry in range(sheet.ncols)]
            no_efaktur = values[3]
            referensi = values[13]
            if not no_efaktur:
                continue 
            if no_efaktur and referensi:    
                check_fpo = self.env['tw.faktur.pajak.out'].search([('ref','=',referensi)])
                if not check_fpo:
                    pesan_error += "\n %s tidak ditemukan di data faktur pajak" % referensi
                    continue
                check_fpo.write({'name': no_efaktur,'state':'close'})
                pesan_berhasil += "\n %s dengan Referensi %s berhasil di update" % (no_efaktur,referensi)
                success += 1

        
        if pesan_error:
            msg += "\n \n silahkan periksa dokumen upload atau periksa format upload."
            self.write({
            'state_x': 'get',
            'message': msg + pesan_error
            })
            form_id = self.env.ref('tw_faktur_pajak_core_tax.tw_upload_core_tax_wizard').id
            return {
                'name': ('Upload E-Faktur Coretax'),
                'res_model': 'tw.upload.core.tax',
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_id': False,
                'views': [(form_id, 'form')],
                'target': 'current',
                'res_id': self.ids[0],
            }
        if success > 0:
            pesan += "\n %s Data Efaktur berhasil di update ke data Faktur Pajak Out" % success
            self.message = pesan + pesan_berhasil
        elif success == 0:
            msg += "\n \n tidak ada data yang diupdate."
            self.message = msg + pesan_error
