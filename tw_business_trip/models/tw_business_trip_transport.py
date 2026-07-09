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

class TwBusinessTripTransport(models.Model):
    _name = "tw.business.trip.transport"
    _description = "Business Trip - Transport"

    # 8: fields
    transportation = fields.Selection(selection=[
        ("AD", "Angkutan Darat"),
        ("AL", "Kapal Laut"),
        ("AU", "Pesawat Terbang"),
        ("TAXI", "Taxi"),
        ("BENSIN", "Bensin"),
        ("TOL", "Tol"),
        ("PARKING", "Parkir"),
        ("OTHER", "Lain - Lain")
    ], required=True)
    state_header = fields.Selection(string='Status Header', related="business_trip_id.state", store=True)
    
    planning_cost = fields.Integer(string="Biaya Planning")
    actual_cost = fields.Integer(string="Biaya actual")
    selisih_cost = fields.Integer(string="Selisih", compute="_compute_selisih_cost", store=True)

    # Documents
    files_upload = fields.Binary("Upload Berkas")
    filename_upload = fields.Char("Nama Berkas")
    files = fields.Binary("Download Berkas", compute='_compute_files')  # , store=False
    filename = fields.Char("Nama Berkas")

    # 9: relation fields
    business_trip_id = fields.Many2one(string="ID Perjalan Dinas", comodel_name="tw.business.trip", ondelete="cascade")

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    def _compute_files(self):
        for x in self:
            x.files = False
            if x.filename:
                x.files = self.env['tw.config.files'].suspend_security().get_file(x.filename)

    @api.depends("planning_cost", "actual_cost")
    def _compute_selisih_cost(self):
        for record in self:
            record.selisih_cost = record.actual_cost - record.planning_cost

    # 12: override methods
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            now = date.today().strftime("%Y-%m-%d")

            create = super(TwBusinessTripTransport, self).create(vals)
            # upload file
            files_upload = vals.get('files_upload')
            if files_upload:
                filename_upload_tokens = str(vals.get('filename_upload')).split('.')
                if filename_upload_tokens[len(filename_upload_tokens) - 1] != 'pdf':
                    raise Warning('Extensi File yg di upload harus PDF sesuai dengan Extensi yang telah ditentukan')

                filename = str('tw_business_trip-transport-')+str(create.id)+now+'.'+filename_upload_tokens[len(filename_upload_tokens) - 1]

                self.env['tw.config.files'].suspend_security().upload_file(filename, files_upload)
                create.files_upload = False
                create.filename_upload = filename
                create.files = False
                create.filename = filename
            return create
    
    def write(self, vals):
        now = date.today().strftime("%Y-%m-%d")

        # upload file
        files_upload = vals.get('files_upload')
        if files_upload:
            filename_upload_tokens = str(vals.get('filename_upload')).split('.')
            if filename_upload_tokens[len(filename_upload_tokens) - 1] != 'pdf':    
                raise Warning('Extensi File yg di upload harus PDF sesuai dengan Extensi yang telah ditentukan')

            filename = str('tw_business_trip-transport-')+str(self.id)+now+'.'+filename_upload_tokens[len(filename_upload_tokens) - 1]

            self.env['tw.config.files'].suspend_security().upload_file(filename, files_upload)
            vals['files_upload'] = False
            vals['filename_upload'] = filename
            vals['files'] = False
            vals['filename'] = filename

        return super(TwBusinessTripTransport, self).write(vals)

    def action_download_file(self):
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/tw.business.trip.transport/{self.id}/files/{self.filename}?download=true',
            'target': 'self',
        }