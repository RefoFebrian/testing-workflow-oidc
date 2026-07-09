# 1: imports of python lib
import base64
import openpyxl
import xlrd
import logging

# 2: import of known third party lib
from datetime import date
from io import BytesIO
from itertools import groupby
from operator import itemgetter

# 3:  imports of odoo
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError as Warning

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

_logger = logging.getLogger(__name__)

class TwUploadTargetSalesPeopleWizard(models.TransientModel):
    _name = "tw.upload.target.sales.people.wizard"
    _description = "Upload Target Sales People"

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    # 8: fields
    upload_file = fields.Binary('File to Upload')
    filename  = fields.Char('Nama File')
    message = fields.Text()

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods

    # 13: action methods
    def action_download_format_file(self):
        """Download the template file for target sales people upload"""
        format = self.env['tw.format.upload'].sudo().search([
            ('name', '=', 'target sales people'),
            ('active', '=', True)
        ], limit=1)
        
        if format and format.file_format_show and format.filename_upload_format:
            return {
                'type': 'ir.actions.act_url',
                'name': 'target_sales_people_template',
                'url': f'/web/content/tw.format.upload/{format.id}/file_format_show/{format.filename_upload_format}?download=true'
            }
        else:
            raise Warning(_("Format template belum tersedia. Silakan hubungi Helpdesk."))

    def action_import(self):
        self.ensure_one()
        
        if not self.file:
            raise ValidationError(_("Silakan unggah file Excel terlebih dahulu"))

        try:
            # Read the Excel file
            file_data = base64.b64decode(self.file)
            book = xlrd.open_workbook(file_contents=file_data)
            sheet = book.sheet_by_index(0)
            
            # Initialize counters and logs
            success_count = 0
            updated_count = 0
            error_lines = []
            
            # Process each row (skip header row)
            for row_idx in range(1, sheet.nrows):
                try:
                    row = sheet.row_values(row_idx)
                    if len(row) < 4:  # Skip incomplete rows
                        error_lines.append(f"Baris {row_idx + 1}: Data tidak lengkap")
                        continue
                        
                    branch_code = str(row[0]).strip()
                    job_position = str(row[1]).strip()
                    target_type = str(row[2]).strip()
                    target_value = float(row[3] or 0)
                    
                    # Find company
                    company = self.env['res.company'].search([('code', '=', branch_code)], limit=1)
                    if not company:
                        error_lines.append(f"Baris {row_idx + 1}: Kode Cabang '{branch_code}' tidak ditemukan")
                        continue
                        
                    # Find job position
                    job = self.env['hr.job'].search([('name', '=', job_position)], limit=1)
                    if not job:
                        error_lines.append(f"Baris {row_idx + 1}: Posisi/Jabatan '{job_position}' tidak ditemukan")
                        continue
                    else:
                        master_target = self.env['tw.master.target'].search([
                            ('name', '=', job.name)
                        ], limit=1)
                        if not master_target:
                            self.env["tw.master.target"].suspend_security().create({
                                "name": job.name
                            })
                    
                    # Find or create target
                    target = self.env['tw.target.sales.people'].search([
                        ('company_id', '=', company.id),
                        ('job_id', '=', job.id),
                        ('target_type', '=', job.name)
                    ], limit=1)
                    
                    if not target:
                        target = self.env['tw.target.sales.people'].create({
                            'company_id': company.id,
                            'job_id': job.id,
                            'target_type': job.name
                        })
                    
                    # Find or create target line
                    target_line = self.env['tw.target.sales.people.line'].search([
                        ('target_id', '=', target.id),
                        ('type', '=', target_type),
                    ], limit=1)
                    
                    if target_line:
                        target_line.write({
                            'target': target_value,
                        })
                        updated_count += 1
                    else:
                        self.env['tw.target.sales.people.line'].create({
                            'target_id': target.id,
                            'type': target_type,
                            'target': target_value,
                        })
                        success_count += 1
                        
                except ValueError as e:
                    error_lines.append(f"Baris {row_idx + 1}: Format angka tidak valid - {str(e)}")
                    _logger.error(f"Error processing row {row_idx + 1}: {e}", exc_info=True)
                except Exception as e:
                    error_lines.append(f"Baris {row_idx + 1}: {str(e)}")
                    _logger.error(f"Error processing row {row_idx + 1}", exc_info=True)
            
            # Prepare result message
            result_message = []
            if success_count > 0:
                result_message.append(_(f"Berhasil menambahkan {success_count} data target baru."))
            if updated_count > 0:
                result_message.append(_(f"Berhasil memperbarui {updated_count} data target yang sudah ada."))
            
            if error_lines:
                result_message.append(_("\nTerjadi kesalahan pada baris berikut:"))
                result_message.append("\n".join(error_lines))  # Show all errors
            
            self.message = "\n".join(result_message)
            
            # Return action to show the wizard with results
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'tw.upload.target.sales.people.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'new',
            }
            
        except Exception as e:
            _logger.error("Error in target sales people import: %s", str(e), exc_info=True)
            raise ValidationError(_("Terjadi kesalahan saat memproses file: %s") % str(e))

    # 14: private methods
    def _read_cell_value(self, value, force_zero_padding=False, use_fraction=False):
        if value is None or value == '':
            return ''
        if isinstance(value, (int, float)) and not use_fraction:
            return str(int(value))
        return str(value).strip()
