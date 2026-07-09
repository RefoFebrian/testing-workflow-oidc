# -*- coding: utf-8 -*-

from odoo import models, fields

class TwDgiInfoWizard(models.TransientModel):
    _inherit = 'tw.dgi.info.wizard'

    id_prospect = fields.Char(string='ID Prospect', readonly=True)
