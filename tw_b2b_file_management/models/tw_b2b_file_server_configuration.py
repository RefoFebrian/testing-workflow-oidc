# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import datetime
from dateutil.relativedelta import relativedelta
import paramiko
if not hasattr(paramiko, 'DSSKey'):
    paramiko.DSSKey = paramiko.PKey  # Basic shim to prevent the ImportError, if causing error, remove this line and install -> pip install "paramiko<3.0.0"
import pysftp
import os

class MftFileServerConfiguration(models.Model):
    _inherit = "tw.api.configuration"

    port = fields.Integer(string='Port')
    folder_path_remote = fields.Char(string='Folder Path Remote')
    folder_path_local = fields.Char(string='Folder Path Local')
    
    config_options_id = fields.Many2one('tw.selection', string='Configuration Options' , domain=[('type','=','ServConfigOptions')])

    def send_sftp(self, path_file, remote_path=None):
        host = self.base_url
        user = self.username
        password = self.password
        remote_path = remote_path if remote_path else self.folder_path_remote
        port = self.port if self.port else 22

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        with pysftp.Connection(host, port=port, username=user, password=password, cnopts=cnopts) as sftp:
            sftp.chdir(remote_path)
            sftp.put(path_file)
            sftp.close()

    def send_data(self,filename,data):
        file_dir = self.folder_path_local
        local_path = file_dir+'/'+filename
        f= open(local_path,"wb+")
        f.write(data)
        f.close()

        if not self.options == 'AHM':
            self.send_sftp(local_path)

    def send_sftp_zip(self,path_extract,filename_zip=None):
        files = os.listdir(path_extract)
        host = self.base_url
        user = self.username
        password = self.password
        remote_path = self.folder_path_remote
        port = self.port if self.port else 22
        
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        with pysftp.Connection(host, port=port, username=user, password=password, cnopts=cnopts) as sftp:
            sftp.chdir(remote_path)
            for file in files:
                if file != filename_zip:
                    sftp.put(path_extract+'/'+file)
            sftp.close()

    def open_file_sftp(self,filename_ids):
        host = self.base_url
        username = self.username
        password = self.password
        remote_path = self.folder_path_remote
        port = self.port if self.port else 22
        file_content=[]
        
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        with pysftp.Connection(host, port=port, username=username, password=password, cnopts=cnopts) as sftp:
            sftp.chdir(remote_path)
            for filename in filename_ids:
                file = sftp.open(filename,'r')
                file_content.append({
                    'filename':filename,
                    'content':file.read().splitlines()
                })
        return file_content

    def get_file_sftp(self,filename):
        host = self.base_url
        username = self.username
        password = self.password
        remote_path = self.folder_path_remote
        local_path = self.folder_path_local
        port = self.port if self.port else 22
        
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        with pysftp.Connection(host, port=port, username=username, password=password, cnopts=cnopts) as sftp:
            sftp.get(remote_path+'\\'+filename, local_path+'/'+filename)

    def check_is_exists_file_sftp(self, path_file):
        host = self.base_url
        username = self.username
        password = self.password
        port = self.port if self.port else 22

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        with pysftp.Connection(host, port=port, username=username, password=password, cnopts=cnopts) as sftp:
            if sftp.exists(path_file):
                return True
            else:
                return False
            
    def execute_command_sftp(self, command):
        host = self.base_url
        username = self.username
        password = self.password
        port = self.port if self.port else 22

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        with pysftp.Connection(host, port=port, username=username, password=password, cnopts=cnopts) as sftp:
            results = sftp.execute(command)
            return results

    def get_sftp(self,start_date,end_date,extension,filename=None):
        host = self.base_url
        username = self.username
        password = self.password
        remote_path = self.folder_path_remote
        port = self.port if self.port else 22

        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None

        with pysftp.Connection(host, port=port, username=username, password=password, cnopts=cnopts) as sftp:
            file_ids=[]
            if filename:
                file_obj = sftp.execute('''dir /a-d /o-d '''+remote_path+''' |find \"'''+filename+'''\" ''')
            else:
                date = str()
                date_loop = start_date
                while date_loop <= end_date:
                    date += date_loop.strftime("%m/%d/%Y")+" "
                    date_loop = date_loop + relativedelta(days=1)
                file_obj = sftp.execute('''dir /a-d /o-d '''+remote_path+''' |findstr \"'''+date+'''\" |find \".'''+extension+'''\"''')
            
            for files in file_obj:
                file = files.split(" ")
                file_ids.append({
                    'upload_date':datetime.strptime(file[0], '%m/%d/%Y').strftime("%Y-%m-%d"),
                    'upload_time':file[2],
                    'filename':file[len(file)-1].replace("\r\n",""),
                })
            return file_ids