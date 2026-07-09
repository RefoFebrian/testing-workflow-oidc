from odoo import models, fields
import os

class MonitoringMftFileLine(models.TransientModel):
    _name = "tw.b2b.file.monitoring.line"
    _description = "Monitoring B2B File or MFT File Detail"
    _order = "upload_date DESC"

    filename = fields.Char(string='Filename')
    upload_date = fields.Date(string='Upload Date')
    upload_time = fields.Char(string='Jam Upload')
    file = fields.Binary(string='File')

    config_options_id = fields.Many2one('tw.selection', 'Configuration Options' , domain=[('type','=','ServConfigOptions')] ,related='b2b_file_monitoring_id.config_options_id')
    b2b_file_monitoring_id = fields.Many2one('tw.b2b.file.monitoring', 'B2B File Monitoring')

    def action_dowload(self):
        mft_conf = self.b2b_file_monitoring_id._check_configuration()
        conf_img_obj = self.env['tw.config.files'].sudo()._config_check()
        
        mft_conf.get_file_sftp(self.filename)
        self.file = conf_img_obj.get_img(self.filename,mft_conf.folder_path_local)
        os.remove(mft_conf.folder_path_local+'/'+self.filename)
        return {
            'type': 'ir.actions.act_url',
            'name': ('Download File'),
            'url': '/web/content/tw.b2b.file.monitoring.line/%s/file/%s?download=true' % (self.id, self.filename)
        }