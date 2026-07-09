from odoo import models, fields


class B2bFileWizard(models.TransientModel):
    _name = "tw.b2b.file.wizard"
    _description = "mft.wizard"
    
    message = fields.Text('Message', readonly=True)