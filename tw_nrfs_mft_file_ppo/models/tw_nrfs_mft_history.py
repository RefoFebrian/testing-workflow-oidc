# -*- coding: utf-8 -*-

# 1: imports of python lib
import logging
import os
from datetime import date, datetime, time

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib

class TWNrfsMftStory(models.Model):
    _name = "tw.nrfs.mft.history"
    _description = "NRFS - History MFT"
    _order = "id desc"

    nrfs_filename = fields.Char(string='Nama File NRFS')
    nrfs_send_date = fields.Date(string='Tanggal Kirim NRFS')
    nrfs_id = fields.Many2one('tw.nrfs', string='NRFS ID')