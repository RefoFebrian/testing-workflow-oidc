# -*- coding: utf-8 -*-

from odoo import models, fields

class TwDgiInfoWizard(models.TransientModel):
    """
    Popup Wizard to display DGI information.
    """
    _name = 'tw.dgi.info.wizard'
    _description = 'DGI Information Wizard'

    dgi_get_date = fields.Datetime(string='DGI Get Date', readonly=True)
    dgi_get_uid = fields.Many2one('res.users', string='DGI Get By', readonly=True)

