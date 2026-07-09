from datetime import date
from zipfile import ZipFile

from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

import random


class TwB2bFileUpload(models.TransientModel):
    _name = "tw.b2b.file.upload"
    _description = "B2B File or MFT File Upload"

    def _get_default_date(self):
        return date.today()

    name = fields.Char('Name')
    date = fields.Date('Date', default=_get_default_date)

    extension = fields.Selection(selection=lambda self: self.env['tw.selection'].get_mft_file_extension_options())
    type = fields.Selection(string='Upload Type', selection=[
        ('file','Upload by File'),
        ('zip','Upload by ZIP'),
    ],default='file')
    state_x = fields.Selection([
        ('choose','choose'),
        ('get','get')
    ],default='choose')

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'tw_b2b_file_upload_attachment_rel',
        'wizard_id',
        'attachment_id',
        string='Files',
    )
    filename_upload = fields.Char('Filename Uploaded')
    uploaded_filenames = fields.Text('Uploaded Filenames')
    upload_count = fields.Integer('Uploaded File Count')
    is_teds_upload = fields.Boolean(compute='_compute_is_teds_upload')

    config_options_id = fields.Many2one('tw.selection', 'Configuration Options' , domain=[('type','=','ServConfigOptions')])

    @api.depends('config_options_id')
    def _compute_is_teds_upload(self):
        for rec in self:
            selection_name = (rec.config_options_id.name or '').upper()
            selection_value = (rec.config_options_id.value or '').upper()
            rec.is_teds_upload = 'TEDS' in selection_name or 'TEDS' in selection_value

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            filename = vals.get('filename_upload')
            ext = vals.get('extension')
            if filename:
                filename_upload = filename.split('.')
                ext = ext or filename_upload[-1]
                title = "[%s] %s" % (ext.upper(), filename.upper())
            else:
                title = "[%s] UPLOAD" % ((ext or 'FILE').upper())
            vals['name'] = title
        return super(TwB2bFileUpload, self).create(vals_list)

    def action_import(self):
        self.ensure_one()

        attachments = self.attachment_ids.filtered(lambda attachment: attachment.datas and attachment.name)
        if not attachments:
            raise Warning('Please input the File First.')

        uploaded_filenames = self.action_upload_file(attachments)
        upload_summary = uploaded_filenames[0] if len(uploaded_filenames) == 1 else _('%s files uploaded') % len(uploaded_filenames)

        self.write({
            'filename_upload': upload_summary,
            'uploaded_filenames': '\n'.join(uploaded_filenames),
            'upload_count': len(uploaded_filenames),
            'name': "[%s] %s" % ((self.type == 'zip' and 'ZIP' or (self.extension or 'FILE')).upper(), upload_summary.upper()),
            'state_x': 'get',
        })

        form_id = self.env.ref('tw_b2b_file_management.tw_b2b_file_upload_form_view').id

        return {
            'name': ('B2B File Upload'),
            'res_model': 'tw.b2b.file.upload',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': False,
            'views': [(form_id, 'form')],
            'target': 'current',
            'res_id': self.ids[0],
        }

    def _get_attachment_extension(self, attachment):
        split_name = (attachment.name or '').rsplit('.', 1)
        if len(split_name) < 2:
            raise Warning(_('File %s does not have a valid extension.') % (attachment.name or _('Unknown')))
        return split_name[-1].lower()

    def _check_attachment_before_upload(self, attachment):
        ext = self._get_attachment_extension(attachment)
        selected_extension = (self.extension or '').lower()

        if ext == 'zip' and self.type != 'zip':
            raise Warning('Please Select the Upload Type of ZIP File.')

        if self.type != 'zip' and not self.is_teds_upload and not selected_extension:
            raise Warning('Please Select Format File.')

        if self.type != 'zip' and not self.is_teds_upload and ext != selected_extension:
            raise Warning('Please Upload Files According to the Selected Extension.')

        if self.type == 'zip' and ext != 'zip':
            raise Warning('Please Upload Files With ZIP Format.')

    def _prepare_uploaded_filename(self, attachment):
        if self.type != 'zip':
            return attachment.name

        size = 6
        alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        tmp = attachment.name.rsplit('.', 1)
        return tmp[0] + '_' + ''.join(random.choice(alphabet) for _ in range(size)) + '.' + tmp[-1]

    def action_upload_file(self, attachments):
        self.ensure_one()
        configuration_obj = self.env['tw.api.configuration'].get_api_config('mft_windows')
        if not configuration_obj:
            raise Warning('Attention, No Configuration for MFT File Upload is Active!')

        conf_file_obj = self.env['tw.config.files'].with_context(type='mft', name=self.config_options_id.value)
        local_path = configuration_obj.folder_path_local
        uploaded_filenames = []

        for attachment in attachments:
            self._check_attachment_before_upload(attachment)

            filename_upload = self._prepare_uploaded_filename(attachment)
            conf_file_obj.sudo().upload_file(filename_upload, attachment.datas)
            uploaded_filenames.append(filename_upload)

            if self.type == 'zip':
                path = local_path + '/' + filename_upload
                with ZipFile(path, 'r') as zip_obj:
                    zip_obj.extractall(local_path)

        return uploaded_filenames
