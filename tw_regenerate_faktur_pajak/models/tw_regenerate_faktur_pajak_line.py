# -*- coding: utf-8 -*-

# 1: imports of python lib
from datetime import datetime, timedelta

# 2: import of known third party lib

# 3:  imports of odoo
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

# 4:  imports from odoo modules

# 5: local imports

# 6: Import of unknown third party lib

class TwRegenerateFakturPajakGabunganLine(models.Model):
    _name = "tw.regenerate.faktur.pajak.gabungan.line"
    _description = "Regenerate Faktur Pajak Gabungan Line"

    # 7: defaults methods

    # 8: fields
    name = fields.Char(string="Transaction No")
    regenerate_id = fields.Many2one('tw.regenerate.faktur.pajak.gabungan')
    untaxed_amount = fields.Float('Untaxed Amount')
    tax_amount = fields.Float('Tax Amount')
    amount_total = fields.Float('Total Amount')
    date = fields.Date('Date')
    transaction_id = fields.Integer(string='Transaction ID')

    # 9: related fields
    partner_id = fields.Many2one('res.partner', string='Partner')
    model_id = fields.Many2one('ir.model', string='Form Name')
    faktur_pajak_out_id = fields.Many2one('tw.faktur.pajak.out', string='Faktur Pajak')