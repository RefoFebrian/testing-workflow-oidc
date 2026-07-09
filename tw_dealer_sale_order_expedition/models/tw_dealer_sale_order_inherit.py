# -*- coding: utf-8 -*-

# 1: imports of python lib
import itertools

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, Command, _

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning
from itertools import groupby

# 5: local imports

# 6: Import of unknown third party lib


class TwSaleOrderExpedition(models.Model):
    _inherit = "tw.dealer.sale.order"

    # 7: defaults methods

    # 8: fields
    amount_accrue_expedition = fields.Float(compute='_compute_amounts_expedition', string='Total Accrue Expedition', store=True, help="The total amount.")
    
    # 9: relation fields
    
    # 10: constraints & sql constraints
	
    # 11: compute/depends & on change methods
    @api.depends('order_line.city_id', 'order_line.district_id')
    def _compute_partner_stnk_location(self):
        for order in self:
            order.city_ids = order.order_line.mapped('city_id')
            order.district_ids = order.order_line.mapped('district_id')
    
    @api.depends('order_line', 'order_line.accrue_expedition')
    def _compute_amounts_expedition(self):
        for order in self:
            total_accrue_expedition = 0
            for line in order.order_line:
                total_accrue_expedition += line.accrue_expedition
            order.amount_accrue_expedition = total_accrue_expedition

    # 12: override base methods

    # 13: action methods
	
    # 14: private methods
    def _recompute_totals(self):
        super()._recompute_totals()
        self._set_expedition_amount()

    def _set_expedition_amount(self):
        for order in self:
            if order.state == 'draft':
                account_conf = self.company_id.branch_setting_id.account_setting_id
                if account_conf.is_accrue_expedition and account_conf.accrue_expedition:
                    for line in order.order_line:
                        line.accrue_expedition = account_conf.accrue_expedition
    
    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped, final, date)
        # Tambahkan ke moves
        moves += self._create_accrue_expedition_move()
        return moves

    def _create_accrue_expedition_move(self):
        move = self.env['account.move']
        invoice_vals = self._prepare_accrue_expedition_move()
        if invoice_vals:
            move = self._create_account_invoices(invoice_vals, final=True)
        return move

    def _get_additional_cancel_account_moves(self):
        try:
            moves = super()._get_additional_cancel_account_moves()
        except AttributeError:
            moves = self.env['account.move']

        self.ensure_one()
        account_conf = self.company_id.branch_setting_id.account_setting_id
        expedition_journal = account_conf.journal_dso_accrue_ekspedisi_id if account_conf else False
        if not expedition_journal:
            return moves

        expedition_moves = self.env['account.move'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('journal_id', '=', expedition_journal.id),
            ('move_type', '=', 'entry'),
            ('state', '=', 'posted'),
            ('reversed_entry_id', '=', False),
            ('ref', '=', self.name),
        ])
        return moves | expedition_moves

    def _prepare_accrue_expedition_move(self):
        account_conf = self.company_id.branch_setting_id.account_setting_id
        invoice_vals = {}
        expedition_lines = self.order_line.filtered(lambda l: l.accrue_expedition > 0)
        # Di teds 1.0, accrue expedisi hanya dibuat jika unit memiliki BBN
        bbn_lines = self.order_line.filtered(lambda l: getattr(l, 'is_bbn') == True)
        bbn_count = len(bbn_lines)
        if bbn_count > 0:
            if expedition_lines:
                # Check configuration
                journal_expedisi = account_conf.journal_dso_accrue_ekspedisi_id
                if not journal_expedisi:
                    raise Warning(_("Journal untuk 'Journal Accrue Dana Ongkos Angkut' belum dikonfigurasi.\nSilakan konfigurasikan di menu pengaturan akun."))
                debit_account_id = journal_expedisi.default_debit_account_id.id
                if not debit_account_id:
                    raise Warning(_("Account debit default untuk 'Journal Accrue Dana Ongkos Angkut' belum dikonfigurasi.\nSilakan konfigurasikan di menu pengaturan akun."))
                credit_account_id = journal_expedisi.default_credit_account_id.id
                if not credit_account_id:
                    raise Warning(_("Account kredit default untuk 'Journal Accrue Dana Ongkos Angkut' belum dikonfigurasi.\nSilakan konfigurasikan di menu pengaturan akun."))

                invoice_vals = self._prepare_invoice()
                code = journal_expedisi.code
                prefix = self.company_id.code
                invoice_vals.update({
                    'name': self.env['ir.sequence'].get_sequence_code(code, prefix),
                    'move_type': 'entry',
                    'journal_id': journal_expedisi.id,
                    'partner_id': self.company_id.partner_id.id,
                    'line_ids': [
                        Command.create({
                            'name': 'Accrue Dana Ongkos Angkut %s' % (self.name),
                            'credit': account_conf.accrue_expedition,
                            'debit': 0,
                            'product_id': False,
                            'discount': 0,
                            'quantity': bbn_count,
                            'account_id': journal_expedisi.default_credit_account_id.id,
                            'tax_ids': False
                        }),
                        Command.create({
                            'credit': 0,
                            'debit': account_conf.accrue_expedition,
                            'product_id': False,
                            'discount': 0,
                            'quantity': bbn_count,
                            'account_id': journal_expedisi.default_debit_account_id.id,
                            'tax_ids': False
                        }),
                    ],
                })
                
        return invoice_vals
    
    def _prepare_sumary_discount_data(self, product_id, lines):
        data = super()._prepare_sumary_discount_data(product_id, lines)
        data.update({
            'accrue_expedition': sum(line.accrue_expedition if line.biro_jasa_id else 0 for line in lines),
        })
        return data
    
