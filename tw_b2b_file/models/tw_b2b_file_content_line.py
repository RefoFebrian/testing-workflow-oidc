# -*- coding: utf-8 -*-

# 1: imports of python lib

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TwB2BFileContentLine(models.Model):
    _name = "tw.b2b.file.content.line"
    _description = "B2B File Content Details"

    # 7: defaults methods
    
    # 8: fields
    name = fields.Char(string="Key", help="Identifier key to descibe the data")
    value = fields.Char(string="Value", help="Stored value of the key")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')],
                              default='draft', string="Status",
                              help=" * Draft: The content is not processed yet.\n"
                                   " * Done: The content has been processed.\n")
    
    # 9: relation fields
    file_content_id = fields.Many2one('tw.b2b.file.content', string="B2B File", ondelete='cascade', help="Related B2B File")
    
    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        contents = super().create(vals_list)
        # for content in contents:
        #     ext = content.file_id.ext
        #     content.payload = content._convert_content_to_payload(ext)
            
        return contents

    # 13: action methods
    def cron_process_content(self):
        self.state = 'done'
        pass

    # 14: private methods