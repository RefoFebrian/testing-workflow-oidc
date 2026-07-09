# -*- coding: utf-8 -*-

from odoo import models, fields

class TWVehicleRegistrationHandoverLine(models.Model):
    _inherit = "tw.vehicle.registration.handover.line" # Penyerahan STNK Line
    
    # DGI Reference Field
    ref_doc_number = fields.Char(
        string="Reference Doc Number",
        help="Nomor Penyerahan STNK dari DGI",
        copy=False
    )
