import string
from odoo import models,fields,api

class UploadMappingJasaResultWizard(models.TransientModel):
    _name = "tw.upload.mapping.jasa.result.wizard"
    _description = "Upload Mapping Jasa Result Wizard"

    total_success = fields.Integer(string="Total Success")
    total_failed = fields.Integer(string="Total Failed")
    total_processed = fields.Integer(string="Total Processed", compute='_total_processed')
    not_found_list = fields.Text(string="Detail Hasil")

    @api.depends('total_success', 'total_failed')
    def _total_processed(self):
        for record in self:
            record.total_processed = record.total_success + record.total_failed
