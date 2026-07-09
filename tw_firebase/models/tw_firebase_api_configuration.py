# -*- coding: utf-8 -*-
import re

from datetime import datetime
from odoo import api, fields, models


class APIConfiguration(models.Model):
    _inherit = "tw.api.configuration"

    project_id = fields.Char(help="Firebase project-id is obtained from Firebase project configuration")
    creds_file = fields.Binary()
    creds_filename = fields.Char()

    api_type_id = fields.Many2one('tw.selection', string='API Type' , domain=[('type','=','ApiType')])

    def _upload_credentials(self, vals):
        creds_file = vals.pop('creds_file')
        ext = vals['creds_filename'].split('.')[-1] if vals.get('creds_filename') else ''
        name = vals.get('name', self.name)
        creds_filename = f'{name}_{datetime.now()}.{ext}'
        creds_filename = re.sub(r'[:\s]', '_', creds_filename)
        self.env['tw.config.files'].suspend_security().upload_file(creds_filename, creds_file)
        vals['creds_filename'] = creds_filename

        return vals
    
    def get_creds_file_path(self):
        return self.env['tw.config.files'].suspend_security().get_path_file(self.creds_filename)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('creds_file'):
                creds_vals = self._upload_credentials(vals)
                vals.update(creds_vals)

        return super().create(vals_list)

    def write(self, vals):
        if vals.get('creds_file'):
            creds_vals = self._upload_credentials(vals)
            vals.update(creds_vals)

        return super().write(vals)
