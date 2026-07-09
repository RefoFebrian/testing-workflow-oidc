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

class TwBusinessTripDetail(models.Model):
    _name = "tw.business.trip.detail"
    _description = "Business Trip - Detail"

    # 8: fields
    activity_date = fields.Date(string="Tanggal Kegiatan")
    activity = fields.Text(string="Kegiatan")
    description = fields.Text(string="Uraian")
    result = fields.Text(string="Hasil")

    # 9: relation fields
    business_trip_id = fields.Many2one(string="ID Perjalan Dinas", comodel_name="tw.business.trip", ondelete="cascade")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods