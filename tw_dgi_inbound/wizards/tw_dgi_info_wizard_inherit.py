# -*- coding: utf-8 -*-

from odoo import models, fields

class TwDgiInfoWizard(models.TransientModel):
    _inherit = 'tw.dgi.info.wizard'

    md_reference_po = fields.Char(string='MD Reference PO', readonly=True)
    md_reference_sl = fields.Char(string='MD Reference SL', readonly=True)
