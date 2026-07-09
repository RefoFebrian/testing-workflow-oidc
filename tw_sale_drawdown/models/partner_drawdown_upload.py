# -*- coding: utf-8 -*-

import base64
import logging
import xlrd
from io import BytesIO
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class PartnerDrawdownUploadWizard(models.TransientModel):
    _name = "partner.drawdown.upload.wizard"
    _description = "Partner Drawdown Upload Wizard"

    upload_file = fields.Binary('File Excel',
        help="File Excel dengan format:\n- Kolom 1: Kode Partner\n- Kolom 2: Drawdown Unit\n- Kolom 3: Drawdown Sparepart")
    filename = fields.Char('Nama File')

    def action_download_format_file(self):
        """Download the template file for partner drawdown upload"""
        format = self.env['tw.format.upload'].sudo().search([
            ('name', '=', 'partner drawdown'),
            ('active', '=', True)
        ], limit=1)
        
        if format and format.file_format_show and format.filename_upload_format:
            return {
                'type': 'ir.actions.act_url',
                'name': 'drawdown_template',
                'url': f'/web/content/tw.format.upload/{format.id}/file_format_show/{format.filename_upload_format}?download=true'
            }
        else:
            raise UserError(_("Format template belum tersedia. Silakan hubungi tim IT."))
    
    def action_import(self):
        self.ensure_one()
        
        if not self.upload_file:
            raise ValidationError(_("Silakan unggah file Excel terlebih dahulu"))

        try:
            # Read the Excel file
            file_data = base64.b64decode(self.upload_file)
            book = xlrd.open_workbook(file_contents=file_data)
            sheet = book.sheet_by_index(0)
            
            # Process each row (skip header row)
            partner = self.env['res.partner']
            success_count = 0
            error_lines = []
            
            for row_idx in range(1, sheet.nrows):  # Skip header row
                try:
                    row = sheet.row_values(row_idx)
                    if len(row) < 3:  # Skip empty rows
                        continue
                        
                    partner_code = str(row[0]).strip()
                    drawdown_unit = float(row[1] or 0)
                    drawdown_sparepart = float(row[2] or 0)
                    
                    # Find partner by code
                    partner_obj = partner.suspend_security().search([('code', '=', partner_code)], limit=1)
                    
                    if not partner_obj:
                        error_lines.append(f"Baris {row_idx + 1}: Kode Partner '{partner_code}' tidak ditemukan")
                        continue
                        
                    # Update partner with drawdown values
                    partner_obj.write({
                        'drawdown_unit': drawdown_unit,
                        'drawdown_sparepart': drawdown_sparepart,
                    })
                    success_count += 1
                    
                except ValueError as e:
                    error_lines.append(f"Baris {row_idx + 1}: Format data tidak valid - {str(e)}")
                    _logger.error(f"Error processing row {row_idx + 1}: {e}", exc_info=True)
                except Exception as e:
                    error_lines.append(f"Baris {row_idx + 1}: {str(e)}")
                    _logger.error(f"Error processing row {row_idx + 1}", exc_info=True)
            
            # Prepare result message
            if success_count > 0 or error_lines:
                result_message = _("Berhasil memperbarui %d partner.\n\n") % success_count
                if error_lines:
                    result_message += _("Terjadi kesalahan pada baris berikut:")
                    result_message += "\n" + "\n".join(error_lines[:10])  # Show first 10 errors
                    if len(error_lines) > 10:
                        result_message += _("\n...dan %d kesalahan lainnya") % (len(error_lines) - 10)
                
                # Show result to user
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Hasil Import'),
                        'message': result_message,
                        'sticky': True,
                        'next': {'type': 'ir.actions.act_window_close'},
                    }
                }
            
        except Exception as e:
            _logger.error("Error in partner drawdown import: %s", str(e), exc_info=True)
            raise ValidationError(_("Error processing file: %s") % str(e))
