from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

import xml.etree.ElementTree as element_tree
import webbrowser

class MonitoringB2bFile(models.TransientModel):
    _name = "tw.b2b.file.monitoring"
    _description = "Monitoring B2B File or MFT File"

    @api.depends('b2b_file_monitoring_ids')
    def cek_is_report(self):
        for record in self:
            if len(record.b2b_file_monitoring_ids) > 0:
                record.is_report = True
            else:
                record.is_report = False

    is_report = fields.Boolean(string='Report?',compute='cek_is_report')

    name = fields.Char('Filename')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    extension = fields.Selection(selection=lambda self: self.env['tw.selection'].get_mft_file_extension_options())

    config_options_id = fields.Many2one('tw.selection', 'Configuration Options' , domain=[('type','=','ServConfigOptions')])
    b2b_file_monitoring_ids = fields.One2many('tw.b2b.file.monitoring.line', 'b2b_file_monitoring_id', 'B2B File Monitoring Detail')

    def _check_configuration(self):
        config = self.env['tw.api.configuration'].suspend_security().search([
            ('config_options_id','=',self.config_options_id.id)
        ], limit=1)
        if not config:
            raise Warning('Attention, No Configuration for MFT File Monitoring is Active!')
        return config

    def action_search(self):
        if self.start_date > self.end_date:
            raise Warning('Date Period must not be reversed!')
        
        self.b2b_file_monitoring_ids = False
        
        mft_conf = self._check_configuration()
        config_options_id = self.config_options_id.id

        filename=None
        if self.name:
            tmp = self.name.split(".")
            if tmp[len(tmp)-1] != self.extension:
                raise Warning ('Attention, Filename Extension is Different from Field Extension!')
            filename=self.name

        mft_ids = mft_conf.get_sftp(
            start_date=self.start_date,
            end_date=self.end_date,
            extension=self.extension,
            filename=filename
        )

        if mft_ids:
            self.b2b_file_monitoring_ids = mft_ids
        else:
            self.is_report = False

        self.config_options_id = config_options_id

    def action_xml(self):
        if not self.b2b_file_monitoring_ids:
            raise Warning ('Attention, Please Click the Search Button First!')

        mft_conf = self._check_configuration()

        filename_ids=[]
        for filename in self.b2b_file_monitoring_ids:
            filename_ids.append(str(filename.filename))
        file_content = mft_conf.open_file_sftp(filename_ids)

        root = element_tree.Element("data")

        for file in file_content:
            tag = element_tree.Element("%s" % (file['filename']))
            root.append (tag)
            for content in file['content']:
                value = element_tree.SubElement(tag, "datafile")
                value.text = content

        tree = element_tree.ElementTree(root)
        name = f"MFT{self.id}_XML_{date.today().strftime('%Y-%m-%d')}"
        local_path = mft_conf.folder_path_local.replace("/","\\")

        save_path_file = fr"{local_path}\{name}.xml"
        with open (save_path_file, "wb") as files :
            tree.write(files)

        file_url = f"file:///{mft_conf.folder_path_local}/{name}.xml"
        webbrowser.open(file_url)