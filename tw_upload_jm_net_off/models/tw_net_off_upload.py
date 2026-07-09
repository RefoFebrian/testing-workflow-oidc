# -*- coding: utf-8 -*-

# 1: imports of python lib
import base64
import logging
from datetime import date

# 2: import of known third party lib
import xlrd

# 3: imports of odoo
import os
from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.tools import float_compare
from odoo.tools.misc import file_path as file_path_util

_logger = logging.getLogger(__name__)

# Column indices
_COL_BRANCH = 0
_COL_PARTNER = 1
_COL_DESCRIPTION = 2
_COL_ACCOUNT = 3
_COL_MOVE_LINE = 4
_COL_DEBIT = 5
_COL_CREDIT = 6
_MIN_COLS = 7


class TWNetOffUploadWizard(models.TransientModel):
    _name = "tw.net.off.upload.wizard"
    _description = "TW Net Off Upload Wizard"

    upload_file = fields.Binary(
        string='File Excel',
        help=(
            "Format Excel (baris pertama = header kolom, baris 2+ = data):\n"
            "Kolom 1: Branch Code\n"
            "Kolom 2: Partner Code\n"
            "Kolom 3: Description\n"
            "Kolom 4: Account Code\n"
            "Kolom 5: Account Move Line (nama journal item)\n"
            "Kolom 6: Debit\n"
            "Kolom 7: Credit\n\n"
            "Branch Code, Partner Code, dan Description hanya diisi pada baris pertama "
            "dari setiap grup Net Off. Baris berikutnya dalam grup yang sama biarkan kosong."
        )
    )
    filename = fields.Char(string='Nama File')

    # -------------------------------------------------------------------------
    # 13: action methods
    # -------------------------------------------------------------------------
    def action_download_format_file(self):
        """Download the Net Off upload template.
        Priority: tw.format.upload record → data/template_upload_net_off.xlsx
        """
        format_obj = self.env['tw.format.upload'].sudo().search([
            ('name', '=', 'net off'),
            ('active', '=', True),
        ], limit=1)

        if format_obj and format_obj.file_format_show and format_obj.filename_upload_format:
            return {
                'type': 'ir.actions.act_url',
                'name': 'net_off_template',
                'url': (
                    f'/web/content/tw.format.upload/{format_obj.id}'
                    f'/file_format_show/{format_obj.filename_upload_format}?download=true'
                ),
            }

        # Fallback: serve from module data/ folder
        filename = 'template_upload_net_off.xlsx'
        file_path = file_path_util(f'tw_upload_jm_net_off/data/{filename}')
        if not file_path or not os.path.exists(file_path):
            raise UserError(_("Format template belum tersedia. Silakan hubungi tim IT."))

        with open(file_path, 'rb') as f:
            file_content = base64.b64encode(f.read())

        attachment = self.env['ir.attachment'].sudo().create({
            'name': filename,
            'datas': file_content,
            'res_model': self._name,
            'res_id': self.id,
            'type': 'binary',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}/{filename}?download=true',
            'target': 'self',
        }

    def action_import(self):
        self.ensure_one()

        if not self.upload_file:
            raise UserError(_("Silakan unggah file Excel terlebih dahulu."))

        file_data = base64.b64decode(self.upload_file)
        try:
            book = xlrd.open_workbook(file_contents=file_data)
        except Exception:
            raise UserError(_("File tidak valid. Pastikan file berformat .xls atau .xlsx."))

        sheet = book.sheet_by_index(0)

        # Parse all data rows (skip row 0 = header labels)
        groups = self._parse_groups(sheet)

        if not groups:
            raise UserError(_("Tidak ada data yang ditemukan dalam file."))

        errors = []
        validated_groups = []

        for group_idx, group in enumerate(groups, start=1):
            group_errors, validated = self._validate_group(group_idx, group)
            errors.extend(group_errors)
            if not group_errors:
                validated_groups.append(validated)

        if errors:
            raise UserError(_("Ditemukan kesalahan:\n\n") + "\n".join(errors))

        # Create Net Off records
        created = self.env['tw.net.off']
        for validated in validated_groups:
            net_off = self._create_net_off(validated)
            created |= net_off

        return {
            'type': 'ir.actions.act_window',
            'name': _('Net Off'),
            'res_model': 'tw.net.off',
            'view_mode': 'list,form',
            'domain': [('id', 'in', created.ids)],
            'target': 'current',
        }

    # -------------------------------------------------------------------------
    # 14: private methods
    # -------------------------------------------------------------------------
    def _parse_groups(self, sheet):
        """
        Parse the sheet into groups. Each group is a dict with:
          - branch_code, partner_code, description (from the first row of the group)
          - lines: list of dicts with account_code, move_line_name, debit, credit, row_num
        A new group starts when branch_code is non-empty.
        Row 0 is the column header row — skip it.
        """
        groups = []
        current_group = None

        for row_idx in range(1, sheet.nrows):
            row = sheet.row_values(row_idx)

            # Stop at the first fully-empty row (end of data)
            if not any(str(v).strip() for v in row):
                break

            # Skip note/footer rows (first non-empty cell starts with '*')
            first_val = next((str(v).strip() for v in row if str(v).strip()), '')
            if first_val.startswith('*'):
                continue

            branch_code = self._cell_str(row, _COL_BRANCH)
            partner_code = self._cell_str(row, _COL_PARTNER)
            description = self._cell_str(row, _COL_DESCRIPTION)

            # A non-empty branch_code signals the start of a new group
            if branch_code:
                current_group = {
                    'branch_code': branch_code,
                    'partner_code': partner_code,
                    'description': description,
                    'lines': [],
                }
                groups.append(current_group)

            if current_group is None:
                # Lines before any header row — skip
                continue

            account_code = self._cell_str(row, _COL_ACCOUNT)
            move_line_name = self._cell_str(row, _COL_MOVE_LINE)
            debit = row[_COL_DEBIT] if len(row) > _COL_DEBIT else 0
            credit = row[_COL_CREDIT] if len(row) > _COL_CREDIT else 0

            current_group['lines'].append({
                'account_code': account_code,
                'move_line_name': move_line_name,
                'debit': debit,
                'credit': credit,
                'row_num': row_idx + 1,  # 1-based for user messages
            })

        return groups

    def _validate_group(self, group_idx, group):
        """
        Validate a single group. Returns (errors_list, validated_dict).
        validated_dict is None if there are errors.
        """
        errors = []
        prefix = _("Grup %(idx)s", idx=group_idx)

        # --- Validate branch ---
        company = self.env['res.company'].sudo().search(
            [('code', '=', group['branch_code'])], limit=1
        )
        if not company:
            errors.append(_(
                "%(prefix)s: Branch '%(code)s' tidak ditemukan.",
                prefix=prefix, code=group['branch_code'],
            ))
        elif company not in self.env.user.company_ids:
            errors.append(_(
                "%(prefix)s: Anda tidak memiliki akses ke branch '%(branch)s'. "
                "Hubungi administrator untuk mengaktifkan akses branch ini.",
                prefix=prefix, branch=company.name,
            ))

        # --- Validate partner (optional) ---
        partner = self.env['res.partner']
        if group['partner_code']:
            partner = self.env['res.partner'].sudo().search(
                [('code', '=', group['partner_code'])], limit=1
            )
            if not partner:
                errors.append(_(
                    "%(prefix)s: Partner '%(code)s' tidak ditemukan.",
                    prefix=prefix, code=group['partner_code'],
                ))

        # --- Validate description ---
        if not group['description']:
            errors.append(_("%(prefix)s: Description tidak boleh kosong.", prefix=prefix))

        # --- Validate lines ---
        if not group['lines']:
            errors.append(_("%(prefix)s: Tidak ada baris journal.", prefix=prefix))

        validated_lines = []
        for line in group['lines']:
            row_num = line['row_num']
            line_errors, validated_line = self._validate_line(row_num, line, company)
            errors.extend(line_errors)
            if not line_errors:
                validated_lines.append(validated_line)

        if errors:
            return errors, None

        # --- Validate balance ---
        total_debit = sum(l['debit'] for l in validated_lines)
        total_credit = sum(l['credit'] for l in validated_lines)
        precision = self.env['decimal.precision'].precision_get('Account')
        if float_compare(total_debit, total_credit, precision_digits=precision) != 0:
            errors.append(_(
                "%(prefix)s: Total Debit (%(d)s) tidak sama dengan Total Credit (%(c)s).",
                prefix=prefix, d=total_debit, c=total_credit,
            ))
            return errors, None

        # Use the first line's account as the header account_id
        header_account_id = validated_lines[0]['account_id']

        return [], {
            'company': company,
            'partner': partner,
            'description': group['description'],
            'header_account_id': header_account_id,
            'lines': validated_lines,
        }

    def _validate_line(self, row_num, line, company):
        """Validate a single line row. Returns (errors, validated_dict)."""
        errors = []
        validated = {}

        # --- Account Code ---
        account_code = line['account_code']
        if not account_code:
            errors.append(_("Baris %(row)s: Account Code tidak boleh kosong.", row=row_num))
        else:
            domain = [('code', '=', account_code)]
            if company:
                domain.append(('company_ids', 'in', [company.id]))
            account = self.env['account.account'].sudo().search(domain, limit=1)
            if not account:
                errors.append(_(
                    "Baris %(row)s: Akun '%(code)s' tidak ditemukan.",
                    row=row_num, code=account_code,
                ))
            else:
                validated['account_id'] = account.id

        # --- Move Line (account.move.line by name) ---
        move_line_name = line['move_line_name']
        if not move_line_name:
            errors.append(_("Baris %(row)s: Account Move Line tidak boleh kosong.", row=row_num))
        else:
            domain = [('name', '=', move_line_name), ('reconciled', '=', False)]
            if company:
                domain.append(('company_id', '=', company.id))
            move_line = self.env['account.move.line'].sudo().search(domain, limit=1)
            if not move_line:
                errors.append(_(
                    "Baris %(row)s: Journal Item '%(name)s' tidak ditemukan atau sudah direkonsiliasi.",
                    row=row_num, name=move_line_name,
                ))
            else:
                validated['move_line_id'] = move_line.id
                validated['name'] = move_line.name

        # --- Debit ---
        try:
            debit = float(line['debit'] or 0)
            if debit < 0:
                raise ValueError
            validated['debit'] = debit
        except (ValueError, TypeError):
            errors.append(_(
                "Baris %(row)s: Debit '%(val)s' tidak valid.",
                row=row_num, val=line['debit'],
            ))

        # --- Credit ---
        try:
            credit = float(line['credit'] or 0)
            if credit < 0:
                raise ValueError
            validated['credit'] = credit
        except (ValueError, TypeError):
            errors.append(_(
                "Baris %(row)s: Credit '%(val)s' tidak valid.",
                row=row_num, val=line['credit'],
            ))

        # At least one of debit/credit must be > 0
        if not errors and validated.get('debit', 0) == 0 and validated.get('credit', 0) == 0:
            errors.append(_(
                "Baris %(row)s: Debit dan Credit tidak boleh keduanya 0.",
                row=row_num,
            ))

        return errors, validated if not errors else None

    def _create_net_off(self, validated):
        """Create a single tw.net.off record from validated group data."""
        company = validated['company']
        partner = validated['partner']
        lines = validated['lines']

        net_off = self.env['tw.net.off'].sudo().create({
            'company_id': company.id,
            'partner_id': partner.id if partner else False,
            'description': validated['description'],
            'account_id': validated['header_account_id'],
            'date': date.today(),
            'line_ids': [
                (0, 0, {
                    'account_id': l['account_id'],
                    'move_line_id': l['move_line_id'],
                    'name': l['name'],
                    'debit': l['debit'],
                    'credit': l['credit'],
                })
                for l in lines
            ],
        })
        return net_off

    @staticmethod
    def _cell_str(row, col_idx):
        """Safely get a string value from a row, stripping float suffixes like '1234.0'."""
        if len(row) <= col_idx:
            return ''
        val = str(row[col_idx]).strip()
        if val.endswith('.0'):
            val = val[:-2]
        return val
