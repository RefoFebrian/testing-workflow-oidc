# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWActivityDetailBiayaInherit(models.Model):
    _inherit = "tw.activity.atl.btl.detail.biaya"

    upload_file = fields.Binary(string='Upload File')
    upload_filename = fields.Char(string='File Name')

    expense_source_id = fields.Many2one('tw.master.expense.source', string='Expense Source')

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        config = self.env['tw.config.files']
        # Map to store docs temporarily by list index since we need record IDs first
        upload_data = {}
        for i, val in enumerate(vals_list):
            if val.get('upload_file'):
                upload_data[i] = {
                    'binary': val.pop('upload_file'),
                    'filename': val.get('upload_filename', 'Attachment')
                }
        
        records = super(TWActivityDetailBiayaInherit, self).create(vals_list)

        for i, rec in enumerate(records):
            if i in upload_data:
                data = upload_data[i]
                tmp_foto = str(data['filename']).split('.')
                ext = tmp_foto[-1] if len(tmp_foto) > 1 else 'bin'
                allowed_ext = self.env['ir.config_parameter'].sudo().get_param('tw_activity_atl_btl.attachment_allowed_extenstion')
                if ext not in allowed_ext:
                    raise Warning('Dokumen pada Detail Biaya vendor %s dengan catatan %s, Tipe dokumen yang diterima hanya format %s' % (rec.partner_id.name, rec.note, allowed_ext))
                filename = f"tw_activity_detail_biaya-docs-{rec.id}.{ext}"
                
                # Upload and validate size
                config.suspend_security().upload_file(filename, data['binary'])
                cek_size = config.suspend_security().cek_size(filename)
                cek_size_kb = cek_size / 1024.0
                if cek_size_kb > 300:
                    raise Warning(_('File terlalu besar, maksimal 300kb.'))
                
                rec.upload_filename = filename

        return records
    
    def write(self, vals):
        config = self.env['tw.config.files']
        if vals.get('upload_file'):
            docs = vals.pop('upload_file')
            filename_orig = vals.get('upload_filename') or self.upload_filename or 'Attachment'
            
            tmp_foto = str(filename_orig).split('.')
            ext = tmp_foto[-1] if len(tmp_foto) > 1 else 'bin'
            allowed_ext = self.env['ir.config_parameter'].sudo().get_param('tw_activity_atl_btl.attachment_allowed_extenstion')
            if ext not in allowed_ext:
                raise Warning('Dokumen pada Detail Biaya vendor %s dengan catatan %s, Tipe dokumen yang diterima hanya format %s' % (self.partner_id.name, self.note, allowed_ext))
            filename = f"tw_activity_detail_biaya-docs-{self.id}.{ext}"
            
            config.suspend_security().upload_file(filename, docs)
            cek_size = config.suspend_security().cek_size(filename)
            cek_size_kb = cek_size / 1024.0
            if cek_size_kb > 300:
                raise Warning(_('File terlalu besar, maksimal 300kb.'))
            
            vals['upload_filename'] = filename

        return super(TWActivityDetailBiayaInherit, self).write(vals)

    def _get_upload_file_data(self):
        """Helper to retrieve binary data from external storage."""
        self.ensure_one()
        if not self.upload_filename:
            return False
        config = self.env['tw.config.files']
        # Assuming context 'umum' is used as in the user's upload logic
        return config.suspend_security().with_context(type='umum').get_file(self.upload_filename)

