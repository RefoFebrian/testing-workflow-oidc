from odoo import models, fields, api

class TwVehicleRegistrationUploadResultLine(models.TransientModel):
    _name = "tw.vehicle.registration.upload.result.line"
    _description = "Vehicle Registration Upload Result line"

    wizard_id = fields.Many2one('tw.vehicle.registration.upload.result.wizard', string='Wizard', ondelete='cascade')
    branch = fields.Char(string='Branch')
    biro = fields.Char(string='Biro')
    status = fields.Char(string='Result')
    
class TwVehicleRegistrationUploadResultWizard(models.TransientModel):
    _name = "tw.vehicle.registration.upload.result.wizard"
    _description = "Vehicle Registration Upload Result Wizard"

    upload_filename = fields.Char(string="Filename")
    summary_success = fields.Integer(string="Total Success", readonly=True)
    summary_failed = fields.Integer(string="Total Failed", readonly=True)
    summary_skipped = fields.Integer(string="Total Skipped", readonly=True)
    summary_text = fields.Text(string="Summary", readonly=True)
    result_line_ids = fields.One2many('tw.vehicle.registration.upload.result.line', 'wizard_id', string='Result Line')