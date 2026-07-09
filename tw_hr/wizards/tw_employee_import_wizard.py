# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import logging
import io

try:
    import openpyxl
except ImportError:
    openpyxl = None

_logger = logging.getLogger(__name__)

class EmployeeImportWizard(models.TransientModel):
    _name = 'tw.employee.import.wizard'
    _description = 'Employee Import Wizard'

    file = fields.Binary(string='File', required=True)
    file_name = fields.Char(string='File Name')
    skip_existing = fields.Boolean(string="Skip Existing Employee", default=False, help="If checked, the wizard will not update employees that already exist in the database.")
    process_batch = fields.Boolean(string="Process Batch (Faster)", default=True, help="If checked, new employees are sent to the database in bulk (vals list), making creation significantly faster.")
    batch_limit = fields.Integer(string="Batch Limit", default=1000, help="Number of records to process per batch.")
    start_row = fields.Integer(string="Start Row", default=2, help="Excel row number to start importing from (default is 2).")
    import_log = fields.Text(string='Import Log', readonly=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], default='draft')

    def action_import(self):
        self.ensure_one()
        if self.start_row < 2:
            raise UserError(_("Start Row must be 2 or greater."))

        if not openpyxl:
            raise UserError(_("Python openpyxl library is required to read Excel files."))

        if not self.file_name or not self.file_name.endswith('.xlsx'):
            raise UserError(_("Please upload an Excel (.xlsx) file."))

        try:
            file_data = base64.b64decode(self.file)
            workbook = openpyxl.load_workbook(filename=io.BytesIO(file_data), data_only=True)
            sheet = workbook.active
        except Exception as e:
            raise UserError(_("Error reading Excel file: %s") % str(e))

        # Read headers
        headers = []
        for cell in sheet[1]:
            headers.append(cell.value)

        # Mapping dictionary
        header_map = {}
        for idx, header in enumerate(headers):
            if not header:
                continue
            h_lower = str(header).lower().strip()
            if h_lower in ('external id', 'id', 'xml_id'):
                header_map['external_id'] = idx
            elif h_lower in ('employee name', 'name', 'nama karyawan'):
                header_map['name'] = idx
            elif h_lower in ('nip', 'registry number', 'registry_number', 'no. pendaftaran'):
                header_map['registry_number'] = idx
            elif h_lower in ('branch', 'company', 'company_id', 'cabang'):
                header_map['company_id'] = idx
            elif h_lower in ('area', 'area_id'):
                header_map['area_id'] = idx
            elif h_lower in ('work email', 'work_email', 'email kerja'):
                header_map['work_email'] = idx
            elif h_lower in ('work phone', 'work_phone', 'telp kerja'):
                header_map['work_phone'] = idx
            elif h_lower in ('work mobile', 'mobile phone', 'mobile_phone', 'no handphone', 'handphone'):
                header_map['mobile_phone'] = idx
            elif h_lower in ('job position', 'job_position', 'job_id', 'jabatan'):
                header_map['job_id'] = idx
            elif h_lower in ('working start date', 'working_start_date', 'tgl_masuk', 'tanggal masuk'):
                header_map['working_start_date'] = idx
            elif h_lower in ('working end date', 'working_end_date', 'tgl_keluar', 'tanggal keluar'):
                header_map['working_end_date'] = idx
            elif h_lower in ('no. npwp', 'no_npwp', 'npwp', 'tax_number', 'tax number'):
                header_map['tax_number'] = idx
            elif h_lower in ('no. kontrak', 'no_kontrak', 'contract_number', 'contract number'):
                header_map['contract_number'] = idx
            elif h_lower in ('work address', 'work_address', 'address_id', 'alamat kerja'):
                header_map['address_id'] = idx
            elif h_lower in ('private street', 'private_street', 'alamat pribadi'):
                header_map['private_street'] = idx
            elif h_lower in ('private street2', 'private_street2'):
                header_map['private_street2'] = idx
            elif h_lower in ('private state', 'private_state', 'provinsi pribadi'):
                header_map['private_state_id'] = idx
            elif h_lower in ('private city', 'private_city', 'kota pribadi'):
                header_map['private_city'] = idx
            elif h_lower in ('private zip', 'private_zip', 'kode pos pribadi'):
                header_map['private_zip'] = idx
            elif h_lower in ('private country', 'private_country', 'negara pribadi'):
                header_map['private_country_id'] = idx
            elif h_lower in ('private email', 'private_email', 'email pribadi'):
                header_map['private_email'] = idx
            elif h_lower in ('marital status', 'marital', 'status pernikahan'):
                header_map['marital'] = idx
            elif h_lower in ('identification no', 'identification_no', 'identification_id', 'no ktp', 'ktp'):
                header_map['identification_id'] = idx
            elif h_lower in ('passport no', 'passport_no', 'passport_id', 'no paspor'):
                header_map['passport_id'] = idx
            elif h_lower in ('gender', 'jenis kelamin'):
                header_map['gender'] = idx
            elif h_lower in ('create user?', 'create_user?', 'is_user', 'buat user?'):
                header_map['is_user'] = idx
            elif h_lower in ('date of birth', 'date_of_birth', 'birthday', 'tanggal lahir'):
                header_map['birthday'] = idx
            elif h_lower in ('nomor rekening', 'acc_number', 'acc number', 'no rekening'):
                header_map['acc_number'] = idx
            elif h_lower in ('nama pemilik rekening', 'acc_holder_name', 'acc holder name', 'pemilik rekening'):
                header_map['acc_holder_name'] = idx
            elif h_lower in ('bank', 'bank_id'):
                header_map['bank_id'] = idx
            elif h_lower in ('coach', 'coach_id', 'pembimbing'):
                header_map['coach_id'] = idx
            elif h_lower in ('manager', 'parent_id', 'atasan'):
                header_map['parent_id'] = idx

        if 'name' not in header_map:
            raise UserError(_("Could not find an 'Employee Name' or 'Name' column in the header."))

        # Helper to parse dates safely
        from datetime import date, datetime
        def parse_date(val):
            if not val:
                return False
            if isinstance(val, (date, datetime)):
                return val.strftime('%Y-%m-%d')
            val_str = str(val).strip()
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y'):
                try:
                    dt = datetime.strptime(val_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except:
                    continue
            return val_str

        # Helper to parse boolean safely
        def parse_boolean(val):
            if not val:
                return False
            val_str = str(val).strip().lower()
            return val_str in ('true', '1', 'yes', 'y')

        # Load all rows to count total progress
        all_rows = []
        for row in sheet.iter_rows(min_row=self.start_row, values_only=True):
            if any(row):
                all_rows.append(row)

        total_rows = len(all_rows)
        _logger.info("=== STARTING EMPLOYEE IMPORT: TOTAL ROWS = %s ===", total_rows)

        # Pre-fetch candidate codes and values for bulk O(1) lookups
        all_ext_ids = []
        company_codes = set()
        area_codes = set()
        job_names = set()
        address_names = set()
        state_names = set()
        country_names = set()
        bank_names = set()
        coach_names = set()
        manager_names = set()
        ident_ids = set()
        reg_nums = set()
        mobile_phones = set()

        for row in all_rows:
            if 'external_id' in header_map and row[header_map['external_id']] is not None:
                val = str(row[header_map['external_id']]).strip()
                if val:
                    all_ext_ids.append(val)
            if 'company_id' in header_map and row[header_map['company_id']] is not None:
                val = str(row[header_map['company_id']]).strip()
                if val:
                    company_codes.add(val)
            if 'area_id' in header_map and row[header_map['area_id']] is not None:
                val = str(row[header_map['area_id']]).strip()
                if val:
                    area_codes.add(val)
            if 'job_id' in header_map and row[header_map['job_id']] is not None:
                val = str(row[header_map['job_id']]).strip()
                if val:
                    job_names.add(val)
            if 'address_id' in header_map and row[header_map['address_id']] is not None:
                val = str(row[header_map['address_id']]).strip()
                if val:
                    address_names.add(val)
            if 'private_state_id' in header_map and row[header_map['private_state_id']] is not None:
                val = str(row[header_map['private_state_id']]).strip()
                if val:
                    state_names.add(val)
            if 'private_country_id' in header_map and row[header_map['private_country_id']] is not None:
                val = str(row[header_map['private_country_id']]).strip()
                if val:
                    country_names.add(val)
            if 'bank_id' in header_map and row[header_map['bank_id']] is not None:
                val = str(row[header_map['bank_id']]).strip()
                if val:
                    bank_names.add(val)
            if 'coach_id' in header_map and row[header_map['coach_id']] is not None:
                val = str(row[header_map['coach_id']]).strip()
                if val:
                    coach_names.add(val)
            if 'parent_id' in header_map and row[header_map['parent_id']] is not None:
                val = str(row[header_map['parent_id']]).strip()
                if val:
                    manager_names.add(val)
            if 'identification_id' in header_map and row[header_map['identification_id']] is not None:
                val = str(row[header_map['identification_id']]).strip()
                if val:
                    ident_ids.add(val.replace('.0', '').replace(' ', '').replace('-', ''))
            if 'registry_number' in header_map and row[header_map['registry_number']] is not None:
                val = str(row[header_map['registry_number']]).strip()
                if val:
                    reg_nums.add(val)
            if 'mobile_phone' in header_map and row[header_map['mobile_phone']] is not None:
                val_str = str(row[header_map['mobile_phone']]).strip()
                if val_str:
                    sanitized_phone = val_str.replace(' ', '').replace('-', '').replace('\'', '')
                    if sanitized_phone.endswith('.0'):
                        sanitized_phone = sanitized_phone[:-2]
                    if sanitized_phone.startswith('0'):
                        sanitized_phone = '62' + sanitized_phone[1:]
                    mobile_phones.add(sanitized_phone)

        # 1. Pre-fetch ir.model.data (External IDs)
        existing_xml_id_records = {}
        if all_ext_ids:
            ext_pairs = [ext.split('.', 1) if '.' in ext else ('__import__', ext) for ext in all_ext_ids]
            modules = {p[0] for p in ext_pairs}
            names = {p[1] for p in ext_pairs}
            names_list = list(names)
            for i in range(0, len(names_list), 1000):
                chunk_names = names_list[i:i+1000]
                records = self.env['ir.model.data'].sudo().search([
                    ('model', '=', 'hr.employee'),
                    ('module', 'in', list(modules)),
                    ('name', 'in', chunk_names)
                ])
                for r in records:
                    if (r.module, r.name) in ext_pairs:
                        existing_xml_id_records[(r.module, r.name)] = r

        # 2. Pre-fetch res.company
        companies_map = {}
        if company_codes:
            companies = self.env['res.company'].search(['|', ('code', 'in', list(company_codes)), ('name', 'in', list(company_codes))])
            for c in companies:
                companies_map[c.code] = c.id
                companies_map[c.name] = c.id

        # 3. Pre-fetch res.area
        areas_map = {}
        if area_codes:
            areas = self.env['res.area'].search(['|', '|', ('description', 'in', list(area_codes)), ('code', 'in', list(area_codes)), ('name', 'in', list(area_codes))])
            for a in areas:
                if a.description:
                    areas_map[a.description] = a.id
                if a.code:
                    areas_map[a.code] = a.id
                if a.name:
                    areas_map[a.name] = a.id

        # 4. Pre-fetch hr.job
        jobs_map = {}
        if job_names:
            jobs = self.env['hr.job'].search([('name', 'in', list(job_names))])
            for j in jobs:
                jobs_map[j.name.lower()] = j.id

        # 5. Pre-fetch res.partner (work address)
        partners_map = {}
        if address_names:
            partners = self.env['res.partner'].search([('name', 'in', list(address_names)), ('is_company', '=', True)])
            for p in partners:
                partners_map[p.name.lower()] = p.id

        # 6. Pre-fetch res.country.state
        states_map = {}
        if state_names:
            states = self.env['res.country.state'].search(['|', ('name', 'in', list(state_names)), ('code', 'in', list(state_names))])
            for s in states:
                states_map[s.name.lower()] = s.id
                states_map[s.code.lower()] = s.id

        # 7. Pre-fetch res.country
        countries_map = {}
        if country_names:
            countries = self.env['res.country'].search(['|', ('name', 'in', list(country_names)), ('code', 'in', list(country_names))])
            for c in countries:
                countries_map[c.name.lower()] = c.id
                countries_map[c.code.lower()] = c.id

        # 8. Pre-fetch res.bank
        banks_map = {}
        if bank_names:
            banks = self.env['res.bank'].search(['|', ('name', 'in', list(bank_names)), ('bic', 'in', list(bank_names))])
            for b in banks:
                banks_map[b.name.lower()] = b.id
                if b.bic:
                    banks_map[b.bic.lower()] = b.id

        # 9. Pre-fetch hr.employee for coaches and managers
        emp_names = coach_names.union(manager_names)
        emps_map = {}
        if emp_names:
            emp_names_list = list(emp_names)
            for i in range(0, len(emp_names_list), 1000):
                chunk = emp_names_list[i:i+1000]
                emps = self.env['hr.employee'].search([('name', 'in', chunk)])
                for emp in emps:
                    emps_map[emp.name.lower()] = emp.id

        # 10. Pre-fetch hr.employee for duplicates/existence checking by ident, reg and phone
        existing_emp_by_ident = {}
        if ident_ids:
            ident_ids_list = list(ident_ids)
            for i in range(0, len(ident_ids_list), 1000):
                chunk = ident_ids_list[i:i+1000]
                emps = self.env['hr.employee'].with_context(active_test=False).search([('identification_id', 'in', chunk)])
                for emp in emps:
                    existing_emp_by_ident[emp.identification_id] = emp

        existing_emp_by_reg = {}
        if reg_nums:
            reg_nums_list = list(reg_nums)
            for i in range(0, len(reg_nums_list), 1000):
                chunk = reg_nums_list[i:i+1000]
                emps = self.env['hr.employee'].with_context(active_test=False).search([('registry_number', 'in', chunk)])
                for emp in emps:
                    existing_emp_by_reg[emp.registry_number] = emp

        existing_emp_by_phone = {}
        if mobile_phones:
            mobile_phones_list = list(mobile_phones)
            for i in range(0, len(mobile_phones_list), 1000):
                chunk = mobile_phones_list[i:i+1000]
                emps = self.env['hr.employee'].with_context(active_test=False).search([('mobile_phone', 'in', chunk)])
                for emp in emps:
                    existing_emp_by_phone[emp.mobile_phone] = emp

        success_count = 0
        log_lines = []
        log_lines.append(f"--- Starting Custom Employee Import (Total: {total_rows} rows) ---")

        batch_create_vals = []
        batch_create_meta = []

        def flush_create_batch():
            nonlocal success_count, log_lines, batch_create_vals, batch_create_meta
            if not batch_create_vals:
                return
            
            # Create all records in the batch at once.
            # If this fails, it will intentionally throw a massive error and stop the wizard as requested.
            new_emps = self.env['hr.employee'].with_context(import_file=True).create([v.copy() for v in batch_create_vals])
            
            # Create external IDs if any
            xml_id_vals_to_create = []
            for i, emp in enumerate(new_emps):
                meta = batch_create_meta[i]
                ext_id = meta['external_id']
                if ext_id:
                    module, name = ext_id.split('.', 1) if '.' in ext_id else ('__import__', ext_id)
                    xml_id_rec = existing_xml_id_records.get((module, name))
                    if xml_id_rec:
                        if xml_id_rec.res_id != emp.id:
                            xml_id_rec.write({'res_id': emp.id})
                    else:
                        xml_id_vals_to_create.append({
                            'name': name,
                            'module': module,
                            'model': 'hr.employee',
                            'res_id': emp.id,
                            'noupdate': True
                        })
                
                # Update lookup dicts so subsequent rows can find them
                emps_map[meta['name'].lower()] = emp.id
                if meta['vals'].get('identification_id'):
                    existing_emp_by_ident[meta['vals']['identification_id']] = emp
                if meta['vals'].get('registry_number'):
                    existing_emp_by_reg[meta['vals']['registry_number']] = emp
                if meta['vals'].get('mobile_phone'):
                    existing_emp_by_phone[meta['vals']['mobile_phone']] = emp
                
                warning_text = f" (Warnings: {', '.join(meta['warnings'])})" if meta['warnings'] else ""
                log_lines.append(f"Row {meta['row_idx']}: SUCCESS - BATCH CREATED '{meta['name']}'{warning_text}")
                success_count += 1

            if xml_id_vals_to_create:
                created_xml_ids = self.env['ir.model.data'].sudo().create(xml_id_vals_to_create)
                for x in created_xml_ids:
                    existing_xml_id_records[(x.module, x.name)] = x
            
            _logger.info(">>> SUCCESSFULLY BATCH CREATED %s records", len(new_emps))
            
            # Clear buffers
            batch_create_vals.clear()
            batch_create_meta.clear()

        for idx, row in enumerate(all_rows, start=1):
            row_idx = idx + self.start_row - 1
            vals = {}
            row_warnings = []
            
            # 1. Basic Fields
            for key, col_idx in header_map.items():
                if key in ('external_id', 'company_id', 'area_id', 'job_id', 'address_id', 
                           'private_state_id', 'private_country_id', 'bank_id', 'coach_id', 'parent_id'):
                    continue # process separately below
                
                raw_val = row[col_idx]
                if raw_val is None or str(raw_val).strip() == '':
                    continue
                    
                val_str = str(raw_val).strip()
                
                if key in ('working_start_date', 'working_end_date', 'birthday'):
                    vals[key] = parse_date(raw_val)
                elif key == 'is_user':
                    vals[key] = parse_boolean(raw_val)
                elif key == 'marital':
                    lower_val = val_str.lower()
                    if 'single' in lower_val or 'lajang' in lower_val:
                        vals[key] = 'single'
                    elif 'marry' in lower_val or 'nikah' in lower_val or 'kawin' in lower_val:
                        vals[key] = 'married'
                    elif 'divorce' in lower_val or 'cerai' in lower_val:
                        vals[key] = 'divorced'
                    elif 'widow' in lower_val or 'janda' in lower_val or 'duda' in lower_val:
                        vals[key] = 'widower'
                    else:
                        vals[key] = 'single'
                elif key == 'gender':
                    lower_val = val_str.lower()
                    if 'female' in lower_val or 'perempuan' in lower_val or 'wanita' in lower_val:
                        vals[key] = 'female'
                    elif 'male' in lower_val or 'laki' in lower_val or 'pria' in lower_val:
                        vals[key] = 'male'
                    else:
                        vals[key] = 'other'
                elif key in ('mobile_phone', 'work_phone'):
                    sanitized_phone = val_str.replace(' ', '').replace('-', '').replace('\'', '')
                    if sanitized_phone.endswith('.0'):
                        sanitized_phone = sanitized_phone[:-2]
                    if sanitized_phone.startswith('0'):
                        sanitized_phone = '62' + sanitized_phone[1:]
                    vals[key] = sanitized_phone
                elif key == 'identification_id':
                    vals[key] = val_str.replace('.0', '').replace(' ', '').replace('-', '')
                elif key == 'acc_number':
                    vals[key] = val_str.replace('.0', '').replace(' ', '').replace('-', '')
                else:
                    vals[key] = val_str

            if not vals.get('name'):
                _logger.warning("Row %s: Skipped (Name is empty)", row_idx)
                log_lines.append(f"Row {row_idx}: SKIPPED (Employee Name is empty)")
                continue

            # Monitor progress in the console log
            print(f"IMPORT PROGRESS >>> {idx}/{total_rows} ({(idx / total_rows) * 100:.1f}%) | Employee: {vals['name']} | NIP: {vals.get('registry_number', 'N/A')}")
            _logger.info("[%s/%s] (%.1f%%) Processing Employee: %s (NIP: %s)", 
                         idx, total_rows, (idx / total_rows) * 100, vals['name'], vals.get('registry_number', 'N/A'))

            external_id = None
            if 'external_id' in header_map:
                ext_val = row[header_map['external_id']]
                if ext_val and str(ext_val).strip() != '':
                    external_id = str(ext_val).strip()

            # 2. Relational Lookups
            # Branch (Company)
            if 'company_id' in header_map:
                val = row[header_map['company_id']]
                if val is not None and str(val).strip() != '':
                    val_str = str(val).strip()
                    company_id = companies_map.get(val_str)
                    if company_id:
                        vals['company_id'] = company_id
                    else:
                        row_warnings.append(f"Branch '{val_str}' not found")
            
            # Area (res.area)
            if 'area_id' in header_map:
                val = row[header_map['area_id']]
                if val is not None and str(val).strip() != '':
                    val_str = str(val).strip()
                    area_id = areas_map.get(val_str)
                    if area_id:
                        vals['area_id'] = area_id
                    else:
                        row_warnings.append(f"Area '{val_str}' not found")
            
            # Job Position (hr.job)
            if 'job_id' in header_map:
                val = row[header_map['job_id']]
                if val is not None and str(val).strip() != '':
                    val_str = str(val).strip()
                    job_id = jobs_map.get(val_str.lower())
                    if job_id:
                        vals['job_id'] = job_id
                    else:
                        row_warnings.append(f"Job Position '{val_str}' not found")
            
            # Work Address (res.partner)
            if 'address_id' in header_map:
                val = row[header_map['address_id']]
                if val is not None and str(val).strip() != '':
                    val_str = str(val).strip()
                    partner_id = partners_map.get(val_str.lower())
                    if partner_id:
                        vals['address_id'] = partner_id
                    else:
                        row_warnings.append(f"Work Address '{val_str}' not found")
            
            # Private State (res.country.state)
            if 'private_state_id' in header_map:
                val = row[header_map['private_state_id']]
                if val is not None and str(val).strip() != '':
                    val_str = str(val).strip()
                    state_id = states_map.get(val_str.lower())
                    if state_id:
                        vals['private_state_id'] = state_id
                    else:
                        row_warnings.append(f"Private State '{val_str}' not found")
            
            # Private Country (res.country)
            if 'private_country_id' in header_map:
                val = row[header_map['private_country_id']]
                if val is not None and str(val).strip() != '':
                    val_str = str(val).strip()
                    country_id = countries_map.get(val_str.lower())
                    if country_id:
                        vals['private_country_id'] = country_id
                    else:
                        row_warnings.append(f"Private Country '{val_str}' not found")
            
            # Bank (res.bank)
            if 'bank_id' in header_map:
                val = row[header_map['bank_id']]
                if val is not None and str(val).strip() != '':
                    val_str = str(val).strip()
                    bank_id = banks_map.get(val_str.lower())
                    if bank_id:
                        vals['bank_id'] = bank_id
                    else:
                        row_warnings.append(f"Bank '{val_str}' not found")
            
            # Coach (hr.employee)
            if 'coach_id' in header_map:
                val = row[header_map['coach_id']]
                if val is not None and str(val).strip() != '':
                    val_str = str(val).strip()
                    coach_id = emps_map.get(val_str.lower())
                    if coach_id:
                        vals['coach_id'] = coach_id
                    else:
                        row_warnings.append(f"Coach employee '{val_str}' not found")
            
            # Manager (hr.employee)
            if 'parent_id' in header_map:
                val = row[header_map['parent_id']]
                if val is not None and str(val).strip() != '':
                    val_str = str(val).strip()
                    manager_id = emps_map.get(val_str.lower())
                    if manager_id:
                        vals['parent_id'] = manager_id
                    else:
                        row_warnings.append(f"Manager employee '{val_str}' not found")

            # Find existing record
            employee = False
            if external_id:
                module, name = external_id.split('.', 1) if '.' in external_id else ('__import__', external_id)
                xml_id_rec = existing_xml_id_records.get((module, name))
                if xml_id_rec:
                    employee = self.env['hr.employee'].browse(xml_id_rec.res_id)
                    if not employee.exists():
                        employee = False
            
            if not employee and vals.get('identification_id'):
                employee = existing_emp_by_ident.get(vals['identification_id'])
            
            if not employee and vals.get('registry_number'):
                employee = existing_emp_by_reg.get(vals['registry_number'])

            # Check duplicate mobile phone
            if vals.get('mobile_phone'):
                existing_phone_emp = existing_emp_by_phone.get(vals['mobile_phone'])
                if existing_phone_emp and (not employee or existing_phone_emp.id != employee.id):
                    row_warnings.append(f"Mobile phone '{vals['mobile_phone']}' is already used by '{existing_phone_emp.name}'")
                    vals['mobile_phone'] = False

            # Save the name before Odoo ORM modifies the 'vals' dictionary via _inherits (which pops 'name')
            emp_name = vals.get('name')

            if employee:
                # UPDATE - Always row-by-row
                try:
                    with self.env.cr.savepoint():
                        if self.skip_existing:
                            warning_text = f" (Warnings: {', '.join(row_warnings)})" if row_warnings else ""
                            log_lines.append(f"Row {row_idx}: SKIPPED (Skip Existing) - '{emp_name}'{warning_text}")
                        else:
                            employee.with_context(import_file=True).write(vals)
                            warning_text = f" (Warnings: {', '.join(row_warnings)})" if row_warnings else ""
                            log_lines.append(f"Row {row_idx}: SUCCESS - UPDATED '{emp_name}'{warning_text}")
                            success_count += 1

                        if external_id:
                            module, name = external_id.split('.', 1) if '.' in external_id else ('__import__', external_id)
                            xml_id_rec = existing_xml_id_records.get((module, name))
                            if xml_id_rec:
                                if xml_id_rec.res_id != employee.id:
                                    xml_id_rec.write({'res_id': employee.id})
                            else:
                                created_xml = self.env['ir.model.data'].sudo().create({
                                    'name': name,
                                    'module': module,
                                    'model': 'hr.employee',
                                    'res_id': employee.id,
                                    'noupdate': True
                                })
                                existing_xml_id_records[(module, name)] = created_xml

                        # Update lookup dicts so subsequent rows can find them
                        emps_map[emp_name.lower()] = employee.id
                        if vals.get('identification_id'):
                            existing_emp_by_ident[vals['identification_id']] = employee
                        if vals.get('registry_number'):
                            existing_emp_by_reg[vals['registry_number']] = employee
                        if vals.get('mobile_phone'):
                            existing_emp_by_phone[vals['mobile_phone']] = employee
                except Exception as e:
                    error_msg = str(e)
                    row_err_msg = _("FAILED IMPORT AT ROW %s (Employee: '%s')\n\nError Details:\n%s") % (row_idx, emp_name or 'Unknown', error_msg)
                    _logger.error("IMPORT ERROR AT ROW %s: %s", row_idx, error_msg, exc_info=True)
                    raise UserError(row_err_msg)
            else:
                # CREATE
                if self.process_batch:
                    # Buffer for batch creation
                    batch_create_vals.append(vals)
                    batch_create_meta.append({
                        'name': emp_name,
                        'row_idx': row_idx,
                        'warnings': row_warnings,
                        'external_id': external_id,
                        'vals': vals
                    })
                else:
                    # Row-by-row creation
                    try:
                        with self.env.cr.savepoint():
                            new_emp = self.env['hr.employee'].with_context(import_file=True).create(vals)
                            if external_id:
                                module, name = external_id.split('.', 1) if '.' in external_id else ('__import__', external_id)
                                xml_id_rec = existing_xml_id_records.get((module, name))
                                if xml_id_rec:
                                    if xml_id_rec.res_id != new_emp.id:
                                        xml_id_rec.write({'res_id': new_emp.id})
                                else:
                                    created_xml = self.env['ir.model.data'].sudo().create({
                                        'name': name,
                                        'module': module,
                                        'model': 'hr.employee',
                                        'res_id': new_emp.id,
                                        'noupdate': True
                                    })
                                    existing_xml_id_records[(module, name)] = created_xml
                            
                            # Update lookup dicts so subsequent rows can find them
                            emps_map[emp_name.lower()] = new_emp.id
                            if vals.get('identification_id'):
                                existing_emp_by_ident[vals['identification_id']] = new_emp
                            if vals.get('registry_number'):
                                existing_emp_by_reg[vals['registry_number']] = new_emp
                            if vals.get('mobile_phone'):
                                existing_emp_by_phone[vals['mobile_phone']] = new_emp

                            warning_text = f" (Warnings: {', '.join(row_warnings)})" if row_warnings else ""
                            log_lines.append(f"Row {row_idx}: SUCCESS - CREATED '{emp_name}'{warning_text}")
                            success_count += 1
                    except Exception as e:
                        error_msg = str(e)
                        row_err_msg = _("FAILED IMPORT AT ROW %s (Employee: '%s')\n\nError Details:\n%s") % (row_idx, emp_name or 'Unknown', error_msg)
                        _logger.error("IMPORT ERROR AT ROW %s: %s", row_idx, error_msg, exc_info=True)
                        raise UserError(row_err_msg)

            batch_limit = self.batch_limit if self.batch_limit > 0 else 1000
            
            # Flush batch if limit reached
            if self.process_batch and len(batch_create_vals) >= batch_limit:
                flush_create_batch()

            # --- Commit transaction and clear cache every N records to prevent memory leak ---
            if idx > 0 and idx % batch_limit == 0:
                self.env.cr.commit()
                self.env.cache.invalidate()
                _logger.info(">>> COMMITTED DB TRANSACTION of %s records", batch_limit)

        # Flush any remaining creates at the end of the loop
        if self.process_batch and batch_create_vals:
            flush_create_batch()


        _logger.info("=== EMPLOYEE IMPORT COMPLETED: %s SUCCESS ===", success_count)
        log_lines.append("--- Custom Import Finished ---")
        log_lines.append(f"Total Success: {success_count}")

        self.import_log = "\n".join(log_lines)
        self.state = 'done'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.employee.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

