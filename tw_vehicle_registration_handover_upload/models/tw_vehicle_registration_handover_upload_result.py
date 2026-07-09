# -*- coding: utf-8 -*-
from odoo import api, fields, models

class TwVehicleRegistrationHandoverUploadResultLine(models.TransientModel):
    _name = "tw.vehicle.registration.handover.upload.result.line"
    _description = "Result line for vehicle registration handover upload"

    wizard_id = fields.Many2one('tw.vehicle.registration.handover.upload.result.wizard', string='Wizard', ondelete='cascade')
    branch = fields.Char(string='Branch')
    receiver = fields.Char(string='Receiver')
    status = fields.Char(string='Status')

class TwVehicleRegistrationHandoverUploadResultWizard(models.TransientModel):
    _name = "tw.vehicle.registration.handover.upload.result.wizard"
    _description = "Result wizard for handover upload"

    upload_filename = fields.Char(string='Filename')
    summary_success = fields.Integer(string="Total Success", readonly=True)
    summary_failed = fields.Integer(string="Total Failed", readonly=True)
    summary_skipped = fields.Integer(string="Total Skipped", readonly=True)
    summary_text = fields.Text(string="Summary", readonly=True)
    result_line_ids = fields.One2many('tw.vehicle.registration.handover.upload.result.line', 'wizard_id', string='Results')
