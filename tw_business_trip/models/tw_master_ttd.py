from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning
import base64


class TWMasterTtd(models.Model):
    _name = "tw.master.ttd"
    _description = "Foto TTD"

    # 8: fields
    files_upload_foto = fields.Binary("Upload Berkas")
    filename_upload_foto = fields.Char("Nama Berkas")
    files_foto = fields.Binary("Download Berkas", compute='_compute_files_foto')  # , store=False
    filename_foto = fields.Char("Nama Berkas")

    # 9: relation fields
    employee_id = fields.Many2one('hr.employee', string='Employee')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    def _compute_files_foto(self):
        for x in self:
            x.files_foto = False
            if x.filename_foto:
                x.files_foto = self.env['tw.config.files'].suspend_security().get_file(x.filename_foto)

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            now = date.today().strftime("%Y-%m-%d")

            create = super(TWMasterTtd, self).create(vals)
            if create:
                # cek extensi file foto
                files_upload_foto = vals.get('files_upload_foto')
                if files_upload_foto:
                    filename_upload_foto_tokens = str(vals.get('filename_upload_foto')).split('.')
                    filename_foto = str('tw_master_ttd-foto-')+str(create.id)+now+'.'+filename_upload_foto_tokens[len(filename_upload_foto_tokens) - 1]

                    self.env['tw.config.files'].suspend_security().upload_file(filename_foto, files_upload_foto)
                    create.files_upload_foto = False
                    create.filename_upload_foto = filename_foto
                    create.files_foto = False
                    create.filename_foto = filename_foto

            return create

    def write(self, vals):
        now = date.today().strftime("%Y-%m-%d")

        # cek extensi file foto
        files_upload_foto = vals.get('files_upload_foto')
        if files_upload_foto:
            filename_upload_foto_tokens = str(vals.get('filename_upload_foto')).split('.')
            filename_foto = str('tw_master_ttd-foto-')+str(self.id)+now+'.'+filename_upload_foto_tokens[len(filename_upload_foto_tokens) - 1]

            self.env['tw.config.files'].suspend_security().upload_file(filename_foto, files_upload_foto)
            vals['files_upload_foto'] = False
            vals['filename_upload_foto'] = filename_foto
            vals['files_foto'] = False
            vals['filename_foto'] = filename_foto


        return super(TWMasterTtd, self).write(vals)