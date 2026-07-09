# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class TwFakturPajakOutInherit(models.Model):
    """
    Inherit tw.faktur.pajak.out untuk menambahkan field signature_id.
    Field ini digunakan untuk menentukan siapa yang menandatangani Faktur Pajak.
    """
    _inherit = "tw.faktur.pajak.out"
    
    signature_id = fields.Many2one(
        'tw.signature', 
        string='Signature By',
        help="Nama pihak yang menandatangani faktur pajak."
    )
