# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class TwBirojasaBillingUploadResultLine(models.TransientModel):
    _name = "tw.birojasa.billing.process.upload.result.line"
    _description = 'Result line for billing upload'

    wizard_id = fields.Many2one('tw.birojasa.billing.process.upload.result.wizard', string='Wizard', ondelete='cascade')
    branch = fields.Char(string='Branch')
    biro = fields.Char(string='Biro Jasa')
    status = fields.Char(string='Status')

class TwBirojasaBillingUploadResultWizard(models.TransientModel):
    _name = "tw.birojasa.billing.process.upload.result.wizard"
    _description = 'Result wizard for billing upload'

    upload_filename = fields.Char(string='Filename')
    summary_success = fields.Integer(string="Total Success", readonly=True)
    summary_failed = fields.Integer(string="Total Failed", readonly=True)
    summary_skipped = fields.Integer(string="Total Skipped", readonly=True)
    summary_text = fields.Text(string="Summary", readonly=True)

    result_line_ids = fields.One2many('tw.birojasa.billing.process.upload.result.line', 'wizard_id', string='Results')