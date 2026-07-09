# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TWVehicleRegistrationReceipt(models.Model):
    _name = "tw.vehicle.registration.receipt"
    _inherit = ["tw.vehicle.registration.receipt", "tw.dgi.info.mixin"] # Penerimaan STNK
    
    # MD Reference
    md_reference_number = fields.Char(
        string='MD Reference Number',
        copy=False,
        readonly=True,
        index=True,
        help='Penerimaan STNK (noPST)',
    )
    
    def action_open_dgi_wizard(self):
        """Open DGI wizard dari list view"""
        return {
            'name': 'Get Data from DGI',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dgi.receipt.stnk.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_company_id': self.env.company.id,
            }
        }
