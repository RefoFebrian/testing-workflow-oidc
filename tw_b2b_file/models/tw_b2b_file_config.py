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



class TwB2BFileConfig(models.Model):
    _name = "tw.b2b.file.config"
    _description = "Settings of B2B File"

    name = fields.Char(string="File Name", help="Name the file extension.")
    headers = fields.Char(string="Content Headers", help="Sequentials header name for each file configuration")
    index_mapping = fields.Char(string="Index Mapping", help="Index mapping for each file")
    description = fields.Char(string="Description", help="Describe the configuration for.")
    is_process_by_header = fields.Boolean('Process by Header?', default=False)
    separator_id = fields.Many2one('tw.selection', string="Separator", domain=[('type', '=', 'Separator')],
        help=(
            "Symbols that are used as delimiters in B2B File. "
            "The stored symbols are written in ASCII codes, "
            "so you should convert them to characters that can be used as delimiters."
        )
    )
    separator_name = fields.Char(string="Separator Name", compute='_compute_separator_name')
    limit = fields.Integer('Processing Limit', default=0)

    @api.depends('separator_id')
    def _compute_separator_name(self):
        for record in self:
            record.separator_name = record.separator_id.name
