# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError as Warning
from odoo.fields import Command

class PurchaseOrderInherit(models.Model):
    _inherit = "purchase.order"

    def action_create_invoice(self):
        res = super().action_create_invoice()
        if self.division == 'Unit':
            self.action_invoice_bb_beli_create()
        return res

    def action_invoice_bb_beli_create(self):
        """Membuat Customer Invoice untuk Blind Bonus Beli."""
        self.ensure_one()
        
        if not self.company_id.branch_setting_id.purchase_blind_bonus_amount or self.company_id.branch_setting_id.purchase_blind_bonus_amount <= 0:
            raise Warning(_('Amount Blind Bonus Purchase di Branch Setting %s tidak boleh <= 0, silahkan konfigurasi ulang.'%(self.company_id.code)))
        
        invoice_vals = self._prepare_blind_bonus_invoice()
        
        invoice = self.env['account.move'].with_context(
            default_move_type='out_invoice'
        ).sudo().with_company(self.company_id.id).create(invoice_vals)

        invoice.sudo().sudo().action_post()
        return invoice

    def _get_additional_cancel_account_moves(self):
        moves = super()._get_additional_cancel_account_moves()
        self.ensure_one()

        blind_bonus_journal = self.company_id.branch_setting_id.account_setting_id.journal_purchase_blind_bonus_id
        if self.division != 'Unit' or not blind_bonus_journal:
            return moves

        blind_bonus_moves = self.env['account.move'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('journal_id', '=', blind_bonus_journal.id),
            ('move_type', '=', 'entry'),
            ('state', '=', 'posted'),
            ('reversed_entry_id', '=', False),
            '|',
            ('invoice_origin', '=', self.name),
            ('ref', '=', self.name),
        ])
        return moves | blind_bonus_moves
    
    def _prepare_blind_bonus_invoice(self):
        """Menyiapkan dictionary of values untuk membuat invoice blind bonus baru."""
        self.ensure_one()
        
        branch_setting = self.company_id.branch_setting_id
        if not branch_setting:
            raise Warning("Branch Setting belum diatur untuk cabang ini.")
            
        account_setting = branch_setting.account_setting_id
        if not account_setting:
            raise Warning("Account Setting belum diatur di dalam Branch Setting.")

        journal = account_setting.journal_purchase_blind_bonus_id
        account_cr = account_setting.account_purchase_blind_bonus_cr_id
        account_dr = account_setting.account_purchase_blind_bonus_dr_id
        account_perf_dr = account_setting.account_purchase_blind_bonus_performance_dr_id
        account_perf_cr = account_setting.account_purchase_blind_bonus_performance_cr_id
        
        if not all([journal, account_cr, account_dr, account_perf_dr, account_perf_cr]):
            raise Warning("Konfigurasi Journal atau Akun untuk Blind Bonus Beli belum lengkap di Account Setting. Harap periksa kembali.")
            
        total_qty = sum(line.product_uom_qty for line in self.order_line)
        line_ids = [
            Command.create({
                'name': _('Blind Bonus Beli Performance Dr'),
                'debit': branch_setting.purchase_performance_blind_bonus_amount * total_qty,
                'credit': 0,
                'product_id': False,
                'discount': 0,
                'account_id': account_perf_dr.id,
                'tax_ids': False
            }),
            
            Command.create({
                'name': _('Blind Bonus Beli Performance Cr'),
                'debit': 0,
                'credit': branch_setting.purchase_performance_blind_bonus_amount * total_qty,
                'product_id': False,
                'discount': 0,
                'account_id': account_perf_cr.id,
                'tax_ids': False
            }),

            Command.create({
                'name': _('Blind Bonus Beli'),
                'debit': 0,
                'credit': branch_setting.purchase_blind_bonus_amount * total_qty,
                'product_id': False,
                'discount': 0,
                'account_id': account_cr.id,
                'tax_ids': False
            }),

            Command.create({
                'name': _('Blind Bonus Beli'),
                'debit': branch_setting.purchase_blind_bonus_amount * total_qty,
                'credit': 0,
                'product_id': False,
                'discount': 0,
                'account_id': account_dr.id,
                'tax_ids': False
            })
        ]
        
        return {
            'move_type': 'entry',
            'invoice_origin': self.name,
            'ref': self.name,
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.context_today(self),
            'journal_id': journal.id,
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'division': self.division,
            'line_ids': line_ids,
        }
