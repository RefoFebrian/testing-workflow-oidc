# -*- coding: utf-8 -*-
from datetime import datetime, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning

import logging
_logger = logging.getLogger(__name__)

class WhatsappMessageDetail(models.Model):
    _name = "tw.whatsapp.message.detail"
    _description = "Whatsapp Message Detail"

    # 7: defaults methods

    # 8: fields
    name = fields.Char("Name")

    # 9: relation fields
    whatsapp_id = fields.Many2one(comodel_name='tw.whatsapp.message', string="Whatsapp ID", ondelete="cascade")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods