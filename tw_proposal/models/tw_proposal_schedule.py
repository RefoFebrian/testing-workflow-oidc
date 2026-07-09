# -*- coding: utf-8 -*-

# 1: imports of python lib
import difflib
import json
import os
import logging
import re

# 2: import of known third party lib
from datetime import date, timedelta, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)


class TwProposalSchedule(models.Model):
    _name = "tw.proposal.schedule"
    _description = "Proposal Online - Schedule"

    location = fields.Char(string='Lokasi')
    date_start = fields.Date(string='Start Date')
    date_end = fields.Date(string='End Date')
    # date_close = fields.Date(string='Close Date')
    day_count = fields.Integer(string='Days')
    
    
    proposal_id = fields.Many2one('tw.proposal', string='Nomor Proposal', ondelete='cascade')

    @api.onchange('date_start','date_end')
    def _onchange_date(self):
        self.day_count = False
        if self.date_end and self.date_start:
            if self.date_end < self.date_start:
                raise Warning("End Date must be greater than Start Date")
            self.day_count = (self.date_end - self.date_start).days + 1