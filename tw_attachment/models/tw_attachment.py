# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
from odoo.tools import create_index
from urllib.parse import urlparse
import os
import logging

_logger = logging.getLogger(__name__)

class TWAttachment(models.Model):
    _name = "tw.attachment"
    _inherit = "ir.attachment"
    _description = 'TW Attachment'
    _order = 'id desc'
    


    # Fields
    datas = fields.Binary(string="File Content")

    # Relation Fields
    res_model = fields.Char(string='Related Model', readonly=True, index=False)
    res_id = fields.Many2oneReference(string='Related Document ID', model_field='res_model', readonly=True, index=False)

    # Onchange Method
    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'url':
            self.name = False
            self.datas = False
            self.mimetype = False

        if self.type == 'binary':
            self.name = False
            self.datas = False
            self.mimetype = False
    
    @api.onchange('name')
    def _onchange_name(self):
        if self.type == 'url':
            self._check_url(self.name)

    # Inherit Method
    def init(self):
        """ change index on res_model and res_id to a multi-column index on (res_model, res_id)
        This is to optimize the performance of the search view when searching for attachments by model and id
        """
        create_index(self.env.cr,
                     indexname='tw_attachment_res_model_res_id_idx',
                     tablename='tw_attachment',
                     expressions=['res_model', 'res_id'])
        super().init()
        
    # Private Method 
    def _check_url(self,url):
        """
        Memvalidasi format URL.
        URL harus memiliki skema http atau https dan domain yang valid.
        """
        if url:
            try:
                parsed_url = urlparse(url)
                is_valid = all([parsed_url.scheme in ['http', 'https'], parsed_url.netloc])

                if not is_valid:
                    self.name = False
                    raise Warning(
                        _("URL Website tidak valid. Pastikan menggunakan 'http://' atau 'https://' dan formatnya benar. Contoh: https://www.odoo.com")
                    )
            except ValueError:
                self.name = False
                raise Warning(
                    _("Format URL Website tidak dapat diproses. Harap periksa kembali.")
                )

    def _get_code(self):
        # Replace this if inherit from tw.attachment.mixin and need to use different code path
        return 'general'

    @api.model
    def _get_attachment_path(self):
        """Get the attachment path for a given code.
        
        Args:
            code (str): The storage code to get the path for
            
        Returns:
            str: The full path for storing attachments
        """
        config = self.env['tw.config.files'].search([('name', '=', self._get_code().upper())], limit=1)
        if not config:
            raise Warning(f"Path config not found for code: {self._get_code()}")
        return config.local_path


    @api.model
    def _full_path(self, fname):
        """Get the full filesystem path for the given filename.
        
        Args:
            fname (str): The filename (checksum) to get the full path for
            
        Returns:
            str: The full filesystem path
            
        Raises:
            Warning: If the file doesn't exist
        """
        # Get the full path using _get_path
        _, full_path = self._get_path(None, fname)
        
        # Verify the file exists
        if not os.path.isfile(full_path):
            raise Warning(f"File {full_path} not found")
            
        return full_path

    @api.model
    def _get_path(self, bin_val, checksum):
        """Return the path and filename used to store the file content.
        
        This is a simplified version of Odoo 18's _get_path that uses our custom
        storage path while maintaining the same return signature.
        """
        # Use the checksum as the filename
        fname = checksum
        
        # Get the full path using our custom storage location
        path = self._get_attachment_path()
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            raise Warning(f"Failed to create directory {path}: {e}")
        full_path = os.path.join(path, fname)
        
        return fname, full_path

    @api.model
    def _file_write(self, bin_value, checksum):
        """Write the file to the appropriate directory based on the model.
        
        Args:
            bin_value (bytes): The file content to write
            checksum (str): The SHA1 checksum of the file
            
        Returns:
            str: The stored file path (just the checksum, matching Odoo 18)
        """
        # Get the filename and full path using _get_path
        fname, full_path = self._get_path(bin_value, checksum)
        
        # Write the file
        with open(full_path, 'wb') as f:
            f.write(bin_value)
            
        # Set the correct file permissions (matching Odoo's default)
        try:
            os.chmod(full_path, 0o644)
        except OSError:
            raise Warning(f"Failed to set file permissions for {full_path}")
        
        # Return just the filename (checksum)
        return fname

    @api.model
    def _file_read(self, fname):
        """Read a file from the filesystem based on its path.
        
        Args:
            fname (str): The filename (checksum) to read
            
        Returns:
            bytes: The file content
            
        Raises:
            Warning: If the file cannot be read
        """
        # Get the full path using _get_path
        _, full_path = self._get_path(None, fname)
        
        try:
            with open(full_path, 'rb') as f:
                return f.read()
        except (IOError, OSError) as e:
            raise Warning(f"Error reading file {full_path}")
    
    def create_attachments(self, attachments):
         for attachment_data in attachments:
            filename = attachment_data.get('filename')
            source = attachment_data.get('source') 

            if not filename or not source or not isinstance(source, str):
                continue

            vals = {'name': filename}
            source_trimmed = source.strip()

            if source_trimmed.startswith(('http://', 'https://')):
                vals['type'] = 'url'
                vals['url'] = source_trimmed
                self.create(vals)
            else:
                try:                   
                    base64.b64decode(source_trimmed, validate=True)
                    vals['type'] = 'binary'
                    vals['datas'] = source_trimmed
                    attachment_vals_list.append(vals)
                except (binascii.Error, TypeError):
                    _logger.warning(f"Skipping attachment '{filename}' for Disposal {self.name}: "
                                    f"Source is not a valid URL or Base64 string.")
                    continue
