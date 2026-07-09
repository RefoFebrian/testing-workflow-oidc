# -*- coding: utf-8 -*-

import base64
import os
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from io import BytesIO
from odoo import models, fields, api, tools
from odoo.exceptions import UserError as Warning


class TwReportAutomation(models.Model):
    _name = "tw.report.automation"
    _description = "Report Automation"

    name = fields.Char(string='Name')
    directory = fields.Char(string='Directory')
    model = fields.Char(related='model_id.model', string='Model', store=True)
    parameter = fields.Char(string='Parameter')
    method = fields.Char(string='Method')
    ext = fields.Selection([('pdf', 'PDF'), ('xlsx', 'XLSX'), ('xls', 'XLS'), ('csv', 'CSV')], string='Extension')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed')], string='State', default='draft')
    is_admin = fields.Boolean(string='Is Admin', compute='_compute_is_admin')

    config_id = fields.Many2one('tw.config.files', string='Config', required=True)
    model_id = fields.Many2one('ir.model', string='Model ID', ondelete='cascade')
    report_ids = fields.One2many('tw.report.automation.file', 'report_id', string='Report File')

    def _compute_is_admin(self):
        for record in self:
            record.is_admin = self.env.user.has_group('tw_base.group_system_admin')

    def action_confirmed(self):
        if not self.env.user.has_group('tw_auto_report.group_button_tw_auto_report_confirmed'):
            raise Warning('You do not have permission to confirm this record.')
        self.state = 'confirmed'

    def action_draft(self):
        if not self.env.user.has_group('tw_auto_report.group_button_tw_auto_report_draft'):
            raise Warning('You do not have permission to draft this record.')
        self.state = 'draft'

    def action_generate_report(self):
        self.ensure_one()
        if self.state != 'confirmed':
            raise Warning('Record must be confirmed before generating report.')
        if not self.model or not self.method:
            raise Warning('Model or Method is not selected.')
        model = self.env[self.model]
        if not hasattr(model, self.method):
            raise Warning('Method %s does not exist in model %s.' % (self.method, self.model))
        
        try:
            parameter = eval(self.parameter or '{}')
        except Exception as e:
            raise Warning('Invalid parameter: %s' % str(e))

        fp = getattr(model, self.method)(parameter)

        if not isinstance(fp, (BytesIO,)):
            raise Warning('Method %s does not return a tuple.' % self.method)

        result = base64.b64encode(fp.getvalue())

        filename = "%s_%s" % (
            self.name,
            (datetime.utcnow() + timedelta(hours=7)).strftime("%Y%m%d_%H%M%S")
        )

        full_path = os.path.join(
            self.config_id.local_path,
            self.directory,
            "%s.%s" % (filename, self.ext)
        )

        self.report_ids = [(0, 0, {
            'name': "%s.%s" % (filename, self.ext),
            'full_path': full_path,
            'file': result,
        })]

        return result
    
    @api.model
    def cron_report_automation(self,name):
        records = self.search([('state', '=', 'confirmed'),('name', '=', name)], limit=1)
        if not records:
            raise Warning('No confirmed Report Automation named %s.' % name)
        
        return records.action_generate_report()