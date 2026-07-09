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


class InheritDealerSaleOrder(models.Model):
    _inherit = "tw.dealer.sale.order"

    hl_count = fields.Integer(string="HL Count", compute="_compute_hl_count")

    def _compute_hl_count(self):
        for order in self:
            order.hl_count = self.env['tw.account.payment'].search_count([('partner_id', '=', order.partner_id.id), ('type', '=', 'receive_payment'),('company_id', '=', order.company_id.id)])

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
                'default_type': 'receive_payment',
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
                'default_division': 'Unit',
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
            'domain': [('partner_id', '=', self.partner_id.id), ('type', '=', 'receive_payment'),('company_id', '=', self.company_id.id)],
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