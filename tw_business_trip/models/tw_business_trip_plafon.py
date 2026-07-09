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

class TwBusinessTripPlafon(models.Model):
    _name = "tw.business.trip.plafon"
    _description = "Business Trip - Plafon"
    _rec_name = 'display_name'

    # 8: fields
    display_name = fields.Char(compute='_compute_display_name', store=False)
    name = fields.Selection(selection=[
        ('uang_saku', 'Uang Saku'),
        ('accommodation', 'Akomondasi / Penginapan')
    ], string="Tipe")
    nominal_domestic = fields.Integer(string="Nominal Domestic")
    nominal_asia = fields.Integer(string="Nominal Asia")
    nominal_non_asia = fields.Integer(string="Nominal Non Asia")
    dollar_rate = fields.Integer(string="Kurs Dolar")

    group_id = fields.Many2one("res.groups", string="Group")

    @api.constrains('name', 'group_id')
    def _check_duplicate_data(self):
        duplicate_records = self.search([
            ('name', '=', self.name),
            ('group_id', '=', self.group_id.id),
            ('id', '!=', self.id),  # Exclude the current record
        ], limit=1)
        if duplicate_records:
            raise Warning('Data sudah ada. Duplicate entry is not allowed.')

    @api.depends('group_id','nominal_domestic','nominal_asia','nominal_non_asia','dollar_rate')
    def _compute_display_name(self):
        for rec in self:
            if not rec.group_id:
                rec.display_name = ''
                continue

            rec.display_name = (
                f"{rec.group_id.name} | "
                f"Domestik Rp {rec.nominal_domestic:,.0f} | "
                f"Asia Rp {(rec.nominal_asia * rec.dollar_rate):,.0f} | "
                f"Non-Asia Rp {(rec.nominal_non_asia * rec.dollar_rate):,.0f}"
            )