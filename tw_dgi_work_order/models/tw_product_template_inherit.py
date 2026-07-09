# -*- coding: utf-8 -*-

from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    unit_type_code = fields.Char(string='Kode Tipe Unit', index=True)
