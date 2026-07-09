from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
from io import BytesIO
try:
    import openpyxl
except Exception as e:
    openpyxl = None

class UploadMappingJasaWizard(models.TransientModel):
    _name = "tw.upload.mapping.jasa.wizard"
    _description = "Upload Mapping Jasa Wizard"

    mapping_id = fields.Many2one('tw.dgi.mapping.master.jasa', string='Mapping Jasa')
    file = fields.Binary(string='File',required=True)
    filename = fields.Char(string="Nama File")

    def action_import(self):
        if not self.file:
            raise UserError("Harap Unggah File Excel Terlebih Dahulu.")
        try:
            filedata = base64.b64decode(self.file)
            wb = openpyxl.load_workbook(BytesIO(filedata), read_only=True, data_only=True)
            sheet = wb.active
        except Exception as e:
            raise UserError("Gagal Membaca File: %s" % str(e))
        
        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            raise UserError("No data found in the uploaded file.")
        headers = [str(h).strip() if h is not None else '' for h in rows[0]]
        required_cols = ['Product Jasa','Product MD']
        for col in required_cols:
            if col not in headers:
                raise UserError("Kolom %s tidak ditemukan di file." % col)

        idx_jasa = headers.index('Product Jasa')+1
        idx_md = headers.index('Product MD')+1

        total_success = 0
        total_failed = 0
        results = []

        for rownum, row in enumerate(rows[1:], start=2):
            if not any(row):
                continue

            product_jasa = str(row[idx_jasa-1]).strip() if row[idx_jasa-1] else ''
            product_md = str(row[idx_md-1]).strip() if row[idx_md-1] else ''

            if not product_jasa or not product_md:
                results.append({
                    'product_jasa': product_jasa,
                    'product_md': product_md,
                    'status': f"Failed: empty row (line {rownum})",
                })
                total_failed += 1
                continue
            product = self.env['product.product'].suspend_security().search([('name', '=', product_jasa),('categ_id.name', '=', 'Service')], limit=1)
            if not product:
                results.append({
                    'product_jasa': product_jasa,
                    'product_md': product_md,
                    'status': f"Failed: Product Jasa {product_jasa} not found (line {rownum})",
                })
                total_failed += 1
                continue

            existing = self.env['tw.dgi.mapping.master.jasa.line'].suspend_security().search([
                ('mapping_id','=',self.mapping_id.id),
                ('product_id','=',product.id),
                ('product_md','=',product_md)
            ], limit=1)
            if existing:
                results.append({
                    'product_jasa': product_jasa,
                    'product_md': product_md,
                    'status': f"Failed: Product Jasa {product_jasa} pada branch {self.mapping_id.company_id.name} already mapped (line {rownum})",
                })
                total_failed += 1
                continue
            self.env['tw.dgi.mapping.master.jasa.line'].create({
                'mapping_id':self.mapping_id.id,
                'product_id':product.id,
                'product_md':product_md,
            })
            total_success +=1

        return {
            'name':'Result Mapping Jasa Line Upload',
            'type':'ir.actions.act_window',
            'res_model' : 'tw.upload.mapping.jasa.result.wizard',
            'view_mode': 'form',
            'target':'new',
            'context':{
                'default_total_success':total_success,
                'default_total_failed':total_failed,
                'default_not_found_list':"\n".join([
                    f"Produk jasa :{result['product_jasa']} | Produk MD : {result['product_md']} : {result['status']}"
                    for result in results
                ]) or "Semua data berhasil diimport.",
            }
        }
