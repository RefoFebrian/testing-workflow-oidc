# -*- coding: utf-8 -*-

from odoo import models, fields

class TWPartSalesLine(models.Model):
    _inherit = "tw.part.sales.line"
    
    # DGI Reference Field
    ref_doc_number = fields.Char(
        string="Reference Doc Number",
        help="Nomor Part Sales dari DGI",
        copy=False
    )
