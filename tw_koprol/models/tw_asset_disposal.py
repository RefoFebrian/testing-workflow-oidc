from odoo import models, fields, api
from datetime import datetime, timedelta

import requests
import base64
import binascii

import logging
_logger = logging.getLogger(__name__)

class InheritTwDisposalAsset(models.Model):
    _name = "tw.asset.disposal"
    _inherit = ["tw.asset.disposal","tw.attachment.mixin"]

    koprol_code = fields.Char('Koprol Code')
    last_modified_date = fields.Datetime('Last Modified Date Koprol')


    def create_attachment_file_disposal_assets(self, attachments):
        self.ensure_one()
        attachment_vals_list = []

        for attachment_data in attachments:
            filename = attachment_data.get('filename')
            source = attachment_data.get('source') 

            if not filename or not source or not isinstance(source, str):
                continue

            vals = {'name': filename}
            source_trimmed = source.strip()

            if source_trimmed.startswith(('http://', 'https://')):
                vals['type'] = 'url'
                vals['url'] = source_trimmed
                attachment_vals_list.append(vals)
            else:
                try:                   
                    base64.b64decode(source_trimmed, validate=True)
                    vals['type'] = 'binary'
                    vals['datas'] = source_trimmed
                    attachment_vals_list.append(vals)
                except (binascii.Error, TypeError):
                    _logger.warning(f"Skipping attachment '{filename}' for Disposal {self.name}: "
                                    f"Source is not a valid URL or Base64 string.")
                    continue

        if attachment_vals_list:
            self.write({
                'attachment_ids': [Command.create(vals) for vals in attachment_vals_list]
            })
            _logger.info(f"{len(attachment_vals_list)} attachments successfully processed for Disposal {self.name}")

        return True

