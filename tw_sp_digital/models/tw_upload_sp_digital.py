# 1: imports of python lib
from datetime import date
import base64
import xlrd

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


class EmployeeUploadSpDigital(models.TransientModel):
    _name = "tw.upload.sp.digital"
    _description = 'Upload SP Digital'

    # 7: defaults methods
    def _get_default_date(self):
        return self.env['res.company'].get_default_date()

    # 8: fields
    file = fields.Binary('File')
    date = fields.Date('Tanggal', readonly=True, default=_get_default_date)
    state_x = fields.Selection([
        ('choose', 'choose'),
        ('get', 'get')
    ], default='choose')

    # 9: relation fields

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods

    # 12: override methods
    
    # 13: action methods
    def action_upload_sp_digital_tree(self, type='transaction'):
        domain = []
        name = 'Upload SP Digital'
        path = 'upload-sp-digital'
        upload_type = type
        if type == 'target':
            name = name + ' Master'
            path = path + '-target'

        form_view_id = self.env.ref('tw_sp_digital.tw_upload_sp_digital_wizard_view').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'path': path,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'tw.upload.sp.digital',
            'domain': domain,
            'views': [(form_view_id, 'form')],
            'context': {
                'search_default_fieldname': 1,
                'readonly_by_pass': 1,
                'default_upload_type': upload_type
            },
        }
    
    def action_download_format_file(self):
        name = 'upload SP digital'
        if self._context.get('default_upload_type') == 'target':
            name = 'upload target SP digital'
        format_upload_obj = self.env['tw.format.upload'].suspend_security().search([
            ('name','=',name),
            ('active','=',True)
        ], limit=1)
        if format_upload_obj:
            return {
                'type': 'ir.actions.act_url',
                'name': 'contract',
                'url': f'/web/content/tw.format.upload/{format_upload_obj.id}/file_format_show/{format_upload_obj.filename_upload_format}?download=true'
            }
        else:
            raise Warning(f'Maaf, format template file "{name}" belum tersedia.')
        
    def action_import(self):
        type = self._context.get('default_upload_type')
        if not self.file:
            raise Warning('Silahkan input file terlebih dahulu.')
        
        data = base64.decodebytes(self.file)
        excel = xlrd.open_workbook(file_contents=data)
        sh = excel.sheet_by_index(0)
        warning_note = ''
        vals_header, vals_line_ids = [], []
        for rx in range(1, sh.nrows):
            if type == 'target':
                warning_note, vals_header, vals_line_ids = self._process_import_data(sh, rx, warning_note, vals_header, vals_line_ids, type='target')
            else:
                warning_note, vals_header, vals_line_ids = self._process_import_data(sh, rx, warning_note, vals_header, vals_line_ids)
        
        # Raise Warning if any error or incorrect format
        if warning_note:
            raise Warning(warning_note)

        if type == 'transaction':
            self.env['tw.sp.digital'].suspend_security().create(vals_header)
            self.env['tw.sp.digital.line'].suspend_security().create(vals_line_ids)
            name = 'SP Digital'
            model = 'tw.sp.digital'
            list_view_id = self.env.ref('tw_sp_digital.tw_sp_digital_list_view').id
        else:
            name = 'Target SP Digital'
            model = 'tw.sp.digital.target'
            list_view_id = self.env.ref('tw_sp_digital.tw_sp_digital_target_list_view').id
            
        return {
            'name': (name),
            'view_type': 'form',
            'view_mode': 'list,form',
            'res_model': model,
            'type': 'ir.actions.act_window',
            'res_id': False,
            'views': [(list_view_id, 'list'), (False, 'form')],
            'view_id': False,
            'target': 'current'
        }

    # 14: private methods
    def _process_import_data(self, sh, rx, warning_note, vals_header, vals_line_ids, type='transaction'):
        values = [sh.cell(rx, ry).value for ry in range(sh.ncols)]
        branch = values[0]
        if type == 'target':
            job = values[1]
            qty = values[2]

            job_obj = self.env['hr.job'].suspend_security().search([
                ('name','=',job)
            ], limit=1)
            if not job_obj:
                warning_note += f'Baris ke {rx} Job {job} tidak ditemukan\n'
            if not qty or not str(qty).replace('.0', '').isdigit():
                warning_note += f'Baris ke {rx} Qty {qty} Tidak valid / tidak terisi\n'
            
            # If line contain branch then it will be header
            if branch:
                branch_obj = self.env['res.company'].suspend_security().search([
                    ('code','=',branch)
                ], limit=1)
                if not branch_obj:
                    warning_note += f'Baris ke {rx} Branch Code {branch} tidak ditemukan\n'
                
                if vals_header:
                    if not warning_note:
                        vals_header['line_ids'] = vals_line_ids
                        # Search existing header
                        target_header = self.env['tw.sp.digital.target'].suspend_security().search([
                            ('company_id','=',branch_obj.id)
                        ])
                        if target_header:
                            target_header.suspend_security().write(vals_header)
                        else:
                            self.env['tw.sp.digital.target'].suspend_security().create(vals_header)

                vals_header = {'company_id': branch_obj.id}
                vals_line_ids = []
                vals_line_ids.append([0, False, {
                    'job_id': job_obj.id,
                    'qty': qty
                }])

                # Handle Last Line
                if rx+1 == sh.nrows:
                    if not warning_note:
                        vals_header['line_ids'] = vals_line_ids
                        # Search existing header
                        target_header = self.env['tw.sp.digital.target'].suspend_security().search([
                            ('company_id','=',branch_obj.id)
                        ])
                        if target_header:
                            target_header.suspend_security().write(vals_header)
                        else:
                            self.env['tw.sp.digital.target'].suspend_security().create(vals_header)

            elif not branch:
                vals_line_ids.append([0, False, {
                    'job_id': job_obj.id,
                    'qty': qty
                }])

                # Handle last line
                if rx+1 == sh.nrows:
                    if not warning_note:
                        vals_header['line_ids'] = vals_line_ids
                        # Search existing header
                        target_header = self.env['tw.sp.digital.target'].suspend_security().search([
                            ('company_id','=',branch_obj.id)
                        ])
                        if target_header:
                            target_header.suspend_security().write(vals_header)
                        else:
                            self.env['tw.sp.digital.target'].suspend_security().create(vals_header)
        else:
            nip = values[1]
            nama = values[2]
            job_title = values[3]
            jenis_sp = str(values[4]).lower()
            level_sp = str(int(values[5])) if values[5] else False
            keterangan = values[6] if len(values) > 6 else ''
            month = str(int(values[7])) if len(values) > 7 else str(date.today().month)
            year = str(int(values[8])) if len(values) > 8 else str(date.today().year)

            ## Cek Madatory and skip the loop if any##
            mandatory_fields = [
                'branch',
                'nip',
                'nama',
                'jenis_sp',
                'level_sp',
            ]
            fields = []
            for x in range(0, 5):
                if not values[x]:
                    fields.append(mandatory_fields[x])
            if len(fields) > 0:
                warning_note += f'Terdapat kolom kosong di baris {rx} -> {fields}!'

            if not warning_note:
                branch_obj = self.env['res.company'].suspend_security().search([
                    ('code','=',branch)
                ], limit=1)
                employee_obj = self.env['hr.employee'].suspend_security().search([
                    ('registry_number','=',nip),
                ], limit=1)
                if not employee_obj:
                    warning_note += f'Baris ke {rx} Karyawan [{nip}] {nama} tidak ditemukan di {branch_obj.name or branch}\n'
                elif not branch_obj:
                    branch_obj = employee_obj.company_id

                if branch_obj and employee_obj:
                    # Check is SP header already exist
                    sp_obj = self.env['tw.sp.digital'].search([
                        ('month','=',month),
                        ('year','=',year),
                        ('employee_id','=',employee_obj.id),
                    ], limit=1)
                    # create line only.. if header exist
                    if sp_obj:
                        vals_line_ids.append({
                            'sp_level': level_sp,
                            'type': jenis_sp,
                            'employee_id': employee_obj.id,
                            'sp_digital_id': sp_obj.id,
                            'keterangan': keterangan
                        })
                    else:
                        # Else create line and header
                        vals_header.append({
                            'company_id': branch_obj.id,
                            'employee_id': employee_obj.id,
                            'job_title': job_title.title() or employee_obj.job_id.name.title(),
                            'month': month,
                            'year': year,
                            'line_ids': [[0, 0, {
                                'sp_level': level_sp,
                                'type': jenis_sp,
                                'employee_id': employee_obj.id,
                                'keterangan': keterangan
                            }]]
                        })

        return warning_note, vals_header, vals_line_ids