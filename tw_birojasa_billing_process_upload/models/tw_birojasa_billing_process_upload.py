from odoo import api, fields, models
from odoo.exceptions import UserError,ValidationError
import base64
from io import BytesIO
import logging
from datetime import date, datetime

_logger = logging.getLogger(__name__)
try:
    import openpyxl
except Exception as e:
    openpyxl = None

class TwBirojasaBillingUploadWizard(models.TransientModel):
    _inherit = "tw.vehicle.document.upload.wizard"

    upload_type = fields.Selection(selection_add=[
        ('billing', 'Tagihan birojasa'),
    ],  ondelete={
            'billing': 'set default',
        },)

    def _get_format_name(self):
        format_name = super()._get_format_name()
        if self.upload_type == 'billing':
            format_name = 'birojasa billing'
        return format_name

    def _parse_taxes(self,tax_cell):
        if not tax_cell:
            return self.env['account.tax'].browse([])
        raw= str(tax_cell).strip()
        parts = [p.strip() for p in raw.replace(',',';').split(';') if p.strip()]
        taxes = self.env['account.tax']
        found = taxes.browse()
        for part in parts:
            tax = self.env['account.tax'].suspend_security().search([('name','=',part)],limit=1)
            if not tax:
                tax = self.env['account.tax'].suspend_security().search([('id','=',part)],limit=1)
            if tax:
                found |= tax
        return found

    def _safe_date(self , val):
        if not val:
            return False
        if isinstance(val, (datetime, date)):
            return val.strftime("%Y-%m-%d")
        if isinstance(val, str):
            for fmt in ("%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d"):
                try:
                    return datetime.strptime(val.strip(), fmt).strftime("%Y-%m-%d")
                except Exception:
                    continue
        return False

    def _parse_bool(self, val):
        if not val:
            return False
        raw = str(val).strip().lower()
        if raw in ['true', '1', 'yes', 'y']:
            return True
        if raw in ['false', '0', 'no', 'n']:
            return False
        return None

    def action_upload_transaction(self):
        action_upload = super().action_upload_transaction()
        if self.upload_type == 'billing':
            return self.action_process_upload_billing()
        return action_upload

    def action_process_upload_billing(self):
        self.ensure_one()
        if not openpyxl:
            raise UserError("Openpyxl library is not installed. Please Contact IT")

        if not self.file:
            raise UserError("Silakan unggah file .xlsx terlebih dahulu.")
        
        try :
            filedata = base64.b64decode(self.file)
            wb = openpyxl.load_workbook(BytesIO(filedata),read_only=True, data_only=True)
            ws = wb.active
        except Exception as e:
            raise UserError("Failed to read file: %s" % str(e))
        
        rows = list(ws.iter_rows(values_only=True))
        if not rows or len(rows) < 2:
            raise UserError("File is empty or invalid format.")
        
        header = [str(h).strip() if h is not None else '' for h in rows[0]]

        # helper to find column index (case-insensitive)
        def find_col(possible_names):
            for idx, h in enumerate(header):
                if h:
                    for name in possible_names:
                        if h.lower() == name.lower():
                            return idx
            return None
        
        # detect relevant columns
        branch_idx = find_col(['branch', 'kode branch', 'kode_branch', 'cabang'])
        division_idx = find_col(['division', 'divisi'])
        birojasa_idx = find_col(['biro jasa', 'birojasa', 'biro'])
        tgl_idx = find_col(['tgl', 'date', 'tanggal'])
        type_idx = find_col(['type', 'tipe'])
        description_idx = find_col(['description', 'keterangan', 'desc'])
        document_date_idx = find_col(['document date', 'document_date', 'documentdate', 'document'])
        document_number_idx = find_col(['document number', 'document_number', 'doc number', 'doc_number'])
        document_copy_idx = find_col(['document copy', 'document_copy'])
        taxes_idx = find_col(['taxes', 'tax', 'pajak'])
        engine_idx = find_col(['engine line', 'engine', 'engine_no', 'engine no', 'engine number', 'lot', 'engine_line'])
        notice_no_idx = find_col(['no notice', 'notice number', 'notice_no', 'notice'])
        notice_date_idx = find_col(['tgl jtp notice', 'notice date', 'notice_date', 'jtp'])
        total_tagihan_idx = find_col(['total tagihan', 'Total Tagihan', 'amount total', 'Amount Total'])

         # fallback to sensible defaults
        if branch_idx is None:
            branch_idx = 0
        if division_idx is None:
            division_idx = None
        if birojasa_idx is None:
            birojasa_idx = 1
        if tgl_idx is None:
            tgl_idx = None
        if type_idx is None:
            type_idx = None
        if description_idx is None:
            description_idx = None
        if document_date_idx is None:
            document_date_idx = None
        if document_number_idx is None:
            document_number_idx = None
        if document_copy_idx is None:
            document_copy_idx = None
        if taxes_idx is None:
            taxes_idx = None
        if engine_idx is None:
            engine_idx = None
        if notice_no_idx is None:
            notice_no_idx = None
        if notice_date_idx is None:
            notice_date_idx = None
        if total_tagihan_idx is None:
            total_tagihan_idx = None

        groups = {}
        results = []
        success_count = 0
        failed_count = 0
        line_no = 1
        for rownum, row in enumerate(rows[1:], start=2):
            try:
                branch_val = str(row[branch_idx]).strip() if branch_idx is not None and branch_idx < len(row) and row[branch_idx] is not None else ''
                division_val = (str(row[division_idx]).strip() if division_idx is not None and division_idx < len(row) and row[division_idx] is not None else 'Unit')
                birojasa_val = str(row[birojasa_idx]).strip() if birojasa_idx is not None and birojasa_idx < len(row) and row[birojasa_idx] is not None else ''
                tgl_val = row[tgl_idx] if tgl_idx is not None and tgl_idx < len(row) and row[tgl_idx] else None
                type_val = str(row[type_idx]).strip() if type_idx is not None and type_idx < len(row) and row[type_idx] is not None else ''
                desc_val = str(row[description_idx]).strip() if description_idx is not None and description_idx < len(row) and row[description_idx] is not None else ''
                doc_date_val = row[document_date_idx] if document_date_idx is not None and document_date_idx < len(row) and row[document_date_idx] else None
                doc_num_val = str(row[document_number_idx]).strip() if document_number_idx is not None and document_number_idx < len(row) and row[document_number_idx] is not None else ''
                doc_copy_val = str(row[document_copy_idx]).strip() if document_copy_idx is not None and document_copy_idx < len(row) and row[document_copy_idx] is not None else 'false'
                taxes_cell = row[taxes_idx] if taxes_idx is not None and taxes_idx < len(row) and row[taxes_idx] is not None else None
            
                engine_val = str(row[engine_idx]).strip() if engine_idx is not None and engine_idx < len(row) and row[engine_idx] is not None else ''
                notice_no_val = str(row[notice_no_idx]).strip() if notice_no_idx is not None and notice_no_idx < len(row) and row[notice_no_idx] is not None else ''
                notice_date_val = row[notice_date_idx] if notice_date_idx is not None and notice_date_idx < len(row) and row[notice_date_idx] else None
                notice_date_val = row[notice_date_idx] if notice_date_idx is not None and notice_date_idx < len(row) and row[notice_date_idx] else None
                total_tagihan_val = 0.0
                if total_tagihan_idx is not None and total_tagihan_idx < len(row) and row[total_tagihan_idx] is not None:
                    try:
                        total_tagihan_val = float(row[total_tagihan_idx])
                    except Exception:
                        total_tagihan_val = 0.0

                if not branch_val:
                    results.append([0,0,{'branch':branch_val,'biro':birojasa_val,'status':f'Failed: row {rownum} Branch mandatory'}])
                    failed_count += 1
                    continue
                if not birojasa_val:
                    results.append([0,0,{'branch':branch_val,'biro':birojasa_val,'status':f'Failed: row {rownum} Birojasa mandatory'}])
                    failed_count += 1
                    continue
                if not type_val:
                    results.append([0,0,{'branch':branch_val,'biro':birojasa_val,'status':f'Failed: row {rownum} Type mandatory'}])
                    failed_count += 1
                    continue
                if not doc_date_val:
                    results.append([0,0,{'branch':branch_val,'biro':birojasa_val,'status':f'Failed: row {rownum} Document Date mandatory'}])
                    failed_count += 1
                    continue
                # Parse bool
                doc_copy_bool = self._parse_bool(doc_copy_val)
                if doc_copy_bool is None:
                    results.append([0,0,{'branch':branch_val,'biro':birojasa_val,'status':f'Failed: row {rownum} Document Copy must be true or false (received: {doc_copy_val})'}])
                    failed_count += 1
                    continue
                if not engine_val:
                    results.append([0,0,{'branch':branch_val,'biro':birojasa_val,'status':f'Failed: row {rownum} Engine Line mandatory'}])
                    failed_count += 1
                    continue
                if not notice_no_val:
                    results.append([0,0,{'branch':branch_val,'biro':birojasa_val,'status':f'Failed: row {rownum} No Notice mandatory'}])
                    failed_count += 1
                    continue
                if not notice_date_val:
                    results.append([0,0,{'branch':branch_val,'biro':birojasa_val,'status':f'Failed: row {rownum} TGL JTP Notice mandatory'}])
                    failed_count += 1
                    continue

                if hasattr(tgl_val,'date'):
                    tgl_val = tgl_val.date()
                if hasattr(doc_date_val,'date'):
                    doc_date_val = doc_date_val.date()
                if hasattr(notice_date_val,'date'):
                    notice_date_val = notice_date_val.date()
                
                if type_val not in ['reg','adv']:
                    results.append([0,0,{'branch':branch_val,'biro':birojasa_val,'status':f'Failed: row {rownum} Type must be reg or adv'}])
                    failed_count += 1
                    continue

                if not tgl_val:
                    tgl_val = date.today()
                
                taxes_key = str(taxes_cell).strip() if taxes_cell else ''
                process_key = (
                    branch_val,division_val,birojasa_val,str(tgl_val),type_val,desc_val,str(doc_date_val),doc_num_val,taxes_key, doc_copy_bool)

                groups.setdefault(process_key,[]).append({
                    'rownum': rownum,
                    'engine':engine_val,
                    'notice_no':notice_no_val,
                    'notice_date':notice_date_val,
                    'total_tagihan': total_tagihan_val,
                })

            except Exception as e:
                results.append([0,0,{'branch':branch_val,'biro':birojasa_val,'status':f'Failed: row {rownum} {str(e)}'}])
                failed_count += 1
                continue

        for key, lines in groups.items():
            (branch_val,division_val,birojasa_val,tgl_val_s, type_val, desc_val,doc_date_s,doc_num_val,taxes_key, doc_copy_bool) = key

            company = self.env['res.company'].suspend_security().search([('code', '=', branch_val)], limit=1)
            if not company:
                results.append([0,0,{'branch':branch_val,'biro': birojasa_val, 'status':f"Failed : Branch {branch_val} not found"}])
                failed_count += 1
                continue
            
            partner = self.env['res.partner'].suspend_security().search(['|',('code', '=', birojasa_val), ('name', '=', birojasa_val),('category_id.name', '=', 'Birojasa')], limit=1)
            if not partner:
                results.append([0,0,{'branch':branch_val,'biro': birojasa_val, 'status':f"Failed : Biro Jasa {birojasa_val} not found"}])
                failed_count += 1
                continue
            
            # parse dates back
            try:
                doc_date_val = doc_date_s if doc_date_s and doc_date_s != 'None' else None
                tgl_val = tgl_val_s if tgl_val_s and tgl_val_s != 'None' else date.today()
            except Exception:
                # fallback
                doc_date_val = None
                tgl_val = date.today()

            # parse taxes
            taxes = self._parse_taxes(taxes_key)

            # prepare billing_line_ids              
            billing_lines_cmds = []
            approval_correction_amount = 0.0
            for l in lines:
                engine_name = l['engine']
                notice_no = l['notice_no']
                notice_date = l['notice_date']
                total_tagihan = l['total_tagihan']
                rownum = l['rownum']

                lot = self.env['stock.lot'].suspend_security().search([('name', '=', engine_name), ('company_id', '=', company.id)], limit=1)
                if not lot:
                    results.append([0,0,{'branch':branch_val,'biro': birojasa_val, 'status':f"Failed line: Row {rownum}: Engine '{engine_name}' not found for branch {branch_val}"}])
                    failed_count += 1
                    continue
                
                existing_line = self.env['tw.birojasa.billing.process.line'].suspend_security().search([
                    ('lot_id','=', lot.id),
                    ('birojasa_billing_id.state', '!=', 'cancel'),
                    ('state','!=','cancel'),
                    ('birojasa_billing_id.company_id', '=', company.id),
                    ('birojasa_billing_id.biro_jasa_id', '=', partner.id),
                ])
                if existing_line:
                    results.append([0,0,{'branch':branch_val,'biro': birojasa_val, 'status':f"Failed line: Row {rownum}: Engine '{engine_name}' already exists in {existing_line.birojasa_billing_id.name}"}])
                    failed_count += 1
                    continue

                # mandatory per your requirement: notice no & notice date must be present
                if not notice_no:
                    results.append([0,0,{'branch':branch_val,'biro': birojasa_val, 'status':f"Failed line: Row {rownum}: No Notice mandatory"}])
                    failed_count += 1
                    continue
                if not notice_date:
                    results.append([0,0,{'branch':branch_val,'biro': birojasa_val, 'status':f"Failed line: Row {rownum}: TGL JTP Notice mandatory"}])
                    failed_count += 1
                    continue

                # prepare values for line
                approval_correction_amount += (lot.estimation_amount or 0.0) - (total_tagihan or 0.0)
                vals = {
                    'lot_id': lot.id,
                    'notice_number': lot.notice_number or notice_no,
                    'notice_date': self._safe_date(lot.notice_date or notice_date) or '',
                    # amount_total taken from lot estimation or set to 0.0 if missing
                    'correction_amount': approval_correction_amount,
                    'amount_total': total_tagihan,
                    'service_amount': lot.service_amount or 0.0,
                }
                billing_lines_cmds.append((0, 0, vals))
            
            if not billing_lines_cmds:
                results.append([0,0,{'branch':branch_val,'biro': birojasa_val, 'status':f"Failed : No valid lines to process, skipped."}])
                failed_count += 1
                continue

            # create billing process
            try:
                with self.env.cr.savepoint():
                    billing_vals = {
                        'company_id': company.id,
                        'biro_jasa_id': partner.id,
                        'division': division_val or 'Unit',
                        'date': self._safe_date(tgl_val) or '',
                        'type': type_val or 'reg',
                        'approval_correction_amount':approval_correction_amount,
                        'description': desc_val or False,
                        'document_date': self._safe_date(doc_date_val) or '',
                        'document_number': doc_num_val or False,
                        'document_copy': doc_copy_bool,
                        'tax_ids': [(6, 0, taxes.ids)] if taxes else False,
                        'billing_line_ids': billing_lines_cmds,
                    }
                    
                    billing = self.env['tw.birojasa.billing.process'].create(billing_vals)
            except Exception as e:
                results.append([0,0,{'branch':branch_val,'biro': birojasa_val, 'status':f"Failed: Row {rownum}: {str(e)}"}])
                failed_count += 1
                continue
            results.append([0,0,{'branch':branch_val,'biro': birojasa_val, 'status':f"Success: {billing.name} ({len(billing_lines_cmds)} lines)"}])
            success_count += 1

        result_wizard_obj = self.env['tw.birojasa.billing.process.upload.result.wizard'].sudo().create({
            'upload_filename':self.file_name or 'uploaded.xlsx',
            'result_line_ids': results,
            'summary_success': success_count,
            'summary_failed': failed_count,
            'summary_text': (
                f"Total Processed : {len(results)}"
            )
        })

        return {
            'name': 'Upload Result Billing Birojasa',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.birojasa.billing.process.upload.result.wizard',
            'view_mode': 'form',
            'res_id': result_wizard_obj.id,
            'target': 'new',
        }