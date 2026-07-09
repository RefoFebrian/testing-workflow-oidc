# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class FormatUpload(models.Model):
    _name = "tw.format.upload"
    _description = 'Master Format Upload'

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='Name')
    active = fields.Boolean(string='Aktif?',default=True)
    
    filename_format = fields.Char(string='Filename Format', store=True)
    filename_upload_format = fields.Char(string='Filename', store=True)
    
    file_format = fields.Binary(string='File Format')
    file_format_show = fields.Binary(string='File', compute='compute_file_format')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('filename_upload_format')
    def compute_file_format(self):
        for record in self:
            if record.filename_upload_format:
                # Since the get_file method checks the configuration file without arguments,
                # pass the name in the context to obtain the file configuration with the corresponding upload format name.
                image_format = record.env['tw.config.files'].with_context(name='FORMAT-UPLOAD').get_file(record.filename_upload_format)
                if not image_format:
                    raise Warning(_(f"The file associated with '{record.name}' could not be found or accessed. "
                                    "Please ensure the file exists and try again."))
                record.file_format_show = image_format
            else : 
                record.file_format_show = False

    # 12: override methods

    @api.model_create_multi
    def create(self,vals_list):
        file_list = []
        for vals in vals_list:
            file_list.append(vals.get('file_format',False))
            vals['file_format'] = False

        create_list = super(FormatUpload,self).create(vals_list)
        for n,create in enumerate(create_list):
            filename_format_up = False
            if file_list[n]:
                filename_format = create.filename_format
                filename_format_up = create.save_upload_file(file_list[n],filename_format)
                create.filename_upload_format=filename_format_up
        return create_list
    
    def write(self, vals):
        filename_format_up = False
        if vals.get('file_format'):
            file_format = vals['file_format']
            vals['file_format'] = False
            
            filename_format = vals.get('filename_format', self.filename_format)
            filename_format_up = self.save_upload_file(file_format, filename_format)
            
            vals['filename_upload_format'] = filename_format_up
        write = super(FormatUpload,self).write(vals)

        return write
    
    # 13: action methods

    # 14: private methods
    def save_upload_file(self, file, filename):
        tmp_format = filename.split('.')
        filename_format_up = str('tw_format_upload')+'-format-'+str(self.id)+'.'+tmp_format[len(tmp_format) - 1]
        self.env['tw.config.files'].with_context(name='FORMAT-UPLOAD').upload_file(filename_format_up, file)
        return filename_format_up

