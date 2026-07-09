from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class TwWorkOrderAccountSetting(models.Model):
    _inherit = "tw.account.setting"

    wo_reg_journal_id = fields.Many2one(
        'account.journal', 'Journal WO Regular',
        help="Field ini digunakan untuk setting account journal. "
             "pada transaksi Work Order untuk type Reguler"
    )
    wo_customer_payment_journal_id = fields.Many2one(
        'account.journal', 'Journal WO Customer Payment',
        help="Field ini digunakan untuk setting account journal. "
             "pada transaksi Customer Payment"
    )