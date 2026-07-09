# -*- coding: utf-8 -*-

# 1: imports of python lib
import base64
from io import BytesIO
import openpyxl

# 2: import of known third party lib
from datetime import date

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class UploadMinimumWage(models.TransientModel):
    _name = "tw.upload.minimum.wage"
    _description = "Upload Minimum Wage"

    # 7: defaults methods

    # 8: fields
    file = fields.Binary('File')
    state_x = fields.Selection([('choose', 'choose'), ('get', 'get')], default=lambda self: self._context.get('default_state_x', 'choose'))
    message = fields.Text('Message', readonly=True, help="Message to be displayed after import.")
    
    # 9: relation fields
    
    # 10: constraints & sql constraints
    
    # 11: compute/depends & on change methods
    
    # 12: override methods
    
    # 13: action methods
    def action_download_format_file(self):
        format = self.env['tw.format.upload'].suspend_security().search([('name', '=', 'minimum wage'), ('active', '=', True)], limit=1)
        if format:
            return {
                'type': 'ir.actions.act_url',
                'name': 'contract',
                'url': f'/web/content/tw.format.upload/{format.id}/file_format_show/{format.filename_upload_format}'
            }
        else:
            raise Warning(_("Sorry, the format is not available yet. Please contact the Helpdesk."))

    def action_import(self):
        if not self.file:
            raise Warning(_("Silahkan input file terlebih dahulu."))
            
        data = base64.b64decode(self.file)
        try:
            wb = openpyxl.load_workbook(BytesIO(data), data_only=True)
            sh = wb.active
        except Exception as e:
            raise Warning(f"Error reading excel file: {str(e)}")
        
        warning_note = ''
        rows = list(sh.iter_rows(min_row=2, values_only=True))
        
        for idx, values in enumerate(rows, start=2):
            if not values or not any(v is not None for v in values):
                continue
                
            branch_code = values[0]
            minimum_wage = float(values[1]) if values[1] is not None else 0.0

            branch = self.env['res.company'].suspend_security().search([('code', '=', str(branch_code))], limit=1)
            
            if not branch:
                warning_note += f"Baris ke {idx}: Branch dengan kode {branch_code} tidak ditemukan.\n"
                continue
            if not branch.branch_setting_id:
                warning_note += f"Baris ke {idx}: Branch dengan kode {branch_code} tidak memiliki branch setting.\n"
                continue

            branch.branch_setting_id.write({'regional_minimum_wages': minimum_wage})
            
        return {
            'type': 'ir.actions.act_window',
            'name': 'Minimum Wage',
            'res_model': 'tw.upload.minimum.wage',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_message': _("Minimum wage data has been successfully updated.\n"
                                     f"{warning_note}"),
                'default_state_x': 'get'
            }
        }
    
    # 14: private methods
