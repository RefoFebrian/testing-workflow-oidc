# -*- coding: utf-8 -*-

# 1: imports of python lib
import calendar
from datetime import datetime, date

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from odoo.fields import Command

# 5: local imports

# 6: Import of unknown third party lib

class TwCollectingVoucher(models.Model):
    """Model for managing Voucher collection entries.
    
    This model handles the creation and management of accounts receivable/payable
    collection entries with proper state management and workflow.
    """
    _name = "tw.collecting.voucher"
    _description = "Collecting Voucher"
    _inherit = ['tw.collecting']
    _check_company_auto = True
    _order = "id desc"

    # 7: defaults methods

    # 8: fields

    # 9: relation fields
    move_line_ids = fields.Many2many(
        'account.move.line',
        'tw_collecting_voucher_account_move_line_rel',
        'collecting_id',
        'move_line_id',
        string='Journal Items',
        copy=False
    )

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.depends('company_id')
    def _compute_name(self):
        for record in self:
            if record.id and not record.name and record.state:
                seq_name = self.env['ir.sequence'].with_company(record.company_id).get_sequence_code('CV', record.company_id.code)
                record.name = seq_name
    
    @api.depends('company_id')
    def _compute_available_account_ids(self):
        for record in self:
            record.available_account_ids = False
            if record.company_id:
                journal_obj = record.company_id.branch_setting_id.account_setting_id.journal_dso_voucher_id
                domain = [('id', '=', journal_obj.default_credit_account_id.id)]
                record.available_account_ids = self.env['account.account'].suspend_security().search(domain)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.account_id = False
        self._validate_check_journal()

    # 12: override methods

    # 13: action methods
    def action_get_detail(self):
        """Retrieve move lines based on current filters."""
        self.ensure_one()
        self._validate_check_journal()
        journal_id = self.company_id.branch_setting_id.account_setting_id.journal_dso_voucher_id.id
        # Build domain for move line search
        domain = [
            ('company_id', '=', self.company_id.id),
            ('division', '=', self.division),
            ('account_id', '=', self.account_id.id),
            ('move_id.journal_id', '=', journal_id),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
            ('reconciled', '=', False),
            ('full_reconcile_id', '=', False)
        ]
            
        # Search for move lines
        move_lines = self.env['account.move.line'].search(domain)
        if not move_lines:
            raise Warning('No matching journal items found for the given criteria.')
            
        # Calculate total amount
        total_amount = sum(abs(line.amount_residual) for line in move_lines)
        
        # Update record with found move lines and calculated amount
        self.write({
            'move_line_ids': [(6, 0, move_lines.ids)],
            'amount': total_amount,
            'date': self._get_default_date()
        })
        
    def action_confirm(self):
        self.ensure_one()
        self._validate_check_journal()
        move_id = self._create_account_move()

        self.write({
            'collected_move_id': move_id.id,
            'state': 'confirm',
            'confirm_date': datetime.now(),
            'confirm_uid': self._uid,
        })

    def action_view_journal_entry(self):
        """Open the journal entry related to this collecting."""
        self.ensure_one()
        if not self.collected_move_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entry',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.collected_move_id.id,
            'target': 'current',
        }
        
    # 14: private methods
    def _get_account_setting(self):
        self.ensure_one()
        config = self.company_id.branch_setting_id
        if not config:
            raise Warning(f"Tidak ditemukan konfigurasi branch setting untuk dealer {self.company_id.name}, silahkan konfigurasi terlebih dahulu.")
        account_setting = config.account_setting_id
        if not account_setting:
            raise Warning(f"Tidak ditemukan konfigurasi akun setting untuk cabang {self.company_id.name}, silahkan konfigurasi terlebih dahulu.")
        return account_setting
    
    def _validate_check_journal(self):
        self.ensure_one()
        account_setting = self._get_account_setting()
        if not account_setting.journal_collecting_voucher_id:
            raise Warning(f"Konfigurasi Journal Collecting Voucher di dealer {self.company_id.name} belum di setting, silahkan konfigurasi terlebih dahulu.")
        if not account_setting.journal_dso_voucher_id:
            raise Warning(f"Konfigurasi Journal DSO Voucher di dealer {self.company_id.name} belum di setting, silahkan konfigurasi terlebih dahulu.")

    def _create_account_move(self):
        """Create account move for collecting voucher entry."""
        self.ensure_one()
        self._validate_check_journal()
        today = self._get_default_date()
        period_id = self.env['tw.account.period']._get_current_periods(today).id
        journal_id = self.company_id.branch_setting_id.account_setting_id.journal_collecting_voucher_id.id

        move_ids = []
        move_line_vals = []
        total_amount = 0.0
        warning = ""
        for move_line in self.move_line_ids:
            if move_line.reconciled:
                warning += "- %s \r\n" % move_line.name
            
            residual = move_line.amount_residual
            total_amount += residual
            move_line_vals.append({
                'name': f'Collecting {move_line.name}',
                'ref': move_line.ref,
                'debit': abs(residual) if residual < 0 else 0,
                'credit': residual if residual > 0 else 0,
                'division': self.division,
                'date_maturity': today,
                'company_id': move_line.company_id.id,
                'account_id': move_line.account_id.id,
                'partner_id': move_line.partner_id.id,
            })

            if move_line.move_id.payment_state != 'paid':
                move_ids.append(move_line.move_id.id)
        
        if warning != "":
            raise Warning(f"Transaksi berikut sudah di reconcile (sebagian / penuh):\r\n {warning}")

        move_line_vals.append({
            'company_id': self.company_id.id,
            'debit': total_amount if total_amount > 0 else 0,
            'credit': abs(total_amount) if total_amount < 0 else 0,
            'name': self.description,
            'ref': self.name,
            'account_id': self.account_id.id,
            'partner_id': self.company_id.partner_id.id,
            'division': self.division,
            'date_maturity': self.date_maturity if self.date_maturity else today,
        })

        move_id = self.env['account.move'].sudo().create({
            'division': self.division,
            'company_id': self.company_id.id,
            'journal_id': journal_id,
            'period_id': period_id,
            'date': today,
            'name': self.name,
            'ref': self.name,
            'line_ids': [
                Command.create(line)
                for line in move_line_vals
            ],
        }) 
        move_id.sudo().action_post()

        to_reconcile_ids = move_id.line_ids.filtered(lambda x: x.name != x.move_id.name)
        to_reconcile_ids += self.move_line_ids
        to_reconcile_ids.sudo().reconcile()
        
        if move_ids:
            invoice_obj = self.env['account.move'].suspend_security().browse(move_ids)
            invoice_obj.write({'payment_state': 'paid'})

        return move_id
