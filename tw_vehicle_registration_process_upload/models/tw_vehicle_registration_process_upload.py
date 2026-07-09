# -*- coding: utf-8 -*-

from io import BytesIO
from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)

try:
    import openpyxl
except Exception as e:
    openpyxl = None

class TwVehicleRegistrationUploadWizard(models.TransientModel):
    _name = "tw.vehicle.document.upload.wizard"
    _description = "Upload Proses STNK (Wizard)"

    file = fields.Binary(string='File (.xlsx)')
    file_name = fields.Char(string='File Name')
    upload_type = fields.Selection([
        ('registration', 'Proses STNK'),
    ], string="Upload Type", required=True, default='registration')
    result_wizard_id = fields.Many2one('tw.vehicle.registration.upload.result.wizard', string='Result Wizard')


    def action_download_format_file(self):
        self.ensure_one()
        if not self.upload_type:
            raise UserError("Pilih tipe upload terlebih dahulu.")

        # Cari file format di model tw.format.upload
        format_file = self.env['tw.format.upload'].sudo().search([
            ('name', '=', self._get_format_name()),
            ('active', '=', True),
        ], limit=1)

        if not format_file:
            raise UserError("Format file '%s' tidak ditemukan atau tidak aktif." % self._get_format_name())

        # Kembalikan action untuk download file
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/tw.format.upload/%s/file_format_show/%s/?download=true' % (format_file.id, format_file.filename_format),
            'target': 'new',
        }
    def action_upload_transaction(self):
        if self.upload_type == 'registration':
            return self.action_process_upload_registration()

    def action_process_upload_registration(self):
        if not openpyxl:
            raise UserError("openpyxl is not installed. Please Contact IT")
        
        if not self.file:
            raise UserError("Please upload an .xlsx file.")
            
        try :
            filedata = base64.b64decode(self.file)
            wb= openpyxl.load_workbook(BytesIO(filedata),read_only=True,data_only=True)
            sheet = wb.active
        except Exception as e:
            raise UserError("Failed to read file: %s" % str(e))
        
        results = []
        success_count= 0
        failed_count = 0

        rows = list(sheet.iter_rows(values_only=True))
        if not rows:
            raise UserError("No data found in the uploaded file.")

        header = [str(h).strip() if h is not None else '' for h in rows[0]]

        def find_col(possible_name):
            for idx, h in enumerate(header):
                if h:
                    for name in possible_name:
                        if h.lower() == name.lower():
                            return idx
            return None
        
        branch_idx = find_col(['branch', 'cabang','Branch','Kode Branch','kode branch','Kode Cabang'])
        biro_idx = find_col(['Biro Jasa', 'Birojasa','birojasa','biro jasa','BiroJasa'])

        if branch_idx is None or biro_idx is None:
            branch_idx = 0
            biro_idx = 1

        for rownum, row in enumerate(rows[1:], start=2):
            try:
                with self.env.cr.savepoint():
                    raw_branch = row[branch_idx] if branch_idx < len(row) else None
                    raw_biro = row[biro_idx] if biro_idx < len(row) else None
                    
                    branch_code = (str(raw_branch).strip() if raw_branch is not None else '').strip()
                    biro_code = (str(raw_biro).strip() if raw_biro is not None else '').strip()
                    
                    if not branch_code or not biro_code:
                        results.append([0,0,{
                            'branch': branch_code,
                            'biro': biro_code,
                            'status': f"Failed: empty row (line {rownum})",
                        }])
                        failed_count += 1
                        continue
                    
                    company = self.env['res.company'].suspend_security().search([('code', '=', branch_code)], limit=1)
                    if not company:
                        results.append([0,0,{
                            'branch': branch_code,
                            'biro': biro_code,
                            'status': f"Failed : Branch {branch_code} not found",
                        }])
                        failed_count += 1
                        continue
                    
                    partner = self.env['res.partner'].suspend_security().search([('code', '=', biro_code), ('category_id.name', '=', 'Birojasa')], limit=1)
                    if not partner:
                        results.append([0,0,{
                            'branch': branch_code,
                            'biro': biro_code,
                            'status': f"Failed : Biro Jasa {biro_code} not found",
                        }])
                        failed_count += 1
                        continue
                        
                    registration_lines = self._prepare_registration_lines(company.id,partner.id)
                    if not registration_lines:
                        results.append([0,0,{
                            'branch': branch_code,
                            'biro': biro_code,
                            'status': f"Failed : Tidak ada proses STNK di {company.name} - {partner.name}",
                        }])
                        failed_count += 1
                        continue
                    for line in registration_lines:
                        existing = self.env['tw.vehicle.registration.process.line'].suspend_security().search([
                            ('lot_id', '=', line[2].get('lot_id')),
                            ('registration_process_id.state', '!=', 'cancel'),
                            ('state', '!=', 'cancel')
                        ], limit=1)
                    if existing:
                        results.append([0,0,{
                            'branch': branch_code,
                            'biro': biro_code,
                            'status': f"Failed : Draft record already exists ({existing.name})",
                        }])
                        failed_count += 1
                        continue
                    lot_obj = self.env['stock.lot'].suspend_security().search([('id', '=', line[2].get('lot_id'))], limit=1)
                    if not lot_obj.vehicle_document_receive_id:
                        results.append([0,0,{
                            'branch': branch_code,
                            'biro': biro_code,
                            'status': f"Failed : Engine number {lot_obj.name} has not been received (Penerimaan Faktur)",
                        }])
                        failed_count += 1
                        continue
                    
                    registration_process = self.env['tw.vehicle.registration.process'].create({
                        'company_id': company.id,
                        'biro_jasa_id': partner.id,
                        'registration_process_line_ids': registration_lines,
                    })
                    
                    results.append([0,0,{
                        'branch': branch_code,
                        'biro': biro_code,
                        'status': f"Success Created: {registration_process.name} ({len(registration_lines)} lines)",
                    }])
                    success_count += 1

            except Exception as e:
                results.append([0,0,{
                    'branch': branch_code if 'branch_code' in locals() else '',
                    'biro': biro_code if 'biro_code' in locals() else '',
                    'status': f"Failed: {str(e)}",
                }])
                failed_count += 1
                continue
        
        result_wizard_obj = self.env['tw.vehicle.registration.upload.result.wizard'].with_context(nocleanup=True).create({
            'upload_filename': self.file_name or 'uploaded.xlsx',
            'result_line_ids': results,
            'summary_success': success_count,
            'summary_failed': failed_count,
            'summary_text': (
                f"Total Processed: {len(results)}"
            )
        })
        
        return {
            'name': 'Upload Result',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.vehicle.registration.upload.result.wizard',
            'view_mode': 'form',
            'res_id': result_wizard_obj.id,
            'target': 'new',
        }

    def _get_format_name(self):
        return 'stnk proses'

    def _prepare_registration_lines(self,company_id, biro_jasa_id):
        if not company_id or not biro_jasa_id:
            return []
        try:
            query = """
                SELECT sl.id
                FROM stock_lot sl
                WHERE sl.company_id = %s
                AND sl.vehicle_document_receive_id IS NOT NULL
                AND sl.registration_process_id IS NULL
                AND sl.biro_jasa_id = %s
                AND NOT EXISTS(
                    SELECT 1
                    FROM tw_vehicle_registration_process_line rpl
                    JOIN tw_vehicle_registration_process rp ON rpl.registration_process_id = rp.id
                    WHERE rpl.lot_id = sl.id
                    AND rp.state NOT IN ('done', 'cancel')
                    AND rpl.state != 'cancel'
                )
            """
            self._cr.execute(query, (company_id, biro_jasa_id))
        except Exception as e:
            raise UserError("Error fetching registration lines: " + str(e))
        lot_ids = [row[0] for row in self._cr.fetchall()]
        return [(0,0,{'lot_id':lot_id}) for lot_id in lot_ids]