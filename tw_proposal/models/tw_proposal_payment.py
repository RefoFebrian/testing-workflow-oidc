# -*- coding: utf-8 -*-

# 1: imports of python lib
import difflib
import json
import os
import logging
import re

# 2: import of known third party lib
from datetime import date, timedelta, datetime

# 3:  imports of odoo
from odoo import models, fields, api, _, Command

# 4:  imports from odoo modules
from odoo.exceptions import UserError as Warning

# 5: local imports

# 6: Import of unknown third party lib


_logger = logging.getLogger(__name__)

class TwProposalPayment(models.Model):
    _name = "tw.proposal.payment"
    _description = "Proposal Online - List Pembayaran"
    _order = "id desc"

    
    name = fields.Char(string='Nomor Pembayaran')
    payment_model_id = fields.Integer(string='ID Model Pembayaran')
    payment_transaction_id = fields.Integer(string='ID Transaksi')
    payment_date = fields.Date(string='Tanggal Pembayaran')
    payment_amount = fields.Float(string='Total Pembayaran', digits='Product Price')
    
    proposal_id = fields.Many2one('tw.proposal', string='Nomor Proposal', ondelete='cascade')
    account_payment_ids = fields.Many2many('tw.account.payment', string='Account Payment', ondelete='cascade',compute='_compute_account_payment_ids')
    payment_name = fields.Char(
        compute='_compute_payment_name',
    )

    def _compute_payment_name(self):
        for record in self:
            names = record.account_payment_ids.mapped('name')
            record.payment_name = ', '.join(filter(None, names)) if names else False

    def _compute_account_payment_ids(self):
        for record in self:
            payment_lines = self.env['tw.account.payment.line'].search([
                ('move_line_id.move_name', '=', record.name),
                ('payment_id.state', '=', 'paid')
            ])
            record.account_payment_ids = payment_lines.mapped('payment_id')

    def action_open_payment_request(self):
        self.ensure_one()
        if self.name and 'AVP' in self.name:
            model_name = 'tw.advance.payment'
        elif self.name and 'NC' in self.name:
            model_name = 'tw.payment.request'
        
        record = self.env[model_name].search(
            [('name', '=', self.name)],
            limit=1
        )

        if not record:
            return

        return {
            'type': 'ir.actions.act_window',
            'name': 'Request Payment',
            'res_model': model_name,
            'view_mode': 'form',
            'res_id': record.id,
            'target': 'current',
        }
