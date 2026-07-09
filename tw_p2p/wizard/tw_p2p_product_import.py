# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib
import xlrd
import base64

# 3: imports of odoo
from odoo import models, fields, api, _

# 4: imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class TwP2pProductImport(models.TransientModel):
    _name = "tw.p2p.product.import"
    _description = "P2P Product Import TEDS 2.0 Format"

    file = fields.Binary('File', required=True)
    filename = fields.Char('Filename')
    company_id = fields.Many2one(
        'res.company', 
        string='Company', 
        required=True,
        default=lambda self: self.env.company if not self.env.company.parent_id else self.env.company.parent_id,
        domain="[('parent_id', '=', False)]"
    )
    division = fields.Selection([
        ('Unit', 'Unit'),
        ('Sparepart', 'Sparepart')
    ], string='Division', required=True, default='Unit')
    state = fields.Selection([
        ('choose', 'Choose'),
        ('preview', 'Preview'),
        ('done', 'Done')
    ], default='choose')
    preview_data = fields.Html(string='Preview Data', readonly=True)
    import_result = fields.Text(string='Import Result', readonly=True)

    def action_preview(self):
        """Preview first 10 rows of import data"""
        if not self.file:
            raise Warning('Silahkan upload file terlebih dahulu.')
        
        ext = self.filename.split('.')[-1].lower()
        if ext not in ('xls', 'xlsx'):
            raise Warning('Format file harus XLS atau XLSX.')
        
        wb = xlrd.open_workbook(file_contents=base64.decodebytes(self.file))
        sheet = wb.sheet_by_index(0)
        
        # Build preview table
        html = '<table class="table table-sm table-bordered" style="font-size:12px;">'
        html += '<thead><tr style="background:#f5f5f5;">'
        html += '<th>No</th><th>Product Code</th><th>Color Code</th><th>Start Date</th><th>End Date</th><th>Status</th>'
        html += '</tr></thead><tbody>'
        
        preview_count = 0
        for rx in range(1, min(11, sheet.nrows)):  # Show max 10 data rows
            values = [sheet.cell(rx, ry).value for ry in range(sheet.ncols)]
            
            product_code = str(values[0]).strip() if len(values) > 0 else ''
            color_code = str(values[1]).strip() if len(values) > 1 else ''
            start_date_val = values[2] if len(values) > 2 else ''
            end_date_val = values[3] if len(values) > 3 else ''
            
            # Skip header row
            if product_code.lower() in ('name', 'product code', 'kode', ''):
                continue
            
            # Try to find product based on division
            if self.division == 'Unit':
                product_id = self.env['product.product']._get_unit_product_id(product_code, color_code)
            else:  # Sparepart
                product_id = self.env['product.product']._get_sparepart_product_id(product_code)
            status = '<span style="color:green;">✓ Found</span>' if product_id else '<span style="color:red;">✗ Not Found</span>'
            
            # Format dates
            start_date_str = self._format_date(start_date_val)
            end_date_str = self._format_date(end_date_val)
            
            html += '<tr>'
            html += f'<td>{preview_count + 1}</td>'
            html += f'<td><b>{product_code}</b></td>'
            html += f'<td>{color_code}</td>'
            html += f'<td>{start_date_str}</td>'
            html += f'<td>{end_date_str}</td>'
            html += f'<td>{status}</td>'
            html += '</tr>'
            preview_count += 1
        
        html += '</tbody></table>'
        html += f'<p class="text-muted">Menampilkan {preview_count} data pertama dari {sheet.nrows - 1} baris</p>'
        
        self.preview_data = html
        self.state = 'preview'
        
        return self._return_wizard()

    def action_import(self):
        """Import P2P Products from Excel"""
        if not self.file:
            raise Warning('Silahkan upload file terlebih dahulu.')
        
        ext = self.filename.split('.')[-1].lower()
        if ext not in ('xls', 'xlsx'):
            raise Warning('Format file harus XLS atau XLSX.')
        
        wb = xlrd.open_workbook(file_contents=base64.decodebytes(self.file))
        sheet = wb.sheet_by_index(0)
        
        success_count = 0
        skip_count = 0
        error_count = 0
        messages = []
        
        for rx in range(1, sheet.nrows):
            values = [sheet.cell(rx, ry).value for ry in range(sheet.ncols)]
            
            product_code = str(values[0]).strip() if len(values) > 0 else ''
            color_code = str(values[1]).strip() if len(values) > 1 else ''
            start_date_val = values[2] if len(values) > 2 else ''
            end_date_val = values[3] if len(values) > 3 else ''
            
            # Skip header row
            if product_code.lower() in ('name', 'product code', 'kode', ''):
                continue
            
            # Validate product code
            if not product_code:
                error_count += 1
                messages.append(f'Baris {rx}: Product Code kosong')
                continue
            
            # Find product based on division
            if self.division == 'Unit':
                product_id = self.env['product.product']._get_unit_product_id(product_code, color_code)
                if not product_id:
                    error_count += 1
                    messages.append(f'Baris {rx}: Product {product_code} dengan warna {color_code} tidak ditemukan')
                    continue
            else:  # Sparepart
                product_id = self.env['product.product']._get_sparepart_product_id(product_code)
                if not product_id:
                    error_count += 1
                    messages.append(f'Baris {rx}: Product {product_code} tidak ditemukan')
                    continue
            
            # Parse dates
            start_date = self._parse_date(start_date_val)
            end_date = self._parse_date(end_date_val)
            
            if not start_date or not end_date:
                error_count += 1
                messages.append(f'Baris {rx}: Format tanggal tidak valid')
                continue
            
            # Check if already exists
            existing = self.env['tw.p2p.product'].search([
                ('product_id', '=', product_id),
                ('company_ids', 'in', self.company_id.id)
            ], limit=1)
            
            if existing:
                # Check if dates are different
                if existing.start_date != start_date or existing.end_date != end_date:
                    # Update existing with different dates
                    existing.write({
                        'start_date': start_date,
                        'end_date': end_date,
                        'active': True
                    })
                    skip_count += 1
                    messages.append(f'Baris {rx}: {product_code}-{color_code} tanggal diupdate')
                else:
                    # Skip - dates are same
                    skip_count += 1
                    messages.append(f'Baris {rx}: {product_code}-{color_code} sudah ada (skip)')
            else:
                # Create new
                self.env['tw.p2p.product'].create({
                    'product_id': product_id,
                    'company_ids': [(6, 0, [self.company_id.id])],
                    'start_date': start_date,
                    'end_date': end_date,
                    'active': True
                })
                success_count += 1
        
        # Build result summary
        result = f"""
Import Selesai!
===============
✓ Berhasil dibuat: {success_count}
↺ Diupdate: {skip_count}
✗ Error: {error_count}

Detail:
{chr(10).join(messages[-20:]) if messages else 'Tidak ada pesan error'}
"""
        
        self.import_result = result
        self.state = 'done'
        
        return self._return_wizard()

    def action_back(self):
        """Go back to choose state"""
        self.state = 'choose'
        self.preview_data = False
        return self._return_wizard()

    def _return_wizard(self):
        """Return wizard action"""
        return {
            'name': 'Import P2P Product - TEDS 2.0 Format',
            'res_model': 'tw.p2p.product.import',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'res_id': self.id,
        }

    def _format_date(self, value):
        """Format date value for display"""
        try:
            if isinstance(value, float):
                # Excel date serial number
                date_tuple = xlrd.xldate_as_tuple(value, 0)
                return f'{date_tuple[2]:02d}/{date_tuple[1]:02d}/{date_tuple[0]}'
            elif isinstance(value, str) and value:
                return value
        except:
            pass
        return str(value)

    def _parse_date(self, value):
        """Parse date from Excel cell"""
        try:
            if isinstance(value, float):
                # Excel date serial number
                date_tuple = xlrd.xldate_as_tuple(value, 0)
                return fields.Date.to_date(datetime(date_tuple[0], date_tuple[1], date_tuple[2]))
            elif isinstance(value, str) and value:
                # Try common date formats: DD/MM/YYYY or YYYY-MM-DD
                for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
                    try:
                        dt = datetime.strptime(value.strip(), fmt)
                        return fields.Date.to_date(dt)
                    except:
                        continue
        except Exception as e:
            pass
        return None
