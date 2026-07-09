# -*- coding: utf-8 -*-

import base64
import os
from datetime import datetime, date
from odoo import models, fields, api, tools
from odoo.exceptions import UserError as Warning

class tw_config_files(models.Model):
    _inherit = "tw.config.files"

    def upload_full_file_path(self, dir_path, filename, file_data):
        file_ext = filename.split('.')[-1].lower()

        file_data = self.compress_image(filename, file_data, file_ext)

        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

        decoded_file_data = base64.b64decode(file_data)
        file_path = os.path.join(dir_path, filename)

        with open(file_path, 'wb') as fp:
            fp.write(decoded_file_data)

    def get_full_file_path(self, file_path):
        if not os.path.exists(file_path):
            raise Warning(f"The file associated with '{file_path}' could not be found or accessed. "
                            "Please ensure the file exists and try again.")
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
            return base64.b64encode(file_data).decode('utf-8')
        except:
            raise Warning(f"The file associated with '{file_path}' could not be read. "
                            "Please ensure the file exists and try again.")

    
    def compress_image(self, file_name, file, file_ext):
        # Convert Image
        if file_ext in ('jpg', 'jpeg', 'png', 'gif'):
            try:
                file = tools.image_resize_image_big(file, size=(
                    2000, None), filetype=None, avoid_if_small=True)
            except:
                file = file
        return file