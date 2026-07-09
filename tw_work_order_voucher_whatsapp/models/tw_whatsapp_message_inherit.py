# -*- coding: utf-8 -*-
from datetime import datetime, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

import logging
_logger = logging.getLogger(__name__)

class WhatsappMessageDetail(models.Model):
    _inherit = "tw.whatsapp.message"

    # 7: defaults methods

    # 8: fields
    otp_code = fields.Char(string='Kode OTP')
    expired_date = fields.Datetime(string="Tanggal Expired", help="Expired Date for OTP Code")

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods