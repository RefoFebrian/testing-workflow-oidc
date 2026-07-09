# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import date, datetime

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _, Command


# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning, ValidationError

# 5: local imports

# 6: Import of unknown third party lib

class InheritAssetDisposal(models.Model):
    _inherit = "tw.asset.disposal"

    # 7: defaults methods
    
    # 8: fields
    hl_count = fields.Integer(string="HL Count", compute="_compute_hl_count")

    # 9: relation fields
    hl_ids = fields.One2many('tw.asset.disposal.hutang.lain', 'disposal_id', 'Hutang Lain')

    # 10: constraints & sql constraints

    # 11: compute/depends & on change methods
    @api.onchange('type')
    def onchange_type(self):
        self.disposal_line_sold_ids = False
        self.disposal_line_scrap_ids = False
        self.hl_ids = False

    def _compute_hl_count(self):
        for order in self:
            order.hl_count = self.env['tw.account.payment'].search_count([
                ('partner_id', '=', order.partner_id.id),
                ('type', '=', 'receive_payment'),
                ('company_id', '=', order.company_id.id)
            ])
    
    # 12: override methods

    # 13: action methods
    def action_request_approval(self):
        self.cek_hl()
        res = super(InheritAssetDisposal, self).action_request_approval()
        return res

    def action_create_hutang_lain(self):
        form_id = self.env.ref('tw_payment.tw_account_payment_receive_payment_form_view').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.account.payment',
            'name': 'Receive Payment',
            'views': [(form_id, 'form')],
            'view_mode': 'form',
            'view_id': False,
            'target': 'new',
            'context': {
                'default_company_id': self.company_id.id,
                'default_division': self.division,
                'default_amount': self.amount_total,
                'default_type': 'receive_payment',
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
                'default_move_journal_types': ('bank', 'cash'),
                'default_partner_id': self.partner_id.id,
                'action_id': self.env.ref('tw_payment.tw_account_payment_receive_payment_action'),
            }
        }
    
    def action_open_customer_hutang_lain(self):
        list_id = self.env.ref('tw_payment.tw_account_payment_receive_payment_list_view').id
        form_id = self.env.ref('tw_payment.tw_account_payment_receive_payment_form_view').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'tw.account.payment',
            'name': 'Receive Payment',
            'views': [(list_id, 'list'), (form_id, 'form')],
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('type', '=', 'receive_payment'),
                ('company_id', '=', self.company_id.id)
            ],
            'context': {
                'default_type': 'receive_payment',
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
                'default_division': 'Unit',
                'default_move_journal_types': ('bank', 'cash'),
                'default_partner_id': self.partner_id.id,
                'action_id': self.env.ref('tw_payment.tw_account_payment_receive_payment_action'),
            }
        }

    # 14: private methods
    def cek_hl(self):
        if self.type == 'sold':
            total_hl = 0
            if not self.hl_ids:
                raise Warning("Disposal Asset Type Sold harus mencantumkan Alokasi HL !")
            for hl in self.hl_ids:
                if hl.amount_hl_allocation > hl.amount_hl_balance:
                    raise Warning('Perhatian ! \n Nilai Allocation melebihi HL Balance !')
                if int(hl.amount_hl_allocation) <= 0:
                    raise Warning('Perhatian ! \n Nilai Allocation tidak boleh 0 !')
                total_hl += hl.amount_hl_allocation 

            if round(self.amount_total, 2) != round(total_hl, 2):
                raise Warning('Perhatian ! \n Nilai HL tidak sama dengan Amount Total ! \n Amount Total: %s \n Total HL: %s' % (self.amount_total, total_hl))

    def auto_journal_and_reconcile(self, aml_piutang_ids):
        """Create counter journal entries for HL (Hutang Lain) and reconcile with piutang."""
        obj_account_move = self.env['account.move']
        total_hl = 0
        if self.hl_ids:
            obj_branch_config = self.company_id.branch_setting_id.account_setting_id
            if not obj_branch_config.journal_disposal_asset_hl_id:
                raise Warning("Konfigurasi Journal Reconcile HL belum disetting!")

            # Create Journal AL untuk lawan HL
            move_line_vals = []

            for hl_line in self.hl_ids:
                total_hl += hl_line.amount_hl_allocation
                payment = hl_line.hl_id

                # Find the receivable/payable move line from the HL payment
                hl_aml = payment.move_id.line_ids.filtered(
                    lambda l: l.account_id.reconcile and l.credit > 0
                )
                if not hl_aml:
                    hl_aml = payment.move_id.line_ids.filtered(
                        lambda l: l.account_id.reconcile
                    )

                if hl_aml:
                    hl_aml = hl_aml[0]
                    move_line_vals.append(Command.create({
                        'account_id': hl_aml.account_id.id,
                        'partner_id': hl_aml.partner_id.id or self.partner_id.id,
                        'name': payment.name or self.name,
                        'debit': hl_line.amount_hl_allocation,
                        'credit': 0,
                        'company_id': self.company_id.id,
                        'division': self.division,
                    }))

            # Add counter piutang lines
            for aml_piutang in aml_piutang_ids:
                move_line_vals.append(Command.create({
                    'account_id': aml_piutang.account_id.id,
                    'partner_id': self.partner_id.id,
                    'name': self.name,
                    'debit': 0,
                    'credit': aml_piutang.debit,
                    'company_id': self.company_id.id,
                    'division': self.division,
                }))
            vals = {
                'journal_id': obj_branch_config.journal_disposal_asset_hl_id.id,
                'date': self._get_default_date(),
                'ref': self.name,
                'partner_id': self.partner_id.id,
                'name': self.env['ir.sequence'].get_sequence_code('AL', self.company_id.code),
                'company_id': self.company_id.id,
                'line_ids': move_line_vals,
            }
            create_acc_move = obj_account_move.create(vals)
            create_acc_move.action_post()

            # Reconcile HL lines
            for hl_line in self.hl_ids:
                payment = hl_line.hl_id
                hl_aml = payment.move_id.line_ids.filtered(
                    lambda l: l.account_id.reconcile and l.credit > 0
                )
                if not hl_aml:
                    hl_aml = payment.move_id.line_ids.filtered(
                        lambda l: l.account_id.reconcile
                    )
                if hl_aml:
                    counter_aml = create_acc_move.line_ids.filtered(
                        lambda l: l.account_id == hl_aml[0].account_id and l.debit > 0
                    )
                    if counter_aml:
                        (hl_aml[0] | counter_aml[0]).reconcile()

            # Reconcile piutang lines
            total_aml_piutang = 0
            for aml_piutang in aml_piutang_ids:
                total_aml_piutang += aml_piutang.debit
                counter_aml = create_acc_move.line_ids.filtered(
                    lambda l: l.account_id == aml_piutang.account_id and l.credit > 0
                )
                if counter_aml:
                    (aml_piutang | counter_aml[0]).reconcile()

            if total_aml_piutang > total_hl:
                raise Warning('Reconcile Amount Asset (%s) Melebihi Nilai Alokasi HL (%s) !' % (total_aml_piutang, total_hl))

    def _create_account_move(self):
        res = super(InheritAssetDisposal, self)._create_account_move()
        move_line = self.move_id.line_ids.filtered(lambda x: '-Other Receivable' in x.name)
        if move_line:
            self.auto_journal_and_reconcile(move_line)
        return res

