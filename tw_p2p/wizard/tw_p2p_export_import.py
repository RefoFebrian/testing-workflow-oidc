# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime

# 2: import of known third party lib
import xlrd
import base64

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports
import logging
_logger = logging.getLogger(__name__)


# 6: Import of unknown third party lib

class P2pExportImport(models.TransientModel):
    _name = "tw.p2p.export.import"
    _description ="P2P Purchase Order Export Import"

    def _get_default_date(self):
        return datetime.now()

    file = fields.Binary('file')
    filename = fields.Char('Filename')
    upload_date = fields.Date(string='Tanggal Upload', default=_get_default_date)
    state_x = fields.Selection([
        ('choose','choose'),
        ('preview','preview'),
        ('get','get')
    ], default='choose')
    message = fields.Text(string='Message')
    preview_data = fields.Html(string='Preview Data', readonly=True)
    purchase_order_type_id = fields.Many2one('tw.purchase.order.type','Type',required=True,domain="[('company_id', 'in', [company_id, False]),('category','=',division),'|',('name','=','Fix'),('name','=','Additional')]")
    purchase_order_id = fields.Many2one('tw.p2p.purchase.order','Purchase Order')


    def action_export(self):
        report = False
        if self.purchase_order_type_id.name == 'Additional':
            report = self.action_export_additional()
        elif self.purchase_order_type_id.name == 'Fix':
            report = self.action_export_fix()
        else:
             raise Warning('Tidak dapat melakukan export untuk type {type}'.format(type=self.purchase_order_type_id.name))
        
        return report

    def action_export_additional(self):
        """
        Export Additional P2P - Format untuk import:
        - product (product template name)
        - color_code (untuk Unit) / empty string (untuk Sparepart)
        - fix_qty
        - id_line_do_not_delete
        """
        purchase_order = self.purchase_order_id
        ress = []
        
        for line in purchase_order.additional_line_ids:
            product = line.product_id
            color_code = ''
            
            if purchase_order.division == 'Unit':
                # Get color code from product variant's attribute values
                for attr_value in product.product_template_attribute_value_ids:
                    if attr_value.attribute_id.name in ('Color', 'Warna', 'Colour'):
                        color_code = attr_value.product_attribute_value_id.code or ''
                        break
                product_name = product.product_tmpl_id.name
            else:
                product_name = product.default_code or product.name
            
            ress.append({
                'product': product_name,
                'code_product': product.default_code or '',
                'color_code': color_code,
                'fix_qty': line.fix_qty or 0,
                'id_line_do_not_delete': line.id
            })
        
        if not ress:
            ress.append({
                'product': 'COVER,INNER LOWER (Contoh)',
                'code_product': '42078KRM901 (Contoh)',
                'color_code': '',
                'fix_qty': 10,
                'id_line_do_not_delete': ''
            })

        return self.env['web.report'].sudo().generate_report('Template P2P Additional', ress)
    
    def action_export_fix(self):
        """
        Export Fix P2P - Format untuk import:
        - product (product template name)
        - color_code
        - fix_qty
        - tent_1_qty
        - tent_2_qty
        - id_line_do_not_delete
        """
        purchase_order = self.purchase_order_id
        if not purchase_order.purchase_line_ids:
            raise Warning("P2P PO Fix perlu Generate Line terlebih dahulu !")
        
        ress = []
        
        for line in purchase_order.purchase_line_ids:
            product = line.product_id
            color_code = ''
            
            # Get color code from product variant's attribute values
            for attr_value in product.product_template_attribute_value_ids:
                if attr_value.attribute_id.name in ('Color', 'Warna', 'Colour'):
                    color_code = attr_value.product_attribute_value_id.code or ''
                    break
            
            ress.append({
                'product': product.product_tmpl_id.name,
                'code_product': product.default_code or '',
                'color_code': color_code,
                'fix_qty': line.fix_qty or 0,
                'tent_1_qty': line.tent1_qty or 0,
                'tent_2_qty': line.tent2_qty or 0,
                'id_line_do_not_delete': line.id
            })

        return self.env['web.report'].sudo().generate_report('Template P2P FIX', ress)
    
    def action_preview(self):
        """
        Preview first 5 rows of import data before actual import
        """
        if not self.file:
            raise Warning('Silahkan input file terlebih dahulu.')
        
        p2p_obj = self.purchase_order_id
        if not p2p_obj:
            raise Warning("tidak terdapat transaksi P2P")
        
        ext = self.filename.split('.')
        ext = ext[len(ext)-1].lower()
        
        if ext not in ('xls', 'xlsx'):
            raise Warning('Format %s tidak dikenal.' % ext.upper())
        
        wb = xlrd.open_workbook(file_contents=base64.decodebytes(self.file))
        sheet = wb.sheet_by_index(0)
        
        is_fix = p2p_obj.type_name == 'Fix'
        
        # Build preview table
        html = '<table class="table table-sm table-bordered" style="font-size:12px;">'
        html += '<thead><tr style="background:#f5f5f5;">'
        if is_fix:
            html += '<th>No</th><th>Product</th><th>Code</th><th>Color</th><th>Fix Qty</th><th>Tent 1</th><th>Tent 2</th>'
        else:
            html += '<th>No</th><th>Product</th><th>Code</th><th>Color</th><th>Fix Qty</th>'
        html += '</tr></thead><tbody>'
        
        max_preview = min(10, sheet.nrows)  # Check more rows to find data
        data_count = 0
        for rx in range(1, sheet.nrows):
            if data_count >= 5:  # Only show 5 data rows
                break
                
            values = [sheet.cell(rx, ry).value for ry in range(sheet.ncols)]
            
            no_column = values[0] if len(values) > 0 else ''
            
            # Skip non-data rows (header, empty, datetime strings, text headers)
            if not no_column:
                continue
            if isinstance(no_column, str):
                # Skip if it's text like 'N', 'No', 'Total', datetime string, etc.
                if no_column.lower() in ('n', 'no', 'total', '') or '-' in no_column:
                    continue
            
            # Try to convert to int - if fails, skip this row
            try:
                row_num = int(float(no_column))
            except (ValueError, TypeError):
                continue
            
            product_name = values[1] if len(values) > 1 else ''
            code_product = values[2] if len(values) > 2 else ''
            color_code = values[3] if len(values) > 3 else ''
            fix_qty = values[4] if len(values) > 4 else 0
            
            html += '<tr>'
            html += f'<td>{row_num}</td>'
            html += f'<td>{product_name}</td>'
            html += f'<td><b>{code_product}</b></td>'
            html += f'<td>{color_code}</td>'
            html += f'<td>{fix_qty}</td>'
            
            if is_fix:
                tent_1 = values[5] if len(values) > 5 else 0
                tent_2 = values[6] if len(values) > 6 else 0
                html += f'<td>{tent_1}</td><td>{tent_2}</td>'
            
            html += '</tr>'
            data_count += 1
        
        html += '</tbody></table>'
        html += f'<p class="text-muted">Menampilkan {data_count} data pertama</p>'
        
        self.preview_data = html
        self.state_x = 'preview'
        
        form_id = self.env.ref('tw_p2p.tw_p2p_purchase_order_export_import_wizard_form_view').id
        return {
            'name': ('Export / Import'),
            'res_model': 'tw.p2p.export.import',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': False,
            'views': [(form_id, 'form')],
            'target': 'new',
            'res_id': self.ids[0],
        }
    
    def action_back(self):
        """Go back to choose state"""
        self.state_x = 'choose'
        self.preview_data = False
        
        form_id = self.env.ref('tw_p2p.tw_p2p_purchase_order_export_import_wizard_form_view').id
        return {
            'name': ('Export / Import'),
            'res_model': 'tw.p2p.export.import',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': False,
            'views': [(form_id, 'form')],
            'target': 'new',
            'res_id': self.ids[0],
        }
        
    def action_import(self):
        """
        Import Unit / Sparepart digunakan untuk update Purchase Line
        """
        if not self.file:
            raise Warning('Silahkan input file terlebih dahulu.')
        
        if not self.purchase_order_type_id:
             raise Warning('Silahkan input Type terlebih dahulu.')

        p2p_obj = self.purchase_order_id
        if not p2p_obj:
            raise Warning("tidak terdapat transaksi P2P")
        
        # Column mapping based on division and type
        # Fix Unit: no, product, color_code, fix_qty, tent_1_qty, tent_2_qty, id_line
        # Additional Unit: no, product, color_code, fix_qty, id_line
        # Sparepart: no, product, color_code (empty), fix_qty, id_line
        
        is_fix = p2p_obj.type_name == 'Fix'
        
        ext = self.filename.split('.')
        ext = ext[len(ext)-1].lower()
        if self.file:
            wb = xlrd.open_workbook(file_contents=base64.decodebytes(self.file))
        else:
            raise Warning("Pilih file untuk di upload terlebih dahulu!")
        
        if ext not in ('xls', 'xlsx'):
            raise Warning('Format %s tidak dikenal. Mohon gunakan format file yang sudah disediakan!\nKlik Download Contoh di sebelah kanan wizard untuk mengunduh.' % ext.upper())
        sheet = wb.sheet_by_index(0)
        
        msg = ''
        line = []
        
        # Clear existing lines
        p2p_obj.purchase_line_ids.unlink()
        
        for rx in range(1, sheet.nrows):
            values = [sheet.cell(rx, ry).value for ry in range(sheet.ncols)]
            
            # Common columns for all types
            # Template has: N | Product | Code Product | Color code | Fix qty | ...
            no_column = values[0] if len(values) > 0 else None
            # values[1] = product name (skip, for display only)
            code_product = values[2] if len(values) > 2 else None
            color_code = values[3] if len(values) > 3 else None
            fix_qty = values[4] if len(values) > 4 else 0
            
            # Additional columns for Fix Unit
            tent_1_qty = 0
            tent_2_qty = 0
            if is_fix:
                tent_1_qty = values[5] if len(values) > 5 else 0
                tent_2_qty = values[6] if len(values) > 6 else 0
            
            # Validation - skip header or empty rows
            if not no_column or no_column == '' or isinstance(no_column, str):
                continue
            
            if not code_product:
                msg += '\n Baris ke %s: Code Product tidak boleh kosong' % (int(no_column))
                continue
            
            # Get product based on division
            product_id = False
            if p2p_obj.division == 'Unit':
                if not color_code:
                    msg += '\n Baris ke %s: Color Code tidak boleh kosong untuk Unit' % (int(no_column))
                    continue
                product_id = self.env['product.product']._get_unit_product_id(code_product, color_code)
            elif p2p_obj.division == 'Sparepart':
                product_id = self.env['product.product']._get_sparepart_product_id(code_product)

            if not product_id:
                msg += '\n Baris ke %s: Product dengan Code: %s dan Warna %s tidak ditemukan.\n' % (int(no_column), code_product, color_code or '-')
                continue

            line.append([0, 0, {
                'product_id': product_id,
                'fix_qty': fix_qty,
                'tent1_qty': tent_1_qty,
                'tent2_qty': tent_2_qty,
                'active': True
            }])
        
        if msg:
            raise Warning(msg)
        
        if line:
            p2p_obj.write({
                'purchase_line_ids': line
            })
            self.message = "%s Data berhasil di import." % len(line)
        else:
            self.message = "Tidak ada data yang di import."
        
        self.state_x = 'get'

        form_id = self.env.ref('tw_p2p.tw_p2p_purchase_order_export_import_wizard_form_view').id
        return {
            'name': ('Export / Import'),
            'res_model': 'tw.p2p.export.import',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': False,
            'views': [(form_id, 'form')],
            'target': 'current',
            'res_id': self.ids[0],
        }

    def get_excel_column(self, n):
        string = ""
        while n > 0:
            n, remainder = divmod(n - 1, 26)
            string = chr(65 + remainder) + string
        return string