# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWBoomTaskEscalationInherit(models.Model):
    _inherit = "tw.boom.task.escalation"


    note_wa = fields.Char(string="Keterangan WA", related='wa_id.note')

    state_wa = fields.Selection(selection=[
        ("draft", "Draft"),
        ("sent","Sent"), # Received by Wablas server
        ("cancel","Cancel"),
        ("failed","Failed"),
        ("delivered","Delivered"), # Sent to recipient
        ("read","Read")
    ], readonly=True, string="Status WA", default="draft")

    wa_id = fields.Many2one('tw.whatsapp.message', 'WA ID', domain=[('message_type', '=', 'outbox')])