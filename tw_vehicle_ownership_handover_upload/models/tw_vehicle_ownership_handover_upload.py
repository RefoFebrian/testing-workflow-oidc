# -*- coding: utf-8 -*-
import base64
from io import BytesIO
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

try:
    import openpyxl
except ImportError:
    openpyxl = None


class TwVehicleOwnershipHandoverUploadWizard(models.TransientModel):
    _inherit = "tw.vehicle.document.upload.wizard"

    upload_type = fields.Selection(selection_add=[
        ('handover_ownership', 'Penyerahan BPKB'),
    ],
        ondelete={
            'handover_ownership': 'set default',
        },)

    def _get_format_name(self):
        format_name = super()._get_format_name()
        if self.upload_type == 'handover_ownership':
            format_name = 'ownership handover'
        return format_name

    def action_upload_transaction(self):
        action_upload = super().action_upload_transaction()
        if self.upload_type == 'handover_ownership':
           return self.action_process_upload_ownership_handover()
        return action_upload

    def action_process_upload_ownership_handover(self):
        if not self.file:
            raise ValidationError(_("Please upload an Excel file (.xlsx)."))

        if not openpyxl:
            raise UserError(_("Library openpyxl belum terinstall. Hubungi IT."))

        try:
            file_data = base64.b64decode(self.file)
            wb = openpyxl.load_workbook(BytesIO(file_data), data_only=True)
            ws = wb.active
        except Exception as e:
            raise UserError(_("Gagal membaca file Excel: %s") % str(e))
        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            raise UserError("File Excel Tidak Memiliki Data")
        # Ambil header dari baris pertama
        headers = [str(cell).strip() if cell else "" for cell in rows[0]]
        required_cols = ['Branch', 'Partner Type', 'Penerima', 'Nomor Mesin', 'Tanggal Ambil BPKB', 'Tanggal Penyerahan BPKB']
        for col in required_cols:
            if col not in headers:
                raise ValidationError(_("Missing required column: %s") % col)
        
        idx = {h:headers.index(h) for h in headers}

        grouped = {}
        results = []
        success_count = 0
        failed_count = 0

        # Iterasi data mulai baris ke-2
        for rownum, row in enumerate(rows[1:], start=2):
            if not any(row):  
                continue

            def get_value(col_name):
                idx_value = idx.get(col_name)
                return str(row[idx_value]).strip() if idx_value is not None and row[idx_value] is not None else ""

            branch_code = get_value('Branch')
            partner_type = get_value('Partner Type').lower()
            penerima = get_value('Penerima')
            note = get_value('Note')
            partner_name = get_value('A/N BPKB')
            engine_no = get_value('Nomor Mesin')

            tgl_ambil_bpkb = None
            if idx.get('Tanggal Ambil BPKB') is not None:
                tgl_ambil_bpkb = row[idx['Tanggal Ambil BPKB']]
                if isinstance(tgl_ambil_bpkb, datetime):
                    tgl_ambil_bpkb = tgl_ambil_bpkb.date()
                elif isinstance(tgl_ambil_bpkb, (int, float)):
                    tgl_ambil_bpkb = (datetime(1899, 12, 30) + timedelta(days=tgl_ambil_bpkb)).date()
                elif isinstance(tgl_ambil_bpkb, str):
                    try:
                        tgl_ambil_bpkb = datetime.strptime(tgl_ambil_bpkb, "%m/%d/%Y").date()
                    except Exception:
                        raise UserError(_("Format tanggal salah di baris %s (Tanggal Ambil BPKB). Gunakan format MM/DD/YYYY.") % rownum)

            tgl_penyerahan_bpkb = None
            if idx.get('Tanggal Penyerahan BPKB') is not None:
                tgl_penyerahan_bpkb = row[idx['Tanggal Penyerahan BPKB']]
                if isinstance(tgl_penyerahan_bpkb, datetime):
                    tgl_penyerahan_bpkb = tgl_penyerahan_bpkb.date()
                elif isinstance(tgl_penyerahan_bpkb, (int, float)):
                    tgl_penyerahan_bpkb = (datetime(1899, 12, 30) + timedelta(days=tgl_penyerahan_bpkb)).date()
                elif isinstance(tgl_penyerahan_bpkb, str):
                    try:
                        tgl_penyerahan_bpkb = datetime.strptime(tgl_penyerahan_bpkb, "%m/%d/%Y").date()
                    except Exception:
                        raise UserError(_("Format tanggal salah di baris %s (Tanggal Penyerahan BPKB). Gunakan format MM/DD/YYYY.") % rownum)

            # --- Validasi dasar ---
            if not branch_code:
                results.append([0,0,{'branch_code':branch_code, 'status':f"Failed row {rownum}: Branch is mandatory"}])
                failed_count += 1
                continue
            if partner_type not in ['customer', 'finco']:
                results.append([0,0,{'branch_code':branch_code, 'status':f"Failed row {rownum}: Invalid Partner Type"}])
                failed_count += 1
                continue
            if not partner_name and not penerima:
                results.append([0,0,{'branch_code':branch_code, 'status':f"Failed row {rownum}: Penerima is mandatory"}])
                failed_count += 1
                continue
            if not engine_no:
                results.append([0,0,{'branch_code':branch_code, 'status':f"Failed row {rownum}: Engine number is mandatory"}])
                failed_count += 1
                continue
            if not tgl_ambil_bpkb:
                results.append([0,0,{'branch_code':branch_code, 'status':f"Failed row {rownum}: Tanggal Ambil BPKB is mandatory"}])
                failed_count += 1
                continue
            if not tgl_penyerahan_bpkb:
                results.append([0,0,{'branch_code':branch_code, 'status':f"Failed row {rownum}: Tanggal Penyerahan BPKB is mandatory"}])
                failed_count += 1
                continue

            grouped.setdefault((branch_code, partner_type, penerima, note, partner_name, tgl_penyerahan_bpkb), []).append({
                'engine_no': engine_no,
                'tgl_ambil_bpkb': tgl_ambil_bpkb,
                'rownum': rownum,
            })
        for (branch_code, partner_type, penerima, note, partner_name, tgl_penyerahan_bpkb), lines in grouped.items():
            rownum_first = lines[0]['rownum']
            engine_no_first = lines[0]['engine_no']

            # --- Cari data terkait ---
            branch = self.env['res.company'].sudo().search([('code', '=', branch_code)], limit=1)
            if not branch:
                results.append([0,0,{'branch_code':branch_code,'engine_no': engine_no_first, 'status':f"Failed row {rownum_first}: Branch not found"}])
                failed_count += 1
                continue

            partner = False
            if partner_name:
                domain = [
                    '|', ('name', '=', partner_name),
                    ('code', '=', partner_name)
                ]
                if partner_type == 'customer':
                    domain.append(('category_id.name', 'in', ['Customer']))
                else:
                    domain.append(('category_id.name', 'in', ['Birojasa']))
                partner = self.env['res.partner'].sudo().search(domain, limit=1)
                if not partner:
                    results.append([0,0,{'branch_code':branch_code,'engine_no': engine_no_first, 'status':f"Failed row {rownum_first}: A/N BPKB (Partner) not found"}])
                    failed_count += 1
                    continue
            
            # --- Gunakan nama partner sebagai penerima jika kolom kosong ---
            receiver = penerima or (partner.name if partner else 'Tanpa Penerima')
            if receiver =='Tanpa Penerima':
                results.append([0,0,{'branch_code':branch_code,'engine_no': engine_no_first, 'status':f"Failed row {rownum_first} tidak lengkap: Penerima is mandatory"}])
                failed_count += 1
                continue

            line_vals = []
            for l in lines:
                lot_id = self._prepare_available_lot_ids_ownwership_handover(partner, partner_type, branch.id, l['engine_no'])
                if not lot_id or not isinstance(lot_id[0], int):
                    results.append([0,0,{'branch_code':branch_code,'engine_no': l['engine_no'], 'status':f"Failed: Engine number {l['engine_no']} not found or not eligible"}])
                    failed_count += 1
                    continue
                lot = self.env['stock.lot'].sudo().search([('id', '=', lot_id)], limit=1)
                if not lot:
                    results.append([0,0,{'branch_code':branch_code,'engine_no': l['engine_no'], 'status':f"Failed: Engine number {l['engine_no']} not found"}])
                    failed_count += 1
                    continue
                
                existing_line = self.env['tw.vehicle.ownership.handover.line'].sudo().search([
                ('lot_id', '=', lot.id),
                ('state', '!=', 'cancel'),
                ('ownership_handover_id.state', 'not in', ['cancel', 'done']),
                ('ownership_handover_id.company_id','=',branch.id),
                ('ownership_handover_id.partner_type','=',partner_type),
                ('ownership_handover_id.receiver','=',receiver),
                ])
                if existing_line:
                    results.append([0,0,{'branch_code':branch_code,'engine_no': l['engine_no'], 'status':f"Failed: Engine number {l['engine_no']} sudah ada di {existing_line.ownership_handover_id.name}"}])
                    failed_count += 1
                    continue
                if not lot.vehicle_ownership_receipt_id:
                    results.append([0,0,{'branch_code':branch_code,'engine_no': l['engine_no'], 'status':f"Failed: Engine number {l['engine_no']} has not been BPKB received"}])
                    failed_count += 1
                    continue
                if not lot.birojasa_billing_date:
                    results.append([0,0,{'branch_code':branch_code,'engine_no': l['engine_no'], 'status':f"Failed: Engine number {l['engine_no']} has not been Birojasa billing"}])
                    failed_count += 1
                    continue

                # --- Cek apakah sudah pernah diserahkan ---
                if lot.ownership_handover_id:
                    results.append([0,0,{'branch_code':branch_code,'engine_no': l['engine_no'], 'status':f"Failed: Engine number {l['engine_no']} already handed over in {lot.ownership_handover_id.name}"}])
                    failed_count += 1
                    continue
                line_vals.append((0,0,{
                    'lot_id': lot.id,
                    'ownership_handover_date': l['tgl_ambil_bpkb'],
                    'state': 'draft',
                }))
            if not line_vals:
                continue
            
            # --- Buat atau cari header handover ---
            try:
                with self.env.cr.savepoint():
                    handover = self.env['tw.vehicle.ownership.handover'].sudo().create({
                        'company_id': branch.id,
                        'partner_type': partner_type,
                        'partner_id': partner.id if partner else False,
                        'receiver': receiver,
                        'note': note,
                        'ownership_handover_date': tgl_penyerahan_bpkb or fields.Date.today(),
                        'ownership_handover_line_ids':line_vals,
                        'state': 'draft',
            })
            except Exception as e:
                results.append([0,0,{'branch_code':branch_code,'engine_no': lines[0]['engine_no'] if lines else '', 'status':f"Failed to create handover: {str(e)}"}])
                failed_count += 1
                continue
            results.append([0,0,{'branch_code':branch_code,'engine_no': 'Multiple' if len(lines) > 1 else lines[0]['engine_no'], 'status':f"Success: Uploaded to {handover.name}"}])
            success_count += 1
            
        # --- Simpan hasil upload ---
        result_wizard_obj = self.env['tw.vehicle.ownership.handover.upload.result.wizard'].create({
            'upload_filename': self.file_name or 'uploaded.xlsx',
            'result_line_ids':results,
            'summary_success': success_count,
            'summary_failed': failed_count,
            'summary_text': (
                f"Total Processed : {len(results)}"
            )
        })

        return {
            'name': _('Upload Result'),
            'type': 'ir.actions.act_window',
            'res_model': 'tw.vehicle.ownership.handover.upload.result.wizard',
            'view_mode': 'form',
            'res_id': result_wizard_obj.id,
            'target': 'new',
        }

    def _prepare_available_lot_ids_ownwership_handover(self, partner, partner_type, company_id, engine_no):
        if not partner_type or not company_id or not engine_no:
            return []
        where = " AND sl.name = '%s'" % engine_no
        if partner:
            if partner_type == 'customer':
                where += " AND sl.customer_stnk_id = %d" % partner.id
            else:
                where += " AND sl.biro_jasa_id = %d" % partner.id
                
        # Base query with ownership and billing filters
        query = f"""
            SELECT sl.id 
            FROM stock_lot sl
            WHERE sl.company_id = {company_id}
            {where}
            AND sl.vehicle_ownership_receipt_id IS NOT NULL
            AND sl.vehicle_ownership_receipt_id != 0
            AND sl.birojasa_billing_date IS NOT NULL
            AND sl.ownership_handover_id IS NULL
            AND NOT EXISTS (
                SELECT 1 
                FROM tw_vehicle_ownership_handover_line opl
                JOIN tw_vehicle_ownership_handover op 
                    ON opl.ownership_handover_id = op.id
                WHERE opl.lot_id = sl.id 
                AND op.state NOT IN ('done', 'cancel')
                AND opl.state != 'cancel'
            )
            LIMIT 1
        """
        self._cr.execute(query)
        lot_id =  self._cr.fetchone()
        return [lot_id[0] if lot_id else []]