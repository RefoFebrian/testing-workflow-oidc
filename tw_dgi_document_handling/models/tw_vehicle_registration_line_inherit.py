# -*- coding: utf-8 -*-

from odoo import models, fields

class TWVehicleRegistrationLine(models.Model):
    _inherit = "tw.vehicle.registration.process.line"
    
    # DGI Reference Field
    ref_doc_number = fields.Char(
        string="Reference Doc Number",
        help="Nomor Faktur STNK dari DGI",
        copy=False
    )
