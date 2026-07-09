# -*- coding: utf-8 -*-

from odoo import models, fields


class ResPartnerDGI(models.Model):
    """Inherit res.partner to add ID Reference MD for DGI integration"""
    _inherit = "res.partner"
    
    md_reference_id = fields.Char('ID Reference MD',index=True,help="ID Customer Main Dealer")