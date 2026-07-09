# -*- coding: utf-8 -*-

from odoo import models, fields

class TWWorkOrderLine(models.Model):
    _inherit = "tw.work.order.line"
    
    # DGI Reference Field
    ref_doc_number = fields.Char(
        string="Reference Doc Number",
        help="Nomor Work Order dari DGI",
        copy=False
    )
