# -*- coding: utf-8 -*-
from odoo import api, fields, models

class TwVehicleOwnershipHandoverUploadResult(models.TransientModel):
    _name = "tw.vehicle.ownership.handover.upload.result.wizard"
    _description = "Upload Result Wizard"

    result_line_ids = fields.One2many(
        'tw.vehicle.ownership.handover.upload.result.line',
        'result_id',
        string="Result Lines"
    )
    upload_filename = fields.Char(string='Filename')
    summary_success = fields.Integer(string="Total Success", readonly=True)
    summary_failed = fields.Integer(string="Total Failed", readonly=True)
    summary_skipped = fields.Integer(string="Total Skipped", readonly=True)
    summary_text = fields.Text(string="Summary", readonly=True)


class TwVehicleOwnershipHandoverUploadResultLine(models.TransientModel):
    _name = "tw.vehicle.ownership.handover.upload.result.line"
    _description = "Upload Result Line"

    result_id = fields.Many2one('tw.vehicle.ownership.handover.upload.result.wizard', string='Result')
    branch_code = fields.Char("Branch Code")
    engine_no = fields.Char("Engine No")
    status = fields.Char("Status")