# -*- coding: utf-8 -*-
import base64
from io import BytesIO
from datetime import datetime, date, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

try:
    import openpyxl
except ImportError:
    openpyxl = None


class TwVehicleDocumentHandoverUpload(models.TransientModel):
    _inherit = "tw.vehicle.document.upload.wizard"

    upload_type = fields.Selection(selection_add=[
        ('reg_handover', 'Penyerahan STNK'),
    ], 
        ondelete={
            'reg_handover': 'set default',
        },)

    def _get_format_name(self):
        format_name = super()._get_format_name()
        if self.upload_type == 'reg_handover':
            format_name = 'registration handover'
        return format_name
    
    def action_upload_transaction(self):
        action_upload = super().action_upload_transaction()
        if self.upload_type == 'reg_handover':
            return self.action_process_upload_reg_handover()
        return action_upload

    def action_process_upload_reg_handover(self):
        """Proses file Excel untuk membuat penyerahan STNK/Plat"""
        if not openpyxl:
            raise UserError("Library openpyxl belum terinstall. Hubungi IT.")
        if not self.file:
            raise UserError("Silakan upload file Excel terlebih dahulu.")

        try:
            file_data = base64.b64decode(self.file)
            wb = openpyxl.load_workbook(BytesIO(file_data), data_only=True)
            ws = wb.active
        except Exception as e:
            raise UserError(_("Gagal membaca file Excel: %s") % str(e))

        rows = list(ws.iter_rows(values_only=True))
        if len(rows) < 2:
            raise UserError("File Excel tidak memiliki data.")

        # Validasi header kolom
        header = [str(h).strip().lower() if h else '' for h in rows[0]]
        required_headers = ['branch', 'customer', 'penerima', 'note', 'nomor mesin', 'tanggal ambil notice','tanggal ambil stnk','tanggal ambil plat']
        for h in required_headers:
            if h not in header:
                raise UserError(_("Kolom '%s' tidak ditemukan di file Excel.") % h)

        idx = {h: header.index(h) for h in required_headers}
        grouped = {}
        results = []
        success_count= 0
        failed_count = 0
        for rownum, row in enumerate(rows[1:], start=2):
            branch_val = str(row[idx['branch']]).strip() if row[idx['branch']] else ''
            cust_val = str(row[idx['customer']]).strip() if row[idx['customer']] else ''
            penerima_val = str(row[idx['penerima']]).strip() if row[idx['penerima']] else ''
            note_val = str(row[idx['note']]).strip() if row[idx['note']] else ''
            engine_val = str(row[idx['nomor mesin']]).strip() if row[idx['nomor mesin']] else ''
            tgl_ambil_notice_val = row[idx['tanggal ambil notice']]
            tgl_ambil_stnk_val = row[idx['tanggal ambil stnk']]
            tgl_ambil_plat_val = row[idx['tanggal ambil plat']]


            # Validasi mandatory
            if (not branch_val  or not engine_val) or not (tgl_ambil_plat_val or tgl_ambil_stnk_val or tgl_ambil_notice_val):
                results.append([0,0,{'branch':branch_val,'receiver':penerima_val,'status':f"Failed: row {rownum} tidak lengkap. Kolom Branch, Nomor Mesin, dan salah satu Tanggal ambil wajib diisi."}])
                failed_count += 1
                continue
            invalid_date = False
            validated_dates = {}
            for name, val in [
                ('notice', tgl_ambil_notice_val),
                ('stnk', tgl_ambil_stnk_val),
                ('plat', tgl_ambil_plat_val)
            ]:
                date_val = self._safe_date(val)
                if val and not date_val:
                    results.append([0,0,{'branch':branch_val,'receiver':penerima_val,'status':f"Failed: row {rownum} format tanggal ambil {name} salah. Gunakan format MM/DD/YYYY atau pastikan sel Excel bertipe Date."}])
                    failed_count += 1
                    invalid_date = True
                    break
                validated_dates[name] = date_val
                
            if invalid_date:
                continue

            grouped.setdefault((branch_val, cust_val, penerima_val, note_val), []).append({
                'engine_no': engine_val,
                'tgl_ambil_plat': validated_dates['plat'],
                'tgl_ambil_stnk': validated_dates['stnk'],
                'tgl_ambil_notice': validated_dates['notice'],
                'rownum': rownum,
            })
            
        for (branch_code, cust_code, penerima, note), lines in grouped.items():
            # --- Cari branch ---
            company = self.env['res.company'].suspend_security().search([('code', '=', branch_code)], limit=1)
            if not company:
                results.append([0,0,{'branch':branch_code,'receiver':penerima,'status':f"Failed: Branch '{branch_code}' tidak ditemukan."}])
                failed_count += 1
                continue

            # --- Cari customer ---
            partner = False
            if cust_code:
                partner = self.env['res.partner'].suspend_security().search([
                    '|', ('code', '=', cust_code),
                        ('name', '=', cust_code)
                ], limit=1)

                if not partner:
                    results.append([0,0,{'branch':branch_code,'receiver':penerima,'status':f"Failed: Customer '{cust_code}' tidak ditemukan."}])
                    failed_count += 1
                    continue

            # --- Gunakan nama customer sebagai penerima jika kolom kosong ---
            receiver = penerima or (partner.name if partner else 'Tanpa Penerima')
            if receiver == 'Tanpa Penerima':
                results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Failed row {rownum} tidak lengkap: Penerima wajib diisi."}])
                failed_count += 1
                continue

            # --- Buat line ---
            line_vals = []
            for l in lines:
                tgl_ambil_plat = l.get('tgl_ambil_plat')
                tgl_ambil_stnk = l.get('tgl_ambil_stnk')
                tgl_ambil_notice = l.get('tgl_ambil_notice')
                rownum = l['rownum']
                lot_id = self._prepare_available_lot_ids(partner, company.id)
                if not lot_id or not isinstance(lot_id[0], int):
                    results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Failed row {rownum}: Engine number not found"}])
                    failed_count += 1
                    continue
                lot = self.env['stock.lot'].sudo().search([('id', '=', lot_id)], limit=1)
                
                if not lot:
                    cust_label = cust_code or 'Tanpa Customer'
                    results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Failed: Engine '{l['engine_no']}' tidak ditemukan di cabang {branch_code} untuk {cust_label}."}])
                    failed_count += 1
                    continue
                if not lot.vehicle_registration_receipt_id:
                    results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Failed: Engine number '{l['engine_no']}' has not been BPKB received"}])
                    failed_count += 1
                    continue
                if not lot.notice_receipt_id:
                    results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Failed: Engine number '{l['engine_no']}' has not been Notice received"}])
                    failed_count += 1
                    continue
                if not lot.plate_receipt_id:
                    results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Failed: Engine number '{l['engine_no']}' has not been Plate received"}])
                    failed_count += 1
                    continue
                if not lot.birojasa_billing_date:
                    results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Failed: Engine number '{l['engine_no']}' has not been Birojasa billing"}])
                    failed_count += 1
                    continue
                conflict_fields = []
                # if existing:
                #     for exist in existing:
                existing_line = self.env['tw.vehicle.registration.handover.line'].suspend_security().search([
                    ('lot_id','=', lot.id),
                    ('vehicle_registration_handover_id.company_id','=', company.id),
                    ('vehicle_registration_handover_id.receiver','=', receiver),    
                    ('vehicle_registration_handover_id.state', 'not in', ['cancel','done']),
                    ('state','!=','cancel'),
                ])
                if existing_line:
                    if tgl_ambil_stnk and lot.registration_handover_id and lot.registration_handover_id.id != existing_line.vehicle_registration_handover_id.id:
                        conflict_fields.append('STNK')
                    if tgl_ambil_notice and lot.notice_handover_id and lot.notice_handover_id.id != existing_line.vehicle_registration_handover_id.id:
                        conflict_fields.append('NOTICE')
                    
                    if tgl_ambil_plat and lot.plate_handover_id and lot.plate_handover_id.id != existing_line.vehicle_registration_handover_id.id:
                        conflict_fields.append('PLAT')
                        
                    if conflict_fields:
                        results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Failed: Row {rownum}: Engine number '{l['engine_no']}' has already processed for {', '.join(conflict_fields)} in {existing_line.vehicle_registration_handover_id.name}."}])
                        failed_count += 1
                        continue

                # --- Pengecekan "Available Docs" seperti di unchecked_count ---
                available_docs = []
                if not lot.notice_handover_date and not tgl_ambil_notice:
                    available_docs.append('Notice')
                if not lot.plate_handover_date and not tgl_ambil_plat:
                    available_docs.append('Plate')
                if not lot.registration_handover_date and not tgl_ambil_stnk:
                    available_docs.append('STNK')

                unchecked_count = sum([
                    not bool(tgl_ambil_notice),
                    not bool(tgl_ambil_plat),
                    not bool(tgl_ambil_stnk),
                ])

                if available_docs and unchecked_count == len(available_docs):
                    results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Failed: Row {rownum}: Engine number '{l['engine_no']}' — "
                                    f"tidak ada dokumen yang dipilih untuk diserahkan.\n\n"
                                    f"Dokumen yang masih tersedia:\n- " + "\n- ".join(available_docs)}])
                    failed_count += 1
                    continue

                # --- Validasi kombinasi kondisi ---
                # Kasus 1: plate & registration sudah ada, tapi notice belum → wajib isi tgl_ambil_notice
                if lot.plate_handover_date and lot.registration_handover_date and not lot.notice_handover_date:
                    if not tgl_ambil_notice:
                        results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Engine number '{l['engine_no']}': 'tgl_ambil_notice' wajib diisi karena plate & STNK sudah ada."}])
                        failed_count += 1
                        continue
                
                # Kasus 2: plate & notice sudah ada, tapi registration belum → wajib isi tgl_ambil_stnk
                if lot.plate_handover_date and lot.notice_handover_date and not lot.registration_handover_date:
                    if not tgl_ambil_stnk:
                        results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Engine number '{l['engine_no']}': 'tgl_ambil_stnk' wajib diisi karena plate & STNK sudah ada."}])
                        failed_count += 1
                        continue
                
                # Kasus 3: plate & notice sudah ada, tapi registration belum → wajib isi tgl_ambil_stnk
                if not lot.plate_handover_date and lot.notice_handover_date and lot.registration_handover_date:
                    if not tgl_ambil_plat:
                        results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Engine number '{l['engine_no']}': 'tgl_ambil_plat' wajib diisi karena plate & STNK sudah ada."}])
                        failed_count += 1
                        continue

                # Kasus 4: plate sudah ada, tapi STNK & notice kosong → salah satu wajib diisi
                elif lot.plate_handover_date and not lot.registration_handover_date and not lot.notice_handover_date:
                    if not (tgl_ambil_stnk or tgl_ambil_notice):
                        results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Engine number '{l['engine_no']}': minimal salah satu 'tgl_ambil_stnk' atau 'tgl_ambil_notice' harus diisi karena plate sudah ada."}])
                        failed_count += 1
                        continue

                # Kasus 5: STNK sudah ada, tapi plate & notice kosong → salah satu wajib diisi
                elif lot.registration_handover_date and not lot.plate_handover_date and not lot.notice_handover_date:
                    if not (tgl_ambil_plat or tgl_ambil_notice):
                        results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Engine number '{l['engine_no']}': minimal salah satu 'tgl_ambil_plat' atau 'tgl_ambil_notice' harus diisi karena STNK sudah ada."}])
                        failed_count += 1
                        continue

                # Kasus 6: NOTICE sudah ada, tapi plate & STNK kosong → salah satu wajib diisi
                elif lot.notice_handover_date and not lot.plate_handover_date and not lot.registration_handover_date:
                    if not (tgl_ambil_plat or tgl_ambil_stnk):
                        results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Engine number '{l['engine_no']}': minimal salah satu 'tgl_ambil_plat' atau 'tgl_ambil_stnk' harus diisi karena NOTICE sudah ada."}])
                        failed_count += 1
                        continue

                line_val = {
                    'lot_id': lot.id,
                    'plate_handover': bool(lot.plate_handover_date),
                    'vehicle_registration_handover': bool(lot.registration_handover_date),
                    'notice_handover': bool(lot.notice_handover_date),
                    'state': 'draft',
                    'plate_handover_date': lot.plate_handover_date or (tgl_ambil_plat if tgl_ambil_plat else False),
                    'stnk_handover_date': lot.registration_handover_date or (tgl_ambil_stnk if tgl_ambil_stnk else False),
                    'notice_handover_date': lot.notice_handover_date or (tgl_ambil_notice if tgl_ambil_notice else False),
                }

                line_vals.append((0, 0, line_val))

            if not line_vals:
                results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Failed : No valid lines to process, skipped."}])
                failed_count += 1
                continue  
            try:
                with self.env.cr.savepoint():
                # --- Buat record utama ---
                    handover_vals = {
                        'company_id': company.id,
                        'partner_id': partner.id if partner else False,
                        'receiver': receiver,
                        'note': note,
                        'date': date.today(),
                        'state': 'draft',
                        'registration_handover_line_ids': line_vals,
                    }

                    record = self.env['tw.vehicle.registration.handover'].create(handover_vals)
            except Exception as e:
                results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Failed: Row {rownum}: {str(e)}"}])
                failed_count += 1
                continue
            results.append([0,0,{'branch':branch_code,'receiver':receiver,'status':f"Success Dibuat: {record.name} ({len(line_vals)} engine) untuk {branch_code}/{cust_code or 'Tanpa Customer'}."}])
            success_count +=1
        
        result_wizard_obj = self.env['tw.vehicle.registration.handover.upload.result.wizard'].create({
            'upload_filename':self.file_name or 'uploaded.xlsx',
            'result_line_ids': results,
            'summary_success': success_count,
            'summary_failed': failed_count,
            'summary_text': (
                f"Total Processed : {len(results)}"
            )
        })
        return {
            'name': "Hasil Upload Penyerahan STNK/Plat",
            'type': 'ir.actions.act_window',
            'res_model': 'tw.vehicle.registration.handover.upload.result.wizard',
            'view_mode': 'form',
            'target': 'new',
            'res_id': result_wizard_obj.id
        }

    def _safe_date(self, val):
        if not val:
            return False
        if isinstance(val, (datetime, date)):
            return val.strftime("%Y-%m-%d")
        if isinstance(val, (int, float)):
            try:
                # Excel base date is 1899-12-30
                return (date(1899, 12, 30) + timedelta(days=int(val))).strftime("%Y-%m-%d")
            except:
                return False
        if isinstance(val, str):
            val = val.strip()
            if not val:
                return False
            for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%m-%d-%Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(val, fmt).strftime("%Y-%m-%d")
                except:
                    continue
        return False
    
    def _prepare_available_lot_ids(self, partner,company_id):
        if not company_id:
            return []
        where = ""
        if partner:
            where = " AND sl.customer_stnk_id = %d" % partner.id
         # Base query without customer filter
            query = f"""
                SELECT sl.id 
                FROM stock_lot sl
                WHERE sl.company_id = {company_id}
                {where}
                AND sl.vehicle_registration_receipt_id NOTNULL
                AND sl.notice_receipt_id NOTNULL
                AND sl.plate_receipt_id NOTNULL
                AND sl.birojasa_billing_date NOTNULL
                AND (
                    sl.registration_handover_id IS NULL
                    OR sl.notice_handover_id IS NULL
                    OR sl.plate_handover_id IS NULL
                )
                AND NOT EXISTS (
                    SELECT 1 
                    FROM tw_vehicle_registration_handover_line rpl
                    JOIN tw_vehicle_registration_handover rp 
                        ON rpl.vehicle_registration_handover_id = rp.id
                    WHERE rpl.lot_id = sl.id 
                    AND rp.state NOT IN ('done', 'cancel')
                    AND rpl.state != 'cancel'
                )
                LIMIT 1
            """
            self._cr.execute(query)
            lot_id = self._cr.fetchone()
            return [lot_id[0] if lot_id else []]