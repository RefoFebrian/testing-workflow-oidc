# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
import tempfile
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta
# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError

# 5: local imports

# 6: Import of unknown third party lib

class TWReportNrfsGoogleDrive(models.Model):
    _inherit = "tw.report.google.drive"

    def generate_excel_nrfs(self):
        today = (datetime.now() + relativedelta(hours=7)).date()
        start_date = today.replace(day=1).strftime("%Y-%m-%d")
        end_date = today.strftime("%Y-%m-%d")
        datas = self.env['tw.nrfs.report']._generate_excel_buffer_nrfs(start_date=start_date, end_date=end_date, state=None, include_not_done=True)
        temp_dir = False
        if datas:
            temp_dir = tempfile.gettempdir()
            local_path = temp_dir+'/'+datas[1]
            f = open(local_path,"w+b")
            f.write(datas[0].getvalue())
            datas[0].close()
            tw_file_obj = self.create({'name': datas[1], 'tipe': 'Report Nrfs Md'})
        return {'temp_dir':temp_dir, 'filename':datas[1], 'tw_file_obj': tw_file_obj}
    
    def send_file_report_nrfs(self):
        config_obj = self.env['tw.report.google.drive.config.line'].search([('tipe','=','Report Nrfs Md')],limit=1)
        if not config_obj:
            raise Warning('Konfigurasi folder GDrive untuk tipe NRFS tidak ditemukan!')
        file_obj = self.generate_excel_nrfs()
        temp_dir = file_obj.get('temp_dir')
        filename = file_obj.get('filename')
        tw_file_obj = file_obj.get('tw_file_obj')
        if temp_dir:
            path = temp_dir+'/'+filename
            today = datetime.now() + relativedelta(hours=7)
            nama_file = 'Report NRFS TDM ' + today.strftime("%m%Y") + '.xlsx'
            gdrive_file_id = {'id': ''}
            
            config = self._get_google_drive_config_old()
            folder = self._get_google_drive_folder_old(config, 'Report Nrfs Md')
            
            if today.day == 1: # Awal bulan: upload baru
                gdrive_file_id = self.google_upload(nama_file, path, folder, config=config)
            else: # Bukan awal bulan: update file
                gdrive_file_id['id'] = self.search([('tipe','=','Report Nrfs Md'),('id','!=',tw_file_obj.id)], order="id desc", limit=1).gdrive_file_id
                if gdrive_file_id['id']:
                    self.google_upload(nama_file, path, folder, "update", gdrive_file_id['id'], config=config)
                else: # Bukan awal bulan: upload baru (mestinya hanya eksekusi sekali)
                    gdrive_file_id = self.google_upload(nama_file, path, folder, config=config)
            tw_file_obj.suspend_security().write({'gdrive_file_id': str(gdrive_file_id['id'])})