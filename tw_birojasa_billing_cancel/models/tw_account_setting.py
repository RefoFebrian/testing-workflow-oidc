# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TwBirojasaBillingCancelAccountSetting(models.Model):
    _inherit = "tw.account.setting"
    _description = 'Account Settings for Birojasa Billing Cancellation'

    journal_birojasa_billing_cancel_id = fields.Many2one(
        'account.journal',
        string='Journal Birojasa Billing Cancel',
        help="Journal used for Birojasa Billing cancellation entries"
    )