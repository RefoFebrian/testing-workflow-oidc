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

class TwProposalLine(models.Model):
    _name = "tw.proposal.line"
    _rec_name = "description"
    _description = "Proposal Online - Detail"

    # 8: fields
    description = fields.Char(string='Deskripsi')
    qty = fields.Float(string='Qty', digits='Product Unit of Measure', default=1)
    price_unit = fields.Float(string='Price/Qty', digits='Product Price')
    # price * qty
    amount_total = fields.Float(string='Total', digits='Product Price')
    pay_to = fields.Selection([
        ('pic', 'PIC'),
        ('vendor', 'Vendor')
    ], string='Bayar ke')
    
    # untuk jenis pembayaran Cash, wajib input keterangan
    cash_remark = fields.Char(string='Keterangan')
    
    # jumlah yang sudah dibayar
    amount_paid = fields.Float(string='Paid', digits='Product Price')

    # fund booked
    amount_reserved = fields.Float(string='Reserved', digits='Product Price')

    # 9: relation fields
    proposal_id = fields.Many2one('tw.proposal', string='Nomor Proposal', ondelete='cascade')
    # untuk jenis pembayaran Transfer, wajib input vendor
    supplier_id = fields.Many2one('res.partner', string='Supplier', ondelete='restrict')
    # Riwayat pencairan dana
    payment_ids = fields.One2many('tw.proposal.line.payment', 'proposal_line_id', string='Detail Pembayaran')

    @api.onchange("qty","price_unit")
    def _onchange_amount_total(self):
        self.amount_total = False
        if self.price_unit or self.qty:
            self.amount_total = self.qty * self.price_unit
    
    @api.onchange('pay_to')
    def _onchange_pay_to(self):
        if self.pay_to == 'pic':
            self.supplier_id = False
        elif self.pay_to == 'vendor':
            self.cash_remark = False

    # 10: Override Method
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('price_unit') <= 0 or vals.get('qty') <= 0:
                raise Warning('Perhatian! Price Unit atau Qty pada Detail harus lebih besar dari 0')
        return super().create(vals_list)

    def write(self, vals):
        for record in self:
            if 'price_unit' in vals or 'qty' in vals:
                new_price = vals.get('price_unit', record.price_unit)
                new_qty = vals.get('qty', record.qty)
                if new_price <= 0 or new_qty <= 0:
                    raise Warning('Perhatian! Price Unit dan atau Qty pada Detail harus lebih besar dari 0')
        return super().write(vals)