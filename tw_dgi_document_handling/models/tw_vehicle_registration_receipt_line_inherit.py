# -*- coding: utf-8 -*-

from odoo import models, fields

class TWVehicleRegistrationReceiptLine(models.Model):
    _inherit = "tw.vehicle.registration.receipt.line" # Penerimaan STNK Line
    
    # DGI Reference Field
    ref_doc_number = fields.Char(
        string="Reference Doc Number",
        help="Nomor Faktur Penerimaan STNK dari DGI",
        copy=False
    )
