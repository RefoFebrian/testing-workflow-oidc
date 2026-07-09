# -*- coding: utf-8 -*-

from odoo import models, fields

class TWVehicleOwnershipReceiptLine(models.Model):
    _inherit = "tw.vehicle.ownership.receipt.line" # Penerimaan BPKB Line
    
    # DGI Reference Field
    ref_doc_number = fields.Char(
        string="Reference Doc Number",
        help="Nomor Penerimaan BPKB dari DGI",
        copy=False
    )
