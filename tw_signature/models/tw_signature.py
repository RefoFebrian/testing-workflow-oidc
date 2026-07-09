# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class TwSignature(models.Model):
    """
    Master data untuk Signature pada report dan dokumen.
    
    Field:
        name: Nama pihak yang menandatangani dokumen.
    """
    _name = "tw.signature"
    _description = "Signature"
    _order = "name asc"
    
    name = fields.Char(string="Name", required=True)
    
    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Signature name must be unique!')
    ]
