# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
import base64
import os
import shutil
import platform
import subprocess
import logging
_logger = logging.getLogger(__name__)

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.exceptions import ValidationError
from odoo import models, fields, api, tools, _
from PIL import Image

# 5: local imports

# 6: Import of unknown third party lib

class ConfigFiles(models.Model):
    _name = "tw.config.files"
    _description = "Configuration of Saved Files"
    
    # 7: defaults methods

    # 8: fields
    name = fields.Char(string="Code", help="A Unique code to distinct each files configuration!")
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')
    local_path = fields.Char(string='Folder Path Local', required=True)
    active = fields.Boolean(string="Active", default=True, help="Determine if the configuration file is active or used")

    # Selection
    type_id = fields.Many2one(comodel_name='tw.selection', string="Type", domain=[('type','=','TypeConfigFiles')])
    
    # 9: constraints & sql constraints
    _sql_constraints = [('name_active_uniq',
                         "unique(name, active)",
                         "An active configuration with the same code already exists.")]
    
    # 10: compute/depends & on change methods
    @api.depends('local_path')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"{record.name} - {record.local_path}"

    # 11: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = vals['name'].upper()
            vals['local_path'] = str(vals['local_path'])
            cek = self.search([('local_path','=',vals['local_path'])])
            if len(cek) > 0:
                raise Warning('Konfigurasi sudah dibuat dengan local path yang sama !')
        return super(ConfigFiles,self).create(vals_list)

    def write(self,vals):
        if vals.get('local_path'):
            vals['local_path'] = str(vals['local_path'])
            cek = self.search([('local_path','=',vals['local_path'])])
            if len(cek) > 0:
                raise Warning('Konfigurasi sudah dibuat dengan local path yang sama !')
        if vals.get('name'):
            vals['name'] = vals['name'].upper()
        return super(ConfigFiles,self).write(vals)
    
    # 12: action methods
    def _config_check(self):
        """
        Context [type: mft, default: umum]
        """
        type = self.env.context.get('type', 'umum')
        params = [('type_id.value', '=', type)]
        
        if self.env.context.get('name'):
            params.append(('name', '=', self.env.context.get('name')))

        config_file = self.search(params, limit=1)
        if not config_file:
            error_params = '\n'.join([f'{p[0]} = {p[2]}' for p in params])
            raise Warning(_(f"Configuration with these param(s) do not exists!\n{error_params}"))
        
        return config_file

    def upload_file(self, file_name, file):
        config_obj = self._config_check()
        local_path = config_obj.local_path
        if not os.path.isdir(local_path):
            raise Warning(_(f"The specified directory '{local_path}' does not exist. "
                            "Please check the configuration or create the directory before uploading files."))
        
        link = f'{local_path}/{file_name}'

        # Convert Image
        file_split = file_name.split('.')
        file_ext = file_split[-1]
        
        if file_ext in ('jpg','jpeg','png','gif','JPG','JPEG','PNG','GIF'):
            try:
                file = tools.image_resize_image_big(file,size=(2000,None), filetype=None, avoid_if_small=True)
            except:
                file = file
        
        try:
            data = base64.decodebytes(bytes(file, 'utf-8'))
        except:
            data = base64.decodebytes(file)
        open(link, 'wb').write(data)

    def get_file(self, file_name):
        config_obj = self._config_check()
        local_path = config_obj.local_path
        try:
            file_get = open(local_path+'/'+file_name, 'rb').read()
            file = base64.encodebytes(file_get)
            return file
        except Exception as e:
            _logger.error("Get file %s: %s" % (file_name, e))
            return False

    def get_path_file(self, file_name):
        config_obj = self._config_check()
        local_path = config_obj.local_path
        try:
            file_get = local_path+'/'+file_name
            return file_get
        except Exception as e:
            _logger.error("Get file %s: %s" % (file_name, e))
            return False

    def copy_file(self, original, target):
        config_obj = self._config_check()
        local_path = config_obj.local_path
        shutil.copyfile(local_path+'/'+original, local_path+'/'+target)
    
    def cek_size(self, file_name=False, file_path=False):
        if file_name:
            config_obj = self._config_check()
            local_path = config_obj.local_path
            file_path = local_path+"/"+file_name
        if not file_path:
            raise Warning('You need to specify file_name or file_path to use this method.')
        file_size = os.path.getsize(file_path)
        return file_size
    
    def check_resolution_image(self, file_name=False, file_path=False):
        if file_name:
            config_obj = self._config_check()
            local_path = config_obj.local_path
            file_path = local_path+"/"+file_name
        if not file_path:
            raise Warning('You need to specify file_name or file_path to use this method.')
        image = Image.open(file_path)
        return image.size
    
    def remove_file(self, file_name):
        config_obj = self._config_check()
        local_path = config_obj.local_path
        link = local_path + '/' + file_name
        # If file exists, delete it
        if os.path.isfile(link):
            os.remove(link)
        return True
    
    def convert_file(self, file_name, file, file_ext):
        # Convert Image
        if file_ext in ('jpg', 'jpeg', 'png', 'gif'):
            try:
                file = tools.image_resize_image_big(file, size=(
                    2000, None), filetype=None, avoid_if_small=True)
            except:
                file = file
        return file
    
    def compress_pdf(self, file_name, power=3, need_compression_size = 100000):
        """Function to compress PDF via Ghostscript command line interface"""
        """
            INSTALLATION
                
                On Linux: apt install ghostscript
                On MacOSX: brew install ghostscript 
                On Windows: install binaries via [official website] (https://www.ghostscript.com/)

                calling ghoscript on windows should be like this:

                    subprocess.call(['C:/Program Files/gs/gs9.54.0/bin/gswin64.exe', '-sDEVICE=pdfwrite', '-dCom
                
                to make this script run for both windows and linux. If you are using windows device, 
                please : Put 'GS /bin folder' in path on your System Environment Variable. the default will be C:/Program Files/gs/gs9.54.0/bin/
                    
        """
        obj = self.search([])
        if not obj:
            raise Warning('Belum ada konfigurasi image')
        local_path = obj.local_path
        file_path = f'{local_path}/{file_name}'

        # Select the compression Power 
        # 0 is the lowest (May not shrinking the document)
        # 4 is the greatest (May reduce image quality so bad)
        quality = {
            0: '/default',
            1: '/prepress',
            2: '/printer',
            3: '/ebook',
            4: '/screen'
        }

        # Check size of the file, we do compression if the file larger than 1 mb
        file_size = self.cek_size(file_name=file_name)
        if file_size > need_compression_size:
            # Set input file, so output file will remain the origin name
            input_file_path = file_path.replace(".pdf", "_COMPRESS_BACKUP.pdf")
            os.rename(file_path, input_file_path)

            # GhostScript Calling is different on windows
            gs_name = 'gs'
            if platform.system() == 'Windows':
                gs_name = 'gswin64.exe'

            # Call GhostScript with subprocess
            subprocess.call([gs_name, '-sDEVICE=pdfwrite', '-dCompatibilityLevel=1.7',
                             '-dPDFSETTINGS={}'.format(quality[power]),
                             '-dNOPAUSE', '-dQUIET', '-dBATCH',
                             '-sOutputFile={}'.format(file_path),
                             input_file_path]
                            )
            
            # Remove original(Backup) file
            os.remove(input_file_path)

            # If the compression failed with current power, up the power and redo compression
            final_file_size = self.cek_size(file_name=file_name)
            ratio = 1 - (final_file_size / file_size)
            
            # We use ratio, normal ratio for compression is 0.3 - 0.7
            if ratio < 0.1 and power != 4:
                self.compress_pdf(file_name=file_name, power=power+1)
                
    # 13: private methods
                