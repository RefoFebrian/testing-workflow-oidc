# -*- coding: utf-8 -*-

from odoo import models, fields


class TwDgiInfoWizardInheritPS(models.TransientModel):
    """
    Extend DGI Info popup wizard untuk Part Sales module.
    Menambahkan field md_reference_ps agar popup menampilkan
    referensi DGI spesifik Part Sales.
    """
    _inherit = "tw.dgi.info.wizard"

    md_reference_ps = fields.Char(string="MD Reference PS", readonly=True)
