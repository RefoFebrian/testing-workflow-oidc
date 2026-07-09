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

class TwProposalLinePayment(models.Model):
    _name = "tw.proposal.line.payment"
    _description = "Proposal Online - Detail - Riwayat Pembayaran"

    proposal_line_id = fields.Many2one('tw.proposal.line', string='Nomor Proposal', ondelete='cascade')
    name = fields.Char(string='Nomor Pembayaran')
    pay_to = fields.Selection([
        ('pic', 'PIC'),
        ('vendor', 'Vendor')
    ], string='Bayar ke')
    supplier_id = fields.Many2one('res.partner', string='Supplier', ondelete='restrict')
    amount_paid = fields.Float(string='Paid', digits='Product Price')