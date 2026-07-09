# -*- coding: utf-8 -*-

from odoo import models, fields

class TWVehicleOwnershipHandoverLine(models.Model):
    _inherit = "tw.vehicle.ownership.handover.line" # Penyerahan BPKB Line
    
    # DGI Reference Field
    ref_doc_number = fields.Char(
        string="Reference Doc Number",
        help="Nomor Penyerahan BPKB dari DGI",
        copy=False
    )
