import os
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from io import BytesIO
from odoo import models, fields, api, tools
from odoo.exceptions import UserError as Warning

class TwReportAutomationFile(models.Model):
    _name = "tw.report.automation.file"
    _description = "Report Automation File"
    _order = "id desc"
    
    name = fields.Char(string='Name')
    full_path = fields.Char(string='Full Path')
    file = fields.Binary(string='File')

    report_id = fields.Many2one('tw.report.automation', string='Report', required=True, ondelete='cascade')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            file_upload = vals.get('file')
            if file_upload:
                file_name = vals.get('name')
                full_path = vals.get('full_path')
                dir_path = os.path.dirname(full_path)
           
            try : 
                self.env['tw.config.files'].sudo().upload_full_file_path(dir_path, file_name, file_upload)
            except Exception as e:
                raise Warning('Failed to upload file: %s' % str(e))

            vals.pop('file')
        return super(TwReportAutomationFile, self).create(vals_list)

    def unlink(self):
        for record in self:
            if record.full_path and os.path.exists(record.full_path):
                try:
                    os.remove(record.full_path)
                except Exception as e:
                    raise Warning('Failed to delete file: %s' % str(e))
        return super(TwReportAutomationFile, self).unlink()

    def action_download(self):
        self.ensure_one()
        self.file = self.env['tw.config.files'].sudo().get_full_file_path(self.full_path)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/tw.report.automation.file/%s/file/%s?download=true' % (self.id, self.name),
            'target': 'self',
        }
    