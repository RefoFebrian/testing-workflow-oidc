import pytz
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError as Warning

class InheritTwReimbursementPettyCash(models.Model):
    _inherit = "tw.reimbursement.petty.cash"

    bank_transfer_id = fields.Many2one('tw.bank.transfer',string="Bank Transfer")