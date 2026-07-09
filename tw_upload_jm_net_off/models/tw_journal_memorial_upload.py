# -*- coding: utf-8 -*-

# 1: imports of python lib
import base64
import logging
from datetime import date

# 2: import of known third party lib
import xlrd

# 3: imports of odoo
import base64
import os
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_round
from odoo.tools.misc import formatLang, file_path as file_path_util

_logger = logging.getLogger(__name__)

# Column indices — flat table, row 0 = column headers, row 1+ = data
_COL_BRANCH        = 0   # Header-level: Branch code (only on first row of group)
_COL_PERIODE       = 1   # Header-level: Period code
_COL_DESCRIPTION   = 2   # Header-level: Description
_COL_AUTO_REVERSE  = 3   # Header-level: Auto Reverse? (TRUE/FALSE)
_COL_DIVISION      = 4   # Header-level: Division
_COL_PARTNER       = 5   # Header-level: Partner Code (optional)
_COL_LINE_BRANCH   = 6   # Per-line: Branch code for the journal line
_COL_LINE_ACCOUNT  = 7   # Per-line: Account code
_COL_LINE_TYPE     = 8   # Per-line: Dr / Cr
_COL_LINE_AMOUNT   = 9   # Per-line: Amount
_COL_LINE_ASSET    = 11  # Per-line: Asset code (optional)
_COL_JOURNAL_ITEM  = 10  # Per-line: Existing account.move.line name to reconcile (optional)

_TYPE_MAP = {'dr': 'debit', 'cr': 'credit'}


