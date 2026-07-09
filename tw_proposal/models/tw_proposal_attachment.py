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


class TwProposalAttachment(models.Model):
    _name = "tw.proposal.attachment"
    _description = "Proposal Online - Attachment"

    def _compute_files(self):
        for x in self:       
            if x.filename:
                x.files = self.env['tw.config.files'].suspend_security().get_file('PROPOSAL', x.filename)

    is_files_fix = fields.Boolean()
    files_upload = fields.Binary('Upload Berkas')
    filename_upload = fields.Char('Nama Berkas Upload')
    files = fields.Binary('Download Berkas', compute='_compute_files') #, store=False
    filename = fields.Char('Nama Berkas')
    remark = fields.Text(string='Keterangan')
    
    proposal_id = fields.Many2one('tw.proposal', string='Nomor Proposal', ondelete='cascade')

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            if not vals.get('files_upload'):
                raise Warning('Perhatian!\nAnda belum upload berkas apapun.')

            files = vals.get('files_upload')
            
            filename_upload_tokens = str(vals.get('filename_upload')).split('.')
            now = date.today().strftime("%Y-%m-%d")
            filename = str('teds_proposal-')+str(vals['proposal_id'])+now+'.'+filename_upload_tokens[len(filename_upload_tokens) - 1]

            self.env['tw.config.files'].suspend_security().upload_file('PROPOSAL', filename, files)
            vals['files_upload'] = False
            vals['filename_upload'] = filename
            vals['files'] = False
            vals['filename'] = filename
        return super(TwProposalAttachment, self).create(vals)

    def write(self,vals):
        # if not vals.get('is_files_fix'):
        if not vals.get('files_upload'):
            raise Warning('Perhatian!\nAnda belum upload berkas apapun.')

        files = vals.get('files_upload')
        # replace files
        filename_db = self.search([('id','=',self.id)]).filename
        filename_db_tokens = str(filename_db).split('.')
        filename_upload_tokens = str(vals.get('filename_upload')).split('.')
        filename = filename_db_tokens[0]+'.'+filename_upload_tokens[len(filename_upload_tokens) - 1]
        
        self.env['tw.config.files'].suspend_security().upload_file('PROPOSAL', filename, files)
        vals['files_upload'] = False
        vals['filename_upload'] = filename
        vals['files'] = False
        vals['filename'] = filename
        
        return super(TwProposalAttachment, self).write(vals)

    def export_file(self):
        return {
            'type': 'ir.actions.act_url',
            "target": "new",
            'url': '/web/content/tw.proposal.attachment/%s/files/%s?download=true' % (self.id, self.filename)
        }

