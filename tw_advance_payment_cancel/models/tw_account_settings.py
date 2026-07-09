from odoo import models, fields

class TwAccountSetting(models.Model):
    _inherit = "tw.account.setting"

    journal_avp_cancel_id = fields.Many2one(
        'account.journal',
        string='Journal Advance Payment Cancel',
        help='Journal used for Advance Payment cancellation entries'
    )
