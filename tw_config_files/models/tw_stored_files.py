# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
import os
import logging
_logger = logging.getLogger(__name__)

# 4:  imports from odoo modules
from odoo import models, fields, api
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWStoredFiles(models.TransientModel):
    _name = "tw.stored.files.wizard"
    _description = "Stored Files"

    # 7: defaults methods
    def config_selection(self):
        choices = []
        for config in self.env['tw.config.files'].search([]):
            choices.append((config.id, config.local_path))
        return choices

    # 8: fields
    name = fields.Char()
    config_id = fields.Selection(config_selection, default=False)
    file_ids = fields.One2many('tw.stored.files.line.wizard', 'storage_id')
    
    # 9: constraints & sql constraints
    
    # 10: compute/depends & on change methods
    @api.onchange('config_id')
    def display_storage_files(self):
        if self.config_id:
            file_line = []
            config = self.env['tw.config.files'].suspend_security().browse(
                self.config_id)
            try:
                os.chdir(config.local_path)
            except Exception as err:
                raise Warning(err.args)

            for file in os.listdir('.'):
                path = os.path.join(config.local_path, file)
                if os.path.isfile(path):
                    file_line.append([0, 0, { 'name': file }])
            
            if file_line:
                self.file_ids = file_line
                self.name = config.local_path
        else:
            self.file_ids = []

    # 11: override methods
    
    # 12: action methods
    
    # 13: private methods


class TWStoredFilesLine(models.TransientModel):
    _name = "tw.stored.files.line.wizard"
    _description = "Stored Files Tree"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string='File Name')
    file = fields.Binary(string='File')
    storage_id = fields.Many2one('tw.stored.files.wizard', string='File Category')

    # 9: constraints & sql constraints
    
    # 10: compute/depends & on change methods
    
    # 11: override methods
    
    # 12: action methods
    def action_export_file(self):
        config = self.env['tw.config.files'].suspend_security().browse(int(self.storage_id.config_id))
        file = config.suspend_security().get_file(self.name)
        self.file = file

        return {
            'type' : 'ir.actions.act_url',
            'url': '/web/content/tw.stored.files.line.wizard/%s/file/%s?download=true' % (self.id, self.name),
            'target': 'new',
        }
    
    # 13: private methods
    