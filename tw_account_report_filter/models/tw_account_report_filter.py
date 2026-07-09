# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TwAccountReportFilter(models.Model):
    _name = "tw.account.report.filter"
    _description = "Account Report Filter"

    name = fields.Char(string="Name")
    account_ids = fields.Many2many(
        'account.account', 'account_account_report_filter',
        'report_line_id', 'account_id', 'Accounts'
    )
    