class TWJournalMemorialUploadWizard(models.TransientModel):
    _name = "tw.journal.memorial.upload.wizard"
    _description = "TW Journal Memorial Upload Wizard"

    upload_file = fields.Binary(string='File Excel')
    filename = fields.Char(string='Nama File')
    is_auto_net_off = fields.Boolean(
        string='Auto Net Off',
        help=(
            "Jika diaktifkan, Journal Memorial akan dikonfirmasi otomatis "
            "dan Net Off akan dibuat dari baris journal baru + Journal Items "
            "yang direferensikan di kolom L."
        ),
    )

    # -------------------------------------------------------------------------
    # 13: action methods
    # -------------------------------------------------------------------------
    def action_download_format_file(self):
        """Download the JM upload template.
        Priority: tw.format.upload record → data/template_upload_journal_memorial.xlsx
        """
        format_obj = self.env['tw.format.upload'].sudo().search([
            ('name', 'ilike', 'journal memorial'),
            ('active', '=', True),
        ], limit=1)

        if format_obj and format_obj.file_format_show and format_obj.filename_upload_format:
            return {
                'type': 'ir.actions.act_url',
                'name': 'jm_template',
                'url': (
                    f'/web/content/tw.format.upload/{format_obj.id}'
                    f'/file_format_show/{format_obj.filename_upload_format}?download=true'
                ),
            }

        # Fallback: serve from module data/ folder
        filename = 'template_upload_journal_memorial.xlsx'
        file_path = file_path_util(f'tw_upload_jm_net_off/data/{filename}')
        if not file_path or not os.path.exists(file_path):
            raise UserError(_("Format template belum tersedia. Silakan hubungi tim IT."))

        with open(file_path, 'rb') as f:
            file_content = base64.b64encode(f.read())

        # Create attachment
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

        jm_ids = []
        net_off_count = 0
        for validated in validated_groups:
            jm, net_off = self._create_jm(validated)
            jm_ids.append(jm.id)
            if net_off:
                net_off_count += 1

        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Memorial'),
            'res_model': 'tw.journal.memorial',
            'view_mode': 'list,form',
            'domain': [('id', 'in', jm_ids)],
            'target': 'current',
        }

    # -------------------------------------------------------------------------
    # 14: private methods
    # -------------------------------------------------------------------------
    def _parse_groups(self, sheet):
        """
        Parse the flat table into groups.
        Row 0 is the column header row — skip it.
        A new group starts when col A (Branch) is non-empty.
        """
        groups = []
        current_group = None

        for row_idx in range(1, sheet.nrows):
            row = sheet.row_values(row_idx)

            if not any(str(v).strip() for v in row):
                break  # stop at the first fully-empty row (end of data)

            # Skip note/footer rows (first non-empty cell starts with '*')
            first_val = next((str(v).strip() for v in row if str(v).strip()), '')
            if first_val.startswith('*'):
                continue

            branch_code = self._cell_str(row, _COL_BRANCH)

            if branch_code:
                current_group = {
                    'branch_code':  branch_code,
                    'periode_code': self._cell_str(row, _COL_PERIODE),
                    'description':  self._cell_str(row, _COL_DESCRIPTION),
                    'auto_reverse': self._cell_str(row, _COL_AUTO_REVERSE).upper(),
                    'division':     self._cell_str(row, _COL_DIVISION),
                    'partner_code': self._cell_str(row, _COL_PARTNER),
                    'lines': [],
                }
                groups.append(current_group)

            if current_group is None:
                continue

            current_group['lines'].append({
                'row_num':           row_idx + 1,
                'line_branch':       self._cell_str(row, _COL_LINE_BRANCH),
                'account_code':      self._cell_str(row, _COL_LINE_ACCOUNT),
                'type_raw':          self._cell_str(row, _COL_LINE_TYPE),
                'amount_raw':        row[_COL_LINE_AMOUNT] if len(row) > _COL_LINE_AMOUNT else '',
                'asset_code':        self._cell_str(row, _COL_LINE_ASSET),
                'journal_item_name': self._cell_str(row, _COL_JOURNAL_ITEM),
            })

        return groups

    def _validate_group(self, group_idx, group):
        """Validate a single JM group. Returns (errors_list, validated_dict)."""
        errors = []
        prefix = _("Grup %(idx)s", idx=group_idx)

        # --- Branch ---
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

        # --- Period ---
        period = self.env['tw.account.period']
        if not group['periode_code']:
            errors.append(_("%(prefix)s: Periode tidak boleh kosong.", prefix=prefix))
        else:
            domain = [('code', '=', group['periode_code'])]
            if company:
                domain.append(('company_id', 'parent_of', company.id))
            period = self.env['tw.account.period'].sudo().search(domain, limit=1)
            if not period:
                errors.append(_(
                    "%(prefix)s: Periode '%(code)s' tidak ditemukan di branch %(branch)s.",
                    prefix=prefix, code=group['periode_code'], branch=group['branch_code'],
                ))

        # --- Description ---
        if not group['description']:
            errors.append(_("%(prefix)s: Description tidak boleh kosong.", prefix=prefix))

        # --- Division ---
        if not group['division']:
            errors.append(_("%(prefix)s: Division tidak boleh kosong.", prefix=prefix))

        # --- Auto Reverse ---
        auto_reverse_raw = group['auto_reverse']
        if auto_reverse_raw not in ('TRUE', 'FALSE', ''):
            errors.append(_(
                "%(prefix)s: Auto Reverse '%(val)s' tidak valid. Gunakan TRUE atau FALSE.",
                prefix=prefix, val=auto_reverse_raw,
            ))
        is_auto_reverse = auto_reverse_raw == 'TRUE'

        # --- Partner (optional) ---
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

        # --- Lines ---
        if not group['lines']:
            errors.append(_("%(prefix)s: Tidak ada baris journal.", prefix=prefix))

        validated_lines = []
        has_journal_item_refs = False

        # Check raw data first — col K filled regardless of is_auto_net_off
        if any(line.get('journal_item_name') for line in group['lines']):
            has_journal_item_refs = True

        for line in group['lines']:
            line_errors, validated_line = self._validate_line(line, company)
            errors.extend(line_errors)
            if not line_errors:
                validated_lines.append(validated_line)

        # --- Warning: col K filled but is_auto_net_off not checked ---
        if has_journal_item_refs and not self.is_auto_net_off:
            errors.append(_(
                "%(prefix)s: Kolom 'Journal Item' diisi tetapi 'Auto Net Off' belum diaktifkan. "
                "Aktifkan 'Auto Net Off' pada wizard untuk membuat Net Off secara otomatis.",
                prefix=prefix,
            ))

        if errors:
            return errors, None

        # --- Balance check ---
        total_debit  = float_round(sum(l['amount'] for l in validated_lines if l['type'] == 'debit'), precision_digits=2)
        total_credit = float_round(sum(l['amount'] for l in validated_lines if l['type'] == 'credit'), precision_digits=2)
        precision = 2
        if float_compare(total_debit, total_credit, precision_digits=precision) != 0:
            errors.append(_(
                "%(prefix)s: Total Debit (%(d)s) tidak sama dengan Total Credit (%(c)s).",
                prefix=prefix, d=total_debit, c=total_credit,
            ))
            return errors, None

        # --- Journal from branch setting ---
        journal = self._get_journal(company)
        if not journal:
            errors.append(_(
                "%(prefix)s: Journal Memorial belum dikonfigurasi untuk branch %(branch)s.",
                prefix=prefix, branch=company.name if company else group['branch_code'],
            ))
            return errors, None

        return [], {
            'company':            company,
            'period':             period,
            'description':        group['description'],
            'division':           group['division'],
            'is_auto_reverse':    is_auto_reverse,
            'has_journal_items':  has_journal_item_refs,
            'partner':            partner,
            'journal':            journal,
            'lines':              validated_lines,
        }

    def _validate_line(self, line, company):
        """Validate a single line row. Returns (errors, validated_dict)."""
        errors = []
        validated = {}
        row_num = line['row_num']

        # --- Line Branch (col G) ---
        line_branch_code = line['line_branch']
        line_company = company
        if line_branch_code:
            lc = self.env['res.company'].sudo().search(
                [('code', '=', line_branch_code)], limit=1
            )
            if not lc:
                errors.append(_(
                    "Baris %(row)s: Branch baris '%(code)s' tidak ditemukan.",
                    row=row_num, code=line_branch_code,
                ))
            else:
                line_company = lc
        validated['company_id'] = line_company.id if line_company else False

        # --- Account Code (col H) ---
        account_code = line['account_code']
        if not account_code:
            errors.append(_("Baris %(row)s: Account Code tidak boleh kosong.", row=row_num))
        else:
            domain = [('code', '=', account_code)]
            if line_company:
                domain.append(('company_ids', 'parent_of', [line_company.id]))
            account = self.env['account.account'].sudo().search(domain, limit=1)
            if not account:
                errors.append(_(
                    "Baris %(row)s: Akun '%(code)s' tidak ditemukan.",
                    row=row_num, code=account_code,
                ))
            else:
                validated['account_id'] = account.id

        # --- Type (col I): Dr / Cr ---
        type_raw = line['type_raw'].lower()
        mapped_type = _TYPE_MAP.get(type_raw)
        if not mapped_type:
            errors.append(_(
                "Baris %(row)s: Tipe '%(val)s' tidak valid. Gunakan 'Dr' atau 'Cr'.",
                row=row_num, val=line['type_raw'],
            ))
        else:
            validated['type'] = mapped_type

        # --- Amount (col J) ---
        try:
            amount = float(line['amount_raw'] or 0)
            if amount <= 0:
                raise ValueError
            validated['amount'] = float_round(amount, precision_digits=2)
        except (ValueError, TypeError):
            errors.append(_(
                "Baris %(row)s: Amount '%(val)s' tidak valid. Harus berupa angka positif.",
                row=row_num, val=line['amount_raw'],
            ))

        # --- Journal Item Name (col K, optional) ---
        journal_item_name = line['journal_item_name']
        validated['journal_item_ids'] = []
        if journal_item_name and self.is_auto_net_off:
            # If uploaded line is Cr → look for existing item with debit > 0 (and vice versa)
            type_raw = line['type_raw'].lower()
            if type_raw == 'cr':
                side_domain = [('debit', '>', 0)]
            else:
                side_domain = [('credit', '>', 0)]

            move_lines = self.env['account.move.line'].sudo().search([
                ('move_id.state', '=', 'posted'),
                ('reconciled', '=', False),
                *side_domain,
                '|', ('name', '=', journal_item_name),
                     ('ref', '=', journal_item_name),
            ])
            if not move_lines:
                errors.append(_(
                    "Baris %(row)s: Journal Item '%(name)s' tidak ditemukan, "
                    "belum diposting, atau sudah direkonsiliasi.",
                    row=row_num, name=journal_item_name,
                ))
            else:
                validated['journal_item_ids'] = move_lines.ids

        # --- Asset Code (col L, optional) ---
        asset_code = line['asset_code']
        if asset_code and asset_code.lower() not in ('false', 'none', '-'):
            domain = [('name', '=', asset_code), ('state', '!=', 'close')]
            if line_company:
                domain.append(('company_id', '=', line_company.id))
            asset = self.env['account.asset.asset'].sudo().search(domain, limit=1)
            if not asset:
                errors.append(_(
                    "Baris %(row)s: Asset '%(code)s' tidak ditemukan atau sudah ditutup.",
                    row=row_num, code=asset_code,
                ))
            else:
                validated['asset_id'] = asset.id
        else:
            validated['asset_id'] = False

        # Label: account code + type
        validated['name'] = (
            f"{account_code} - {line['type_raw']}" if account_code else line['type_raw']
        )

        return errors, validated

    def _get_journal(self, company):
        if not company:
            return self.env['account.journal']
        branch_setting = self.env['tw.branch.setting'].sudo().get_branch_setting(company)
        if not branch_setting or not branch_setting.account_setting_id:
            return self.env['account.journal']
        return branch_setting.account_setting_id.journal_memorial_journal_id

    def _create_jm(self, validated):
        """
        Create a tw.journal.memorial record.
        If is_auto_net_off=True and there are journal item refs:
          - Auto-confirm the JM (posts account.move)
          - Create tw.net.off combining new JM move lines + existing referenced move lines
        Returns (jm, net_off_or_None).
        """
        company = validated['company']
        period  = validated['period']
        journal = validated['journal']
        partner = validated['partner']

        jm = self.env['tw.journal.memorial'].sudo().create({
            'company_id':        company.id,
            'period_id':         period.id,
            'current_period_id': period.id,
            'journal_id':        journal.id,
            'date':              date.today(),
            'description':       validated['description'],
            'division':          validated['division'],
            'is_auto_reverse':   validated['is_auto_reverse'],
            'line_ids': [
                (0, 0, {
                    'type':       l['type'],
                    'account_id': l['account_id'],
                    'partner_id': partner.id if partner else False,
                    'name':       l['name'],
                    'amount':     l['amount'],
                    'asset_id':   l.get('asset_id', False),
                    'company_id': l['company_id'],
                })
                for l in validated['lines']
            ],
        })

        # Always auto-confirm — posts the account.move immediately

        net_off = None
        if self.is_auto_net_off and validated['has_journal_items']:
            jm.action_confirm()
            net_off = self._create_net_off_from_jm(jm, partner, validated['lines'])

        return jm, net_off

    def _create_net_off_from_jm(self, jm, partner, validated_lines):
        """
        JM is already confirmed at this point.
        1. Collect new unreconciled move lines from jm.move_id.
        2. Collect existing move lines referenced in col K.
        3. Create tw.net.off in draft with all those lines.
        """
        new_move_lines = jm.move_id.line_ids.filtered(lambda l: not l.reconciled)
        if not new_move_lines:
            _logger.warning(
                "JM %s confirmed but no unreconciled move lines — Net Off skipped.", jm.name
            )
            return None

        # Collect existing move lines from col K references (multiple per line)
        existing_move_line_ids = [
            mid
            for l in validated_lines
            for mid in l.get('journal_item_ids', [])
        ]
        existing_move_lines = self.env['account.move.line'].sudo().browse(existing_move_line_ids)

        all_move_lines = new_move_lines | existing_move_lines

        # Use the first line's account as the Net Off header account
        header_account = all_move_lines[0].account_id

        net_off_line_vals = []
        for ml in all_move_lines:
            net_off_line_vals.append((0, 0, {
                'move_line_id': ml.id,
                'account_id':   ml.account_id.id,
                'partner_id':   ml.partner_id.id if ml.partner_id else False,
                'name':         ml.name or jm.description,
                'debit':        ml.debit,
                'credit':       ml.credit,
            }))

        net_off = self.env['tw.net.off'].sudo().create({
            'company_id':  jm.company_id.id,
            'partner_id':  partner.id if partner else False,
            'account_id':  header_account.id,
            'description': jm.description,
            'date':        date.today(),
            'line_ids':    net_off_line_vals,
        })
        return net_off

    @staticmethod
    def _cell_str(row, col_idx):
        """Safely get a stripped string from a row. Strips float suffix '1234.0'."""
        if len(row) <= col_idx:
            return ''
        val = str(row[col_idx]).strip()
        if val.endswith('.0'):
            val = val[:-2]
        return val
