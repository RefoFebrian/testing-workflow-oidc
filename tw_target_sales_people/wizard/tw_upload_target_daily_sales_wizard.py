# 1: imports of python lib
import base64
import openpyxl
import xlrd
import logging

# 2: import of known third party lib
from datetime import date, datetime
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

class TwUploadTargetDailySalesWizard(models.TransientModel):
    _name = "tw.upload.target.daily.sales.wizard"
    _description = "Upload Target Daily Sales Wizard"

    # 7: defaults methods 
    def _get_default_year(self):
        return str(datetime.now().year)

    # 8: fields
    upload_file = fields.Binary('File to Upload')
    filename  = fields.Char('Nama File')
    message = fields.Text()
    year = fields.Selection(
        selection='_get_year_selection',
        string='Tahun', 
        default=_get_default_year
    )

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    def _get_year_selection(self):
        return [(str(year), str(year)) for year in range(2010, datetime.now().year + 2)]

    # 12: override methods

    # 13: action methods
    def action_download_format_file(self):
        """Download the template file for target daily sales upload"""
        format = self.env['tw.format.upload'].sudo().search([
            ('name', '=', 'target daily sales'),
            ('active', '=', True)
        ], limit=1)
        
        if format and format.file_format_show and format.filename_upload_format:
            return {
                'type': 'ir.actions.act_url',
                'name': 'target_daily_sales_template',
                'url': f'/web/content/tw.format.upload/{format.id}/file_format_show/{format.filename_upload_format}?download=true'
            }
        else:
            raise Warning(_("Format template belum tersedia. Silakan hubungi Helpdesk."))

    def action_import(self):
        self.ensure_one()

        if not self.upload_file:
            raise Warning(_("Silakan unggah file Excel terlebih dahulu"))

        try:
            # Read the Excel file
            file_data = base64.b64decode(self.upload_file)
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

                    company_code = str(row[0]).strip()
                    month = str(row[1]).strip()
                    series = str(row[2]).strip()
                    target_value = int(float(row[3] or 0))

                    # Find company
                    company = self.env['res.company'].search([('code', '=', company_code)], limit=1)
                    if not company:
                        error_lines.append(f"Baris {row_idx + 1}: Kode Cabang '{company_code}' tidak ditemukan")
                        continue

                    series = self.env['product.template'].search([('name', '=', series)], limit=1)
                    if not series:
                        error_lines.append(f"Baris {row_idx + 1}: Series '{series}' tidak ditemukan")
                        continue

                    # Validate month
                    try:
                        month_int = int(month)
                        if month_int < 1 or month_int > 12:
                            raise ValueError
                    except (ValueError, TypeError):
                        error_lines.append(f"Baris {row_idx + 1}: Bulan harus antara 1-12")
                        continue

                    # Find or create target daily sales
                    target_daily_sales = self.env['tw.target.daily.sales'].search([
                        ('company_id', '=', company.id),
                        ('year', '=', self.year)
                    ], limit=1)

                    if not target_daily_sales:
                        target_daily_sales = self.env['tw.target.daily.sales'].create({
                            'company_id': company.id,
                            'year': self.year
                        })

                    target_daily_sales_line = self.env['tw.target.daily.sales.line'].search([
                        ('target_daily_sales_id', '=', target_daily_sales.id),
                        ('series', '=', series.id),
                        ('month', '=', month)
                    ], limit=1)
                    if target_daily_sales_line:
                        target_daily_sales_line.write({
                                'target': target_value,
                            })
                        updated_count += 1
                    else:
                        self.env['tw.target.daily.sales.line'].create({
                            'target_daily_sales_id': target_daily_sales.id,
                            'series': series.id,
                            'month': str(month),
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
                'res_model': 'tw.upload.target.daily.sales.wizard',
                'view_mode': 'form',
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'new',
            }

        except Exception as e:
            _logger.error("Error in target daily sales import: %s", str(e), exc_info=True)
            raise ValidationError(_("Terjadi kesalahan saat memproses file: %s") % str(e))

    # 14: private methods
    def _read_cell_value(self, value, force_zero_padding=False, use_fraction=False):
        if value is None or value == '':
            return ''
        if isinstance(value, (int, float)) and not use_fraction:
            return str(int(value))
        return str(value).strip()