# -*- coding: utf-8 -*-

from odoo import models, fields


class TwDgiInfoWizardInheritWO(models.TransientModel):
    """
    Extend DGI Info popup wizard untuk Work Order module.
    Menambahkan field md_reference_pkb dan md_reference_sa
    agar popup menampilkan referensi DGI spesifik WO.
    """
    _inherit = "tw.dgi.info.wizard"

    md_reference_pkb = fields.Char(string="MD Reference PKB", readonly=True)
    md_reference_sa = fields.Char(string="MD Reference SA", readonly=True)
