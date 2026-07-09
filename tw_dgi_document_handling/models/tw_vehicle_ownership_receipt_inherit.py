# -*- coding: utf-8 -*-

from odoo import models, fields, api

class TWVehicleOwnershipReceipt(models.Model):
    _name = "tw.vehicle.ownership.receipt"
    _inherit = ["tw.vehicle.ownership.receipt", "tw.dgi.info.mixin"] # Penerimaan BPKB
    
    # MD Reference
    md_reference_number = fields.Char(
        string='MD Reference Number',
        copy=False,
        readonly=True,
        index=True,
        help='Penerimaan BPKB (noPSB)',
    )
    
    def action_open_dgi_wizard(self):
        """Open DGI wizard dari list view"""
        return {
            'name': 'Get Data from DGI',
            'type': 'ir.actions.act_window',
            'res_model': 'tw.dgi.receipt.bpkb.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_company_id': self.env.company.id,
            }
        }
